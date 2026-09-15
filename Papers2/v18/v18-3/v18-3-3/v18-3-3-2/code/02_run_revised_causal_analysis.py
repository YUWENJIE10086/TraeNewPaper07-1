# -*- coding: utf-8 -*-
"""修订版实证：处理无关结果评分 + 诚实因果森林 + 多重识别诊断。"""
from pathlib import Path
import json, warnings
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from econml.dml import CausalForestDML
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
BASE=Path(__file__).resolve().parents[1]; D=BASE/"data"; D.mkdir(exist_ok=True)
SEED=42; rng=np.random.default_rng(SEED)
OUTCOME=[("price_index",1),("gross_margin",1),("inventory_ratio",-1),("sell_rate",1),("salable_days",-1),("soc_inv",-1)]
PRE=["util","fill","full_surf","ord_success","price_index","gross_margin","unitval","inventory_ratio","channel_coverage","demand_gap","amt_per_cust","new_cust","S_clean"]

def robust_scale(s, positive=True):
    s=pd.to_numeric(s,errors="coerce"); lo,hi=s.quantile([.02,.98]); z=s.clip(lo,hi)
    z=(z-lo)/(hi-lo) if hi>lo else pd.Series(.5,index=s.index)
    return z if positive else 1-z

def build_clean_score(p):
    z=pd.DataFrame(index=p.index)
    for c,direction in OUTCOME: z[c]=robust_scale(p[c],direction>0)
    z=z.apply(lambda s:s.fillna(s.groupby(p["ym"]).transform("median")).fillna(s.median()))
    x=np.maximum(z.to_numpy(float),1e-8); prob=x/x.sum(axis=0)
    entropy=-(prob*np.log(prob)).sum(axis=0)/np.log(len(x)); we=(1-entropy); we/=we.sum()
    sd=x.std(axis=0); corr=np.nan_to_num(np.corrcoef(x,rowvar=False)); wc=sd*(1-np.abs(corr)).sum(axis=1); wc/=wc.sum()
    w=(we+wc)/2; w/=w.sum()
    return x@w*100,pd.DataFrame({"feature":z.columns,"direction":[x[1] for x in OUTCOME],"entropy":we,"critic":wc,"weight":w})

def smd(a,b):
    den=np.sqrt((np.nanvar(a,ddof=1)+np.nanvar(b,ddof=1))/2)
    return float((np.nanmean(a)-np.nanmean(b))/den) if den>0 else 0.0

def twfe(df,outcome,treat="T"):
    fit=smf.ols(f"{outcome} ~ {treat} + C(code) + C(ym)",data=df).fit(cov_type="cluster",cov_kwds={"groups":df["code"]})
    return {"coef":float(fit.params[treat]),"se":float(fit.bse[treat]),"p":float(fit.pvalues[treat]),"ci":[float(fit.conf_int().loc[treat,0]),float(fit.conf_int().loc[treat,1])]}

def two_way_residual(values,code,ym,iterations=12):
    z=pd.Series(np.asarray(values,float)).copy(); code=pd.Series(np.asarray(code)); ym=pd.Series(np.asarray(ym))
    for _ in range(iterations):
        z=z-z.groupby(code).transform("mean"); z=z-z.groupby(ym).transform("mean")
    return z.to_numpy()

def main():
    p=pd.read_csv(D/"raw_panel.csv",encoding="utf-8-sig").sort_values(["code","ym"]).reset_index(drop=True)
    p["S_clean"],weights=build_clean_score(p)
    p["S_clean_lag2"]=p.groupby("code")["S_clean"].shift(2)
    p["S_clean_next"]=p.groupby("code")["S_clean"].shift(-1)
    p["Y_clean"]=p["S_clean_next"]-p["S_clean"]
    prev_fill=p.groupby("code")["fill"].shift(1); q35=p.groupby("ym")["fill"].transform(lambda x:x.quantile(.35))
    p["T"]=((p.fill<=q35)&((prev_fill-p.fill)>2)).astype(int)
    for c in PRE: p[c+"_pre"]=p.groupby("code")[c].shift(1)
    dum=pd.concat([pd.get_dummies(p.cat,prefix="cat",dtype=int),pd.get_dummies(p.price_band_cat,prefix="band",dtype=int)],axis=1); p=pd.concat([p,dum],axis=1)
    cats=[f"cat_{x}" for x in ["一类烟","二类烟","三类烟","四类烟","五类烟"]]; bands=[f"band_{x}" for x in ["低档","中低档","中档","中高档","高档"]]
    for c in cats+bands:
        if c not in p:p[c]=0
    covs=[c+"_pre" for c in PRE]+cats+bands
    d=p.dropna(subset=["Y_clean","S_clean_next"]).copy()
    for c in covs:d[c]=d[c].fillna(d[c].median())
    lo,hi=d.Y_clean.quantile([.01,.99]); d=d[d.Y_clean.between(lo,hi)].copy().reset_index(drop=True)
    X=d[covs].to_numpy(float); Y=d.Y_clean.to_numpy(float); T=d["T"].to_numpy(int); groups=d.code.to_numpy()
    my=RandomForestRegressor(n_estimators=300,min_samples_leaf=15,max_features=.8,n_jobs=-1,random_state=SEED)
    mt=RandomForestClassifier(n_estimators=300,min_samples_leaf=15,max_features=.8,n_jobs=-1,random_state=SEED,class_weight="balanced")
    cf=CausalForestDML(model_y=my,model_t=mt,discrete_treatment=True,cv=GroupKFold(5),n_estimators=600,min_samples_leaf=20,max_samples=.45,honest=True,inference=True,subforest_size=4,n_jobs=-1,random_state=SEED)
    cf.fit(Y,T,X=X,groups=groups); tau=np.asarray(cf.effect(X)).ravel(); cil,ciu=cf.effect_interval(X)
    d["CATE"]=tau; d["CATE_lo"]=np.asarray(cil).ravel(); d["CATE_hi"]=np.asarray(ciu).ravel()
    ql,qh=np.quantile(tau,[1/3,2/3]); d["sensitivity"]=pd.cut(tau,[-np.inf,ql,qh,np.inf],labels=["低敏感","中敏感","高敏感"]).astype(str)
    ate=float(cf.ate(X)); al,au=[float(np.asarray(v).ravel()[0]) for v in cf.ate_interval(X)]
    imp=pd.DataFrame({"feature":covs,"importance":np.asarray(cf.feature_importances_).ravel()}).sort_values("importance",ascending=False)

    # 倾向得分、重叠与1:1无放回匹配
    xs=StandardScaler().fit_transform(X); ps=LogisticRegression(max_iter=3000,class_weight="balanced",random_state=SEED).fit(xs,T).predict_proba(xs)[:,1]; d["ps"]=ps
    ti=list(np.flatnonzero(T==1)); ci=list(np.flatnonzero(T==0)); unused=set(ci); pairs=[]
    for a in sorted(ti,key=lambda i:ps[i]):
        b=min(unused,key=lambda j:abs(ps[j]-ps[a])); unused.remove(b); pairs.append((a,b))
    smds=[]
    for c in covs:smds.append({"feature":c,"before":smd(d.loc[T==1,c],d.loc[T==0,c]),"after":smd(d.iloc[[a for a,b in pairs]][c],d.iloc[[b for a,b in pairs]][c])})
    mt_y=np.array([Y[a] for a,b in pairs]); mc_y=np.array([Y[b] for a,b in pairs]); matched=float(np.mean(mt_y-mc_y))
    rt=max(float(np.mean(mt_y>0)),1e-6); rc=max(float(np.mean(mc_y>0)),1e-6); rr=rt/rc
    rr_e=rr if rr>=1 else 1/rr; evalue=float(rr_e+np.sqrt(rr_e*(rr_e-1)))
    overlap={"treated_p01":float(np.quantile(ps[T==1],.01)),"treated_p99":float(np.quantile(ps[T==1],.99)),"control_p01":float(np.quantile(ps[T==0],.01)),"control_p99":float(np.quantile(ps[T==0],.99)),"outside_005_095":float(np.mean((ps<.05)|(ps>.95))),"ess":float((ps.sum()**2)/(np.square(ps).sum()))}

    # 双向固定效应、负对照结局和置换安慰剂
    fe=twfe(d,"Y_clean")
    # 负对照结局：处理发生前一期相对前两期的状态变化，理论上不可能由当期处理造成。
    d["Y_negative"]=d["S_clean_pre"]-d["S_clean_lag2"]
    neg=twfe(d.dropna(subset=["Y_negative"]),"Y_negative")
    placebo=[]; yr=two_way_residual(d.Y_clean,d.code,d.ym)
    for _ in range(100):
        tp=d.groupby("ym")["T"].transform(lambda x:rng.permutation(x.to_numpy()))
        trr=two_way_residual(tp,d.code,d.ym); placebo.append(float(np.dot(trr,yr)/np.dot(trr,trr)))

    # 处理阈值敏感性：统一用双向固定效应比较方向
    sens=[]
    defs=[("主定义：月内P35且下降>2",q35,2),("月内P30且下降>2",p.groupby("ym")["fill"].transform(lambda x:x.quantile(.30)),2),("月内P40且下降>3",p.groupby("ym")["fill"].transform(lambda x:x.quantile(.40)),3)]
    key=set(zip(d.code.astype(str),d.ym.astype(str)))
    for name,q,drop in defs:
        tmp=p.copy(); tmp["Ts"]=((tmp.fill<=q)&((prev_fill-tmp.fill)>drop)).astype(int); tmp=tmp[["code","ym","Ts"]].merge(d[["code","ym","Y_clean"]],on=["code","ym"])
        r=twfe(tmp,"Y_clean","Ts"); sens.append({"definition":name,"treated":int(tmp.Ts.sum()),**r})

    tr=d[d["T"]==1].copy(); cut=tr.CATE.quantile(2/3); high=tr[tr.CATE>=cut]; other=tr[tr.CATE<cut]
    back={"high_n":len(high),"other_n":len(other),"high_mean":float(high.Y_clean.mean()),"other_mean":float(other.Y_clean.mean()),"high_improve":float((high.Y_clean>0).mean()),"other_improve":float((other.Y_clean>0).mean()),"baseline_smd":smd(high.S_clean_pre,other.S_clean_pre),"baseline_p":float(ttest_ind(high.S_clean_pre,other.S_clean_pre,equal_var=False).pvalue)}
    metrics={"n":len(d),"products":int(d.code.nunique()),"treated":int(T.sum()),"covariates":len(covs),"outcome_indicators":[x[0] for x in OUTCOME],"excluded_from_outcome":["fill","demand_gap","put","util"],"ate":ate,"ate_ci":[al,au],"cate_sd":float(tau.std()),"q_low":float(ql),"q_high":float(qh),"twfe":fe,"negative_control":neg,"placebo":{"reps":100,"mean":float(np.mean(placebo)),"ci":[float(np.quantile(placebo,.025)),float(np.quantile(placebo,.975))],"p_empirical":float(np.mean(np.abs(placebo)>=abs(fe['coef'])))},"psm":{"pairs":len(pairs),"effect":matched,"treated_improve":rt,"control_improve":rc,"risk_ratio":rr,"e_value":evalue,"mean_abs_smd_before":float(np.mean(np.abs([x['before'] for x in smds]))),"mean_abs_smd_after":float(np.mean(np.abs([x['after'] for x in smds])))},"overlap":overlap,"threshold_sensitivity":sens,"backtest":back}
    d.to_csv(D/"analysis_panel.csv",index=False,encoding="utf-8-sig"); weights.to_csv(D/"clean_outcome_weights.csv",index=False,encoding="utf-8-sig"); imp.to_csv(D/"feature_importance.csv",index=False,encoding="utf-8-sig"); pd.DataFrame(smds).to_csv(D/"psm_balance.csv",index=False,encoding="utf-8-sig"); pd.DataFrame({"placebo_effect":placebo}).to_csv(D/"placebo_effects.csv",index=False,encoding="utf-8-sig")
    with open(D/"metrics.json","w",encoding="utf-8") as f:json.dump(metrics,f,ensure_ascii=False,indent=2)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
