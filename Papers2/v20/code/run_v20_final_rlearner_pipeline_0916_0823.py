# -*- coding: utf-8 -*-
"""
v20最终一致口径实验管线 0916_0823
- 从 raw_panel_v1.csv 重建处理定义独立状态评分 S*
- T 仅在当月及上月 fill 有效时定义
- 动态X全部滞后1期
- R-learner + LightGBM异质性排序（如实命名，不再误称因果森林）
- 四项硬实验：严格时间外DR、Top-k增益、随机种子稳定性、共同支持域AIPW
- 额外：真正处理前负对照 Y_pre=S*_{t-1}-S*_{t-2}
"""
from pathlib import Path
import json, math, warnings
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import lightgbm as lgb
warnings.filterwarnings('ignore')
STAMP='0916_0823'
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'Papers2'/'v18'/'data'/'raw_panel_v1.csv'
OUT=ROOT/'Papers2'/'v20'/'experiments'/STAMP
FIG=OUT/'figures'; OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
REG=dict(objective='regression',n_estimators=180,learning_rate=.05,num_leaves=20,min_child_samples=20,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
CLF=dict(objective='binary',n_estimators=180,learning_rate=.05,num_leaves=20,min_child_samples=20,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
STATE=[('price_index',1),('gross_margin',1),('inventory_ratio',-1),('sell_rate',1)]
DYN=['fill','util','full_surf','ord_success','price_index','gross_margin','unitval','inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','sell_rate','salable_days','Sstar']

def group_folds(groups,n=5,seed=42):
    u=np.array(pd.unique(groups)); r=np.random.RandomState(seed); r.shuffle(u); bs=np.array_split(u,n); g=np.asarray(groups)
    return [(np.flatnonzero(~np.isin(g,b)),np.flatnonzero(np.isin(g,b))) for b in bs]

def monthly_rank_score(d):
    parts=[]
    for c,sgn in STATE:
        r=d.groupby('ym')[c].rank(pct=True,method='average')
        if sgn<0: r=1-r
        # missing gets neutral 0.5; record coverage separately
        parts.append(r.fillna(.5))
    Z=np.column_stack(parts)
    d['Sstar']=100*np.nanmean(Z,axis=1)
    return d

def prepare():
    d=pd.read_csv(DATA,encoding='utf-8-sig').sort_values(['code','ym']).reset_index(drop=True)
    d=monthly_rank_score(d)
    # outcome t+1 - t
    d['Sstar_next']=d.groupby('code')['Sstar'].shift(-1); d['Y']=d['Sstar_next']-d['Sstar']
    # true pre-treatment negative-control outcome: t-1 minus t-2
    s1=d.groupby('code')['Sstar'].shift(1); s2=d.groupby('code')['Sstar'].shift(2); d['Y_pre']=s1-s2
    # Treatment only where current and previous fill observed; no missing-as-control.
    d['fill_prev']=d.groupby('code')['fill'].shift(1)
    q35=d.groupby('month')['fill'].transform(lambda x:x.quantile(.35))
    valid=d['fill'].notna() & d['fill_prev'].notna() & q35.notna()
    d['T']=np.nan; d.loc[valid,'T']=((d.loc[valid,'fill']<=q35[valid]) & ((d.loc[valid,'fill_prev']-d.loc[valid,'fill'])>2.0)).astype(int)
    # dynamic X -> t-1
    static=pd.get_dummies(d[['cat','price_band_cat']].fillna('未知'),prefix=['cat','band']).astype(int)
    d=pd.concat([d,static],axis=1); lag=[]
    for c in DYN:
        if c in d:
            z='lag_'+c; d[z]=d.groupby('code')[c].shift(1); lag.append(z)
    feats=lag+[c for c in d if c.startswith('cat_') or c.startswith('band_')]
    x=d[['code','ym','T','Y','Y_pre']+feats].dropna(subset=['T','Y']).copy(); good=[]
    for c in feats:
        if x[c].notna().mean()>=.55 and x[c].nunique(dropna=True)>1:
            x[c]=x[c].fillna(x[c].median()); good.append(c)
    x=x[['code','ym','T','Y','Y_pre']+good].copy(); x['T']=x['T'].astype(int); x['ym']=x['ym'].astype(int)
    # robust outcome restriction only, pre-specified 1-99%; no treatment-dependent trimming
    lo,hi=np.percentile(x.Y.dropna(),[1,99]); x=x[x.Y.between(lo,hi)].copy()
    return x.reset_index(drop=True),good,d

def fit_rlearner(train,feats,seed=42):
    X=train[feats].to_numpy(float); T=train['T'].to_numpy(int); Y=train.Y.to_numpy(float); mu=np.full(len(train),np.nan); e=np.full(len(train),np.nan)
    for tr,va in group_folds(train.code.values,5,seed):
        ry=lgb.LGBMRegressor(**REG,random_state=seed); ry.fit(X[tr],Y[tr]); mu[va]=ry.predict(X[va])
        cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X[tr],T[tr]); e[va]=cl.predict_proba(X[va])[:,1]
    e=np.clip(e,.02,.98); tt=T-e; rho=(Y-mu)/np.where(np.abs(tt)<1e-4,1e-4,tt); q1,q2=np.percentile(rho,[3,97]); rho=np.clip(rho,q1,q2)
    m=lgb.LGBMRegressor(**REG,random_state=seed); m.fit(X,rho,sample_weight=tt**2); return m

def fit_nuisance(train,test,feats,seed=42):
    X=train[feats].to_numpy(float); Xt=test[feats].to_numpy(float); T=train['T'].to_numpy(int); Y=train.Y.to_numpy(float)
    cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X,T); e=np.clip(cl.predict_proba(Xt)[:,1],.03,.97)
    m1=lgb.LGBMRegressor(**REG,random_state=seed); m0=lgb.LGBMRegressor(**REG,random_state=seed); m1.fit(X[T==1],Y[T==1]); m0.fit(X[T==0],Y[T==0])
    return e,m1.predict(Xt),m0.predict(Xt)

def strict_oot(d,feats):
    preds=[]; rows=[]
    for m in sorted(d.ym.unique()):
        tr=d[d.ym<m]; te=d[d.ym==m].copy()
        if tr.ym.nunique()<7 or tr['T'].sum()<20 or te['T'].sum()<2: continue
        tau=np.clip(fit_rlearner(tr,feats,42).predict(te[feats]),-25,25); e,m1,m0=fit_nuisance(tr,te,feats); T=te['T'].to_numpy(int); Y=te.Y.to_numpy(float)
        dr=(m1-m0)+T*(Y-m1)/e-(1-T)*(Y-m0)/(1-e)
        z=te[['code','ym','T','Y']].copy(); z['tau_oot']=tau; z['dr_score']=dr; z['e_test']=e
        for c in ['lag_Sstar','lag_inventory_ratio','lag_price_index']:
            if c in te:z[c]=te[c].values
        preds.append(z); n=max(5,int(math.ceil(.3*len(z)))); a=z.nlargest(n,'tau_oot'); b=z.drop(a.index)
        rows.append(dict(ym=int(m),n=len(z),n_treat=int(z['T'].sum()),top30_n=n,top30_dr=a.dr_score.mean(),rest_dr=b.dr_score.mean(),dr_lift=a.dr_score.mean()-b.dr_score.mean(),rho_tau_dr=spearmanr(z.tau_oot,z.dr_score).statistic))
    p=pd.concat(preds,ignore_index=True); mon=pd.DataFrame(rows); p.to_csv(OUT/'oot_dr_predictions.csv',index=False,encoding='utf-8-sig'); mon.to_csv(OUT/'oot_dr_monthly.csv',index=False,encoding='utf-8-sig'); return mon,p

def topk(p):
    rows=[]
    for pct in [10,20,30,40,50]:
        n=max(5,int(math.ceil(len(p)*pct/100))); a=p.nlargest(n,'tau_oot'); r=dict(top_pct=pct,n=n,model_dr=a.dr_score.mean(),all_dr=p.dr_score.mean(),gain_vs_all=a.dr_score.mean()-p.dr_score.mean())
        if 'lag_Sstar' in p:
            b=p.nlargest(n,'lag_Sstar'); r['state_dr']=b.dr_score.mean(); r['gain_vs_state']=a.dr_score.mean()-b.dr_score.mean()
        if 'lag_inventory_ratio' in p:
            b=p.nlargest(n,'lag_inventory_ratio'); r['inventory_dr']=b.dr_score.mean(); r['gain_vs_inventory']=a.dr_score.mean()-b.dr_score.mean()
        rows.append(r)
    x=pd.DataFrame(rows); x.to_csv(OUT/'topk_dr_gain.csv',index=False,encoding='utf-8-sig'); return x

def stability(d,feats):
    X=d[feats].to_numpy(float); seeds=list(range(101,113)); arr=[]
    for s in seeds: arr.append(np.clip(fit_rlearner(d,feats,s).predict(X),-25,25))
    ref=arr[0]; n=max(1,int(math.ceil(.2*len(d)))); rs=set(np.argsort(ref)[-n:]); rows=[]
    for s,t in zip(seeds,arr): rows.append(dict(seed=s,spearman=spearmanr(ref,t).statistic,top20_overlap=len(rs&set(np.argsort(t)[-n:]))/n,cate_mean=np.mean(t),cate_sd=np.std(t)))
    x=pd.DataFrame(rows); x.to_csv(OUT/'seed_stability.csv',index=False,encoding='utf-8-sig'); return x

def aipw(d,feats,outcome='Y',seed=42):
    q=d.dropna(subset=[outcome]).copy(); X=q[feats].to_numpy(float); T=q['T'].to_numpy(int); Y=q[outcome].to_numpy(float); n=len(q); e=np.full(n,np.nan); m1=np.full(n,np.nan); m0=np.full(n,np.nan)
    for tr,va in group_folds(q.code.values,5,seed):
        cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X[tr],T[tr]); e[va]=cl.predict_proba(X[va])[:,1]
        i1=tr[T[tr]==1]; i0=tr[T[tr]==0]; a=lgb.LGBMRegressor(**REG,random_state=seed); b=lgb.LGBMRegressor(**REG,random_state=seed); a.fit(X[i1],Y[i1]); b.fit(X[i0],Y[i0]); m1[va]=a.predict(X[va]); m0[va]=b.predict(X[va])
    e=np.clip(e,.02,.98); lo=max(e[T==1].min(),e[T==0].min()); hi=min(e[T==1].max(),e[T==0].max()); support=(e>=lo)&(e<=hi)
    def one(mask,label):
        ee=e[mask]; tt=T[mask]; yy=Y[mask]; a=m1[mask]; b=m0[mask]; psi=(a-b)+tt*(yy-a)/ee-(1-tt)*(yy-b)/(1-ee); est=float(psi.mean()); se=float(psi.std(ddof=1)/np.sqrt(len(psi))); return dict(outcome=outcome,sample=label,n=int(mask.sum()),n_treat=int(tt.sum()),estimate=est,se=se,ci_low=est-1.96*se,ci_high=est+1.96*se)
    res=pd.DataFrame([one(np.ones(n,dtype=bool),'full'),one(support,'common_support')]); res['support_lo']=lo;res['support_hi']=hi;res['treated_outside_pct']=100*((~support)&(T==1)).sum()/max(1,(T==1).sum()); return res

def bootstrap_ci(p):
    rng=np.random.RandomState(20260916); ms=p.ym.unique(); vals=[]
    for _ in range(500):
        sel=rng.choice(ms,size=len(ms),replace=True); q=pd.concat([p[p.ym==m] for m in sel],ignore_index=True); n=max(5,int(math.ceil(.3*len(q)))); a=q.nlargest(n,'tau_oot'); b=q.drop(a.index); vals.append(a.dr_score.mean()-b.dr_score.mean())
    return np.percentile(vals,[2.5,50,97.5])

def plots(mon,tk,st,eff):
    plt.rcParams['font.family']='DejaVu Sans';plt.rcParams['svg.fonttype']='none'
    fig,ax=plt.subplots(figsize=(8.7,4.8));ax.axhline(0,color='black',ls='--',lw=1);ax.plot(mon.ym.astype(str),mon.dr_lift,marker='o');ax.set(xlabel='Test month',ylabel='Top-30% DR lift',title='Strict out-of-time DR validation');ax.tick_params(axis='x',rotation=45);ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(FIG/'fig1_oot_dr.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.9,4.8));ax.plot(tk.top_pct,tk.gain_vs_all,marker='o',label='vs all');ax.plot(tk.top_pct,tk.gain_vs_state,marker='s',label='vs state score');ax.plot(tk.top_pct,tk.gain_vs_inventory,marker='^',label='vs inventory ratio');ax.axhline(0,color='black',ls='--',lw=1);ax.set(xlabel='Top-k (%)',ylabel='DR gain',title='Top-k out-of-time ranking gain');ax.legend(frameon=False);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(FIG/'fig2_topk_gain.svg');plt.close(fig)
    q=st[st.seed!=101];fig,ax=plt.subplots(figsize=(7.6,4.8));ax.scatter(q.spearman,q.top20_overlap,s=50);ax.axvline(q.spearman.median(),ls='--',lw=1);ax.axhline(q.top20_overlap.median(),ls='--',lw=1);ax.set(xlabel='Spearman vs seed101',ylabel='Top-20% overlap',title='Random-seed ranking stability');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(FIG/'fig3_seed_stability.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.2,4.5));r=eff[eff.outcome=='Y'];yy=np.arange(len(r))[::-1];
    for y,(_,z) in zip(yy,r.iterrows()):ax.plot([z.ci_low,z.ci_high],[y,y],lw=2);ax.scatter(z.estimate,y,s=50)
    ax.axvline(0,color='black',ls='--',lw=1);ax.set_yticks(yy,r['sample']);ax.set(xlabel='AIPW estimate (95% CI)',title='Common-support re-estimation');ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(FIG/'fig4_overlap_aipw.svg');plt.close(fig)

def main():
    d,f,raw=prepare(); mon,p=strict_oot(d,f); tk=topk(p); st=stability(d,f); eff=pd.concat([aipw(d,f,'Y'),aipw(d,f,'Y_pre')],ignore_index=True); eff.to_csv(OUT/'aipw_and_negative_control.csv',index=False,encoding='utf-8-sig'); ci=bootstrap_ci(p); plots(mon,tk,st,eff)
    q=st[st.seed!=101]; e=eff[(eff.outcome=='Y')&(eff['sample']=='common_support')].iloc[0]; neg=eff[(eff.outcome=='Y_pre')&(eff['sample']=='common_support')].iloc[0]
    s=dict(base_rows=int(len(raw)),analysis_n=int(len(d)),analysis_specs=int(d.code.nunique()),analysis_treated=int(d['T'].sum()),oot_n=int(len(p)),oot_months=int(len(mon)),top30_month_mean=float(mon.dr_lift.mean()),top30_positive_months=int((mon.dr_lift>0).sum()),top30_boot_ci_low=float(ci[0]),top30_boot_ci_high=float(ci[2]),top30_gain_vs_all=float(tk.loc[tk.top_pct==30,'gain_vs_all'].iloc[0]),top30_gain_vs_state=float(tk.loc[tk.top_pct==30,'gain_vs_state'].iloc[0]),top30_gain_vs_inventory=float(tk.loc[tk.top_pct==30,'gain_vs_inventory'].iloc[0]),seed_spearman_median=float(q.spearman.median()),seed_top20_overlap_median=float(q.top20_overlap.median()),support_ate=float(e.estimate),support_ci_low=float(e.ci_low),support_ci_high=float(e.ci_high),treated_outside_pct=float(e.treated_outside_pct),negative_control=float(neg.estimate),negative_control_ci_low=float(neg.ci_low),negative_control_ci_high=float(neg.ci_high))
    # Indicator coverage audit
    cov={c:float(raw[c].notna().mean()) for c,_ in STATE if c in raw}; s['state_indicator_coverage']=cov
    (OUT/'final_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame([s]).to_csv(OUT/'final_summary.csv',index=False,encoding='utf-8-sig')
    print(json.dumps(s,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
