# -*- coding: utf-8 -*-
"""v20-7 严格滚动时间外 + DR/RATE式排序验证。
训练月 < 测试月；测试月用训练期拟合的 propensity/m1/m0 构造DR伪结果，评价因果森林排序。
"""
from pathlib import Path
import json, math, warnings
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import lightgbm as lgb
warnings.filterwarnings('ignore')
STAMP='0916_0811'
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'Papers2'/'v18'/'data'/'causal_forest_panel_v1.csv'
OUT=ROOT/'Papers2'/'v20'/'experiments'/STAMP/'dr_oot'
FIG=OUT/'figures'; OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
REG=dict(objective='regression',n_estimators=180,learning_rate=.05,num_leaves=20,min_child_samples=25,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
CLF=dict(objective='binary',n_estimators=180,learning_rate=.05,num_leaves=20,min_child_samples=25,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
DYN=['util','fill','full_surf','ord_success','price_index','gross_margin','unitval','inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','S']

def folds(groups,n=5,seed=42):
    u=np.array(pd.unique(groups)); r=np.random.RandomState(seed); r.shuffle(u); bs=np.array_split(u,n); g=np.asarray(groups)
    return [(np.flatnonzero(~np.isin(g,b)),np.flatnonzero(np.isin(g,b))) for b in bs]

def prepare():
    d=pd.read_csv(DATA,encoding='utf-8-sig').sort_values(['code','ym']).reset_index(drop=True)
    static=[c for c in d if c.startswith('cat_') or c.startswith('band_')]; lag=[]
    for c in DYN:
        if c in d:
            z='lag_'+c; d[z]=d.groupby('code')[c].shift(1); lag.append(z)
    feats=lag+static; x=d[['code','ym','T','Y']+feats].dropna(subset=['T','Y']).copy(); good=[]
    for c in feats:
        if x[c].notna().mean()>=.55 and x[c].nunique(dropna=True)>1:
            x[c]=x[c].fillna(x[c].median()); good.append(c)
    x=x[['code','ym','T','Y']+good].dropna(); lo,hi=np.percentile(x.Y,[1,99]); x=x[x.Y.between(lo,hi)].copy()
    if 'lag_inventory_ratio' in x:
        x=x[x.lag_inventory_ratio<np.percentile(x.lag_inventory_ratio,99)]
    x['ym']=x.ym.astype(int); x['T']=x.T.astype(int) if False else x['T'].astype(int)
    return x.reset_index(drop=True),good

def fit_tau(train,feats,seed=42):
    X=train[feats].to_numpy(float); T=train['T'].to_numpy(int); Y=train.Y.to_numpy(float); mu=np.full(len(train),np.nan); ep=np.full(len(train),np.nan)
    for tr,va in folds(train.code.values,5,seed):
        ry=lgb.LGBMRegressor(**REG,random_state=seed); ry.fit(X[tr],Y[tr]); mu[va]=ry.predict(X[va])
        cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X[tr],T[tr]); ep[va]=cl.predict_proba(X[va])[:,1]
    ep=np.clip(ep,.02,.98); tt=T-ep; rho=(Y-mu)/np.where(abs(tt)<1e-4,1e-4,tt); a,b=np.percentile(rho,[3,97]); rho=np.clip(rho,a,b)
    m=lgb.LGBMRegressor(**REG,random_state=seed); m.fit(X,rho,sample_weight=tt**2); return m

def nuisance_predict(train,test,feats,seed=42):
    X=train[feats].to_numpy(float); Xt=test[feats].to_numpy(float); T=train['T'].to_numpy(int); Y=train.Y.to_numpy(float)
    cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X,T); e=np.clip(cl.predict_proba(Xt)[:,1],.03,.97)
    m1=lgb.LGBMRegressor(**REG,random_state=seed); m0=lgb.LGBMRegressor(**REG,random_state=seed)
    m1.fit(X[T==1],Y[T==1]); m0.fit(X[T==0],Y[T==0]); return e,m1.predict(Xt),m0.predict(Xt)

def main():
    d,f=prepare(); allpred=[]; month=[]
    for m in sorted(d.ym.unique()):
        tr=d[d.ym<m]; te=d[d.ym==m].copy()
        if tr.ym.nunique()<8 or tr['T'].sum()<25 or te['T'].sum()<3: continue
        tau=np.clip(fit_tau(tr,f,42).predict(te[f]),-25,25); e,m1,m0=nuisance_predict(tr,te,f,42); T=te['T'].to_numpy(int); Y=te.Y.to_numpy(float)
        dr=(m1-m0)+T*(Y-m1)/e-(1-T)*(Y-m0)/(1-e)
        z=te[['code','ym','T','Y']].copy(); z['tau_oot']=tau; z['dr_score']=dr; z['propensity_test']=e
        for c in ['lag_S','lag_inventory_ratio']:
            if c in te: z[c]=te[c].values
        allpred.append(z)
        k=max(5,int(math.ceil(.30*len(z)))); top=z.nlargest(k,'tau_oot'); rest=z.drop(top.index)
        month.append(dict(ym=int(m),n=len(z),treated=int(z['T'].sum()),top30_n=k,top30_dr=top.dr_score.mean(),rest_dr=rest.dr_score.mean(),dr_lift=top.dr_score.mean()-rest.dr_score.mean(),spearman_tau_dr=spearmanr(z.tau_oot,z.dr_score).statistic))
    p=pd.concat(allpred,ignore_index=True); mon=pd.DataFrame(month); p.to_csv(OUT/'dr_oot_predictions.csv',index=False,encoding='utf-8-sig'); mon.to_csv(OUT/'dr_oot_monthly.csv',index=False,encoding='utf-8-sig')
    rows=[]
    for pct in [10,20,30,40,50]:
        n=max(5,int(math.ceil(len(p)*pct/100))); mod=p.nlargest(n,'tau_oot'); rec=dict(top_pct=pct,n=n,model_dr=mod.dr_score.mean(),all_dr=p.dr_score.mean(),gain_vs_all=mod.dr_score.mean()-p.dr_score.mean())
        if 'lag_S' in p:
            b=p.nlargest(n,'lag_S'); rec['state_dr']=b.dr_score.mean(); rec['gain_vs_state']=mod.dr_score.mean()-b.dr_score.mean()
        if 'lag_inventory_ratio' in p:
            b=p.nlargest(n,'lag_inventory_ratio'); rec['inventory_dr']=b.dr_score.mean(); rec['gain_vs_inventory']=mod.dr_score.mean()-b.dr_score.mean()
        rows.append(rec)
    tk=pd.DataFrame(rows); tk.to_csv(OUT/'dr_topk_gain.csv',index=False,encoding='utf-8-sig')
    # cluster bootstrap by month for top30 lift vs rest
    rng=np.random.RandomState(20260916); months=p.ym.unique(); boots=[]
    for _ in range(500):
        sel=rng.choice(months,size=len(months),replace=True); q=pd.concat([p[p.ym==m] for m in sel],ignore_index=True); n=max(5,int(math.ceil(.30*len(q)))); a=q.nlargest(n,'tau_oot'); b=q.drop(a.index); boots.append(a.dr_score.mean()-b.dr_score.mean())
    ci=np.percentile(boots,[2.5,50,97.5])
    summary=dict(n=int(len(d)),oot_n=int(len(p)),oot_months=int(mon.shape[0]),dr_top30_month_mean=float(mon.dr_lift.mean()),dr_top30_month_median=float(mon.dr_lift.median()),dr_top30_positive_months=int((mon.dr_lift>0).sum()),dr_top30_boot_ci_low=float(ci[0]),dr_top30_boot_median=float(ci[1]),dr_top30_boot_ci_high=float(ci[2]),top20_gain_vs_all=float(tk.loc[tk.top_pct==20,'gain_vs_all'].iloc[0]),top30_gain_vs_all=float(tk.loc[tk.top_pct==30,'gain_vs_all'].iloc[0]),top40_gain_vs_all=float(tk.loc[tk.top_pct==40,'gain_vs_all'].iloc[0]),top30_gain_vs_state=float(tk.loc[tk.top_pct==30,'gain_vs_state'].iloc[0]))
    (OUT/'dr_oot_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.rcParams['font.family']='DejaVu Sans'; plt.rcParams['svg.fonttype']='none'
    fig,ax=plt.subplots(figsize=(8.6,4.8)); ax.axhline(0,color='black',lw=1,ls='--'); ax.plot(mon.ym.astype(str),mon.dr_lift,marker='o',lw=1.6); ax.set(xlabel='Test month',ylabel='DR Top-30% lift vs rest',title='Strict out-of-time DR ranking validation'); ax.tick_params(axis='x',rotation=45); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figE_dr_oot_monthly.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.8,4.8)); ax.plot(tk.top_pct,tk.gain_vs_all,marker='o',label='vs all test observations'); ax.plot(tk.top_pct,tk.gain_vs_state,marker='s',label='vs state-score baseline'); ax.axhline(0,color='black',lw=1,ls='--'); ax.set(xlabel='Top-k fraction (%)',ylabel='Mean DR-score gain',title='DR Top-k ranking gain'); ax.legend(frameon=False); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figF_dr_topk_gain.svg'); plt.close(fig)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
