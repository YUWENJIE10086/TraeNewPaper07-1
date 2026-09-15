# -*- coding: utf-8 -*-
"""以分组交叉拟合和诚实因果森林估计品规层面的异质性处理效应。"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from econml.dml import CausalForestDML

OUT = Path(__file__).resolve().parents[1] / "data"
SEED = 42
STATE = [("util",1),("fill",1),("full_surf",1),("price_index",1),("gross_margin",1),
         ("unitval",1),("inventory_ratio",-1),("channel_coverage",1)]
BASE_COVS = ["util","fill","full_surf","ord_success","price_index","gross_margin","unitval",
             "inventory_ratio","channel_coverage","demand_gap","amt_per_cust","new_cust","S"]

def scale(v):
    lo, hi = v.quantile(.02), v.quantile(.98); z = v.clip(lo,hi)
    return (z-lo)/(hi-lo) if hi>lo else pd.Series(.5,index=v.index)

def score(panel):
    z = pd.DataFrame(index=panel.index)
    for c,d in STATE: z[c] = scale(panel[c]) if d>0 else 1-scale(panel[c])
    z = z.apply(lambda x:x.fillna(x.median()))
    x = np.maximum(z.to_numpy(float),1e-8); p=x/x.sum(axis=0); e=-(p*np.log(p)).sum(0)/np.log(len(x))
    we=(1-e)/(1-e).sum(); sd=x.std(0); corr=np.nan_to_num(np.corrcoef(x,rowvar=False)); wc=sd*(1-np.abs(corr)).sum(1); wc/=wc.sum()
    w=(we+wc)/2; w/=w.sum()
    return x@w*100, pd.DataFrame({"feature":z.columns,"entropy":we,"critic":wc,"weight":w})

def smd(a,b):
    den=np.sqrt((np.nanvar(a,ddof=1)+np.nanvar(b,ddof=1))/2)
    return float((np.nanmean(a)-np.nanmean(b))/den) if den>0 else 0.0

def main():
    p=pd.read_csv(OUT/"raw_panel.csv",encoding="utf-8-sig").sort_values(["code","ym"]).reset_index(drop=True)
    p["S"], weights=score(p)
    p["S_prev"]=p.groupby("code")["S"].shift(1); p["S_next"]=p.groupby("code")["S"].shift(-1)
    p["Y"]=p["S_next"]-p["S_prev"]
    prev_fill=p.groupby("code")["fill"].shift(1)
    q35=p.groupby("ym")["fill"].transform(lambda x:x.quantile(.35))
    p["T"]=((p["fill"]<=q35)&((prev_fill-p["fill"])>2.0)).astype(int)
    for c in BASE_COVS: p[c+"_pre"]=p.groupby("code")[c].shift(1)
    dummies=pd.concat([pd.get_dummies(p["cat"],prefix="cat",dtype=int),pd.get_dummies(p["price_band_cat"],prefix="band",dtype=int)],axis=1)
    p=pd.concat([p,dummies],axis=1)
    cats=[f"cat_{x}" for x in ["一类烟","二类烟","三类烟","四类烟","五类烟"]]
    bands=[f"band_{x}" for x in ["低档","中低档","中档","中高档","高档"]]
    for c in cats+bands:
        if c not in p:p[c]=0
    covs=[c+"_pre" for c in BASE_COVS]+cats+bands
    d=p.dropna(subset=["Y","S_prev","S_next"]).copy()
    for c in covs:d[c]=d[c].fillna(d[c].median())
    ylo,yhi=d.Y.quantile([.01,.99]); d=d[d.Y.between(ylo,yhi)].copy()
    X=d[covs].to_numpy(float); Y=d["Y"].to_numpy(float); T=d["T"].to_numpy(int); groups=d["code"].to_numpy()
    model_y=RandomForestRegressor(n_estimators=300,min_samples_leaf=15,max_features=.8,n_jobs=-1,random_state=SEED)
    model_t=RandomForestClassifier(n_estimators=300,min_samples_leaf=15,max_features=.8,n_jobs=-1,random_state=SEED,class_weight="balanced")
    cf=CausalForestDML(model_y=model_y,model_t=model_t,discrete_treatment=True,cv=GroupKFold(5),
        n_estimators=600,min_samples_leaf=20,max_samples=.45,honest=True,inference=True,
        subforest_size=4,n_jobs=-1,random_state=SEED)
    cf.fit(Y,T,X=X,groups=groups)
    tau=np.asarray(cf.effect(X)).ravel(); lo,hi=cf.effect_interval(X); d["CATE"]=tau; d["CATE_lo"]=np.asarray(lo).ravel(); d["CATE_hi"]=np.asarray(hi).ravel()
    qlo,qhi=np.quantile(tau,[1/3,2/3]); d["sensitivity"]=pd.cut(tau,[-np.inf,qlo,qhi,np.inf],labels=["低敏感","中敏感","高敏感"]).astype(str)
    ate=float(cf.ate(X)); ate_lo,ate_hi=[float(np.asarray(v).ravel()[0]) for v in cf.ate_interval(X)]
    imp=np.asarray(cf.feature_importances_).ravel(); importance=pd.DataFrame({"feature":covs,"importance":imp}).sort_values("importance",ascending=False)
    tr=d[d["T"].eq(1)].copy(); cutoff=tr.CATE.quantile(2/3); tr["is_high"]=tr.CATE.ge(cutoff)
    high,other=tr[tr.is_high],tr[~tr.is_high]
    base_smd=smd(high.S_prev,other.S_prev); base_p=float(ttest_ind(high.S_prev,other.S_prev,equal_var=False).pvalue)
    # 1:1 无放回最近邻倾向得分匹配，用于稳健性而非替代主模型
    scaler=StandardScaler(); Xs=scaler.fit_transform(X); ps=LogisticRegression(max_iter=2000,class_weight="balanced",random_state=SEED).fit(Xs,T).predict_proba(Xs)[:,1]
    d["ps"]=ps; ti=np.flatnonzero(T==1); ci=np.flatnonzero(T==0); nn=NearestNeighbors(n_neighbors=1).fit(ps[ci,None]); used=set(); pairs=[]
    for pos in ti[np.argsort(ps[ti])]:
        for j in np.argsort(np.abs(ps[ci]-ps[pos])):
            idx=ci[j]
            if idx not in used: used.add(idx); pairs.append((pos,idx)); break
    smd_rows=[]
    for c in covs:smd_rows.append({"feature":c,"before":smd(d.loc[T==1,c],d.loc[T==0,c]),"after":smd(d.iloc[[a for a,b in pairs]][c],d.iloc[[b for a,b in pairs]][c])})
    matched_effect=float(np.mean([Y[a]-Y[b] for a,b in pairs]))
    metrics={"n":len(d),"products":int(d.code.nunique()),"treated":int(T.sum()),"covariates":len(covs),"covariate_names":covs,
      "ate":ate,"ate_ci":[ate_lo,ate_hi],"cate_sd":float(tau.std()),"q_low":float(qlo),"q_high":float(qhi),
      "honest_fraction_estimation":.55,"honest_fraction_splitting":.45,"min_samples_leaf":20,"trees":600,"group_cv_folds":5,
      "backtest":{"high_n":len(high),"other_n":len(other),"high_mean_change":float(high.Y.mean()),"other_mean_change":float(other.Y.mean()),
        "high_improvement":float((high.Y>0).mean()),"other_improvement":float((other.Y>0).mean()),"baseline_smd":base_smd,"baseline_p":base_p},
      "psm":{"pairs":len(pairs),"effect":matched_effect,"mean_abs_smd_before":float(np.mean(np.abs([x['before'] for x in smd_rows]))),"mean_abs_smd_after":float(np.mean(np.abs([x['after'] for x in smd_rows])))}}
    d.to_csv(OUT/"causal_forest_panel.csv",index=False,encoding="utf-8-sig"); weights.to_csv(OUT/"state_weights.csv",index=False,encoding="utf-8-sig")
    importance.to_csv(OUT/"feature_importance.csv",index=False,encoding="utf-8-sig"); pd.DataFrame(smd_rows).to_csv(OUT/"psm_smd.csv",index=False,encoding="utf-8-sig")
    with open(OUT/"metrics.json","w",encoding="utf-8") as f:json.dump(metrics,f,ensure_ascii=False,indent=2)
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
