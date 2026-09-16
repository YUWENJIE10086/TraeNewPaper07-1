# -*- coding: utf-8 -*-
from pathlib import Path
import json, math, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import lightgbm as lgb
warnings.filterwarnings('ignore')
STAMP='0916_0811'
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'Papers2'/'v18'/'data'/'causal_forest_panel_v1.csv'
OUT=ROOT/'Papers2'/'v20'/'experiments'/STAMP
FIG=OUT/'figures'; OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
REG=dict(objective='regression',n_estimators=160,learning_rate=0.05,num_leaves=20,min_child_samples=25,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
CLF=dict(objective='binary',n_estimators=160,learning_rate=0.05,num_leaves=20,min_child_samples=25,subsample=.85,colsample_bytree=.85,verbose=-1,n_jobs=2)
DYN=['util','fill','full_surf','ord_success','price_index','gross_margin','unitval','inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','S']

def folds(groups,n=5,seed=42):
    u=np.array(pd.unique(groups)); r=np.random.RandomState(seed); r.shuffle(u); arr=np.array_split(u,n); g=np.asarray(groups)
    return [(np.flatnonzero(~np.isin(g,b)),np.flatnonzero(np.isin(g,b))) for b in arr]

def prepare():
    d=pd.read_csv(DATA,encoding='utf-8-sig').sort_values(['code','ym']).reset_index(drop=True)
    static=[c for c in d.columns if c.startswith('cat_') or c.startswith('band_')]
    lag=[]
    for c in DYN:
        if c in d.columns:
            lc='lag_'+c; d[lc]=d.groupby('code')[c].shift(1); lag.append(lc)
    feats=lag+static; x=d[['code','ym','T','Y']+feats].copy().dropna(subset=['T','Y'])
    good=[]
    for c in feats:
        if x[c].notna().mean()>=.55 and x[c].nunique(dropna=True)>1:
            x[c]=x[c].fillna(x[c].median()); good.append(c)
    x=x[['code','ym','T','Y']+good].dropna().copy(); x['ym']=x['ym'].astype(int); x['T']=x['T'].astype(int)
    lo,hi=np.percentile(x.Y,[1,99]); x=x[x.Y.between(lo,hi)].copy()
    if 'lag_inventory_ratio' in x:
        cap=np.percentile(x['lag_inventory_ratio'],99); x=x[x['lag_inventory_ratio']<cap].copy()
    return x.reset_index(drop=True),good

def fit_r(d,feats,seed):
    X=d[feats].to_numpy(float); T=d['T'].to_numpy(float); Y=d.Y.to_numpy(float); mu=np.full(len(d),np.nan); ep=np.full(len(d),np.nan)
    for tr,va in folds(d.code.values,5,seed):
        ry=lgb.LGBMRegressor(**REG,random_state=seed); ry.fit(X[tr],Y[tr]); mu[va]=ry.predict(X[va])
        cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X[tr],T[tr].astype(int)); ep[va]=cl.predict_proba(X[va])[:,1]
    ep=np.clip(ep,.01,.99); yt=Y-mu; tt=T-ep; den=np.where(np.abs(tt)<1e-4,1e-4,tt); rho=yt/den; q1,q2=np.percentile(rho,[3,97]); rho=np.clip(rho,q1,q2)
    m=lgb.LGBMRegressor(**REG,random_state=seed); m.fit(X,rho,sample_weight=tt**2); return m

def rolling(d,feats):
    rows=[]; preds=[]
    for m in sorted(d.ym.unique()):
        tr=d[d.ym<m]; te=d[d.ym==m]
        if tr.ym.nunique()<8 or tr['T'].sum()<25 or te['T'].sum()<3: continue
        mod=fit_r(tr,feats,42); z=te[['code','ym','T','Y']].copy(); z['tau_oot']=np.clip(mod.predict(te[feats]),-25,25)
        for c in ['lag_S','lag_inventory_ratio']:
            if c in te: z[c]=te[c].values
        preds.append(z); q=z[z['T']==1].copy(); k=max(1,int(math.ceil(.3*len(q)))); top=q.nlargest(k,'tau_oot'); rest=q.drop(top.index)
        rows.append(dict(ym=int(m),n_train=len(tr),n_test=len(te),n_treat_test=len(q),top30_n=len(top),top30_mean_Y=top.Y.mean(),rest_mean_Y=rest.Y.mean() if len(rest) else np.nan,lift_top30=top.Y.mean()-(rest.Y.mean() if len(rest) else np.nan),top30_improve_rate=(top.Y>0).mean(),rest_improve_rate=(rest.Y>0).mean() if len(rest) else np.nan))
    a=pd.DataFrame(rows); p=pd.concat(preds,ignore_index=True); a.to_csv(OUT/'time_out_monthly.csv',index=False,encoding='utf-8-sig'); p.to_csv(OUT/'time_out_predictions.csv',index=False,encoding='utf-8-sig'); return a,p

def topk(p):
    q=p[p['T']==1].copy(); base=q.Y.mean(); rows=[]
    for pct in [10,20,30,40,50]:
        n=max(3,int(math.ceil(len(q)*pct/100))); m=q.nlargest(n,'tau_oot'); r=dict(top_pct=pct,n=n,all_treated_mean_Y=base,model_mean_Y=m.Y.mean(),model_gain_vs_all=m.Y.mean()-base,model_improve_rate=(m.Y>0).mean())
        if 'lag_S' in q:
            b=q.nlargest(n,'lag_S'); r['state_baseline_mean_Y']=b.Y.mean(); r['gain_vs_state']=m.Y.mean()-b.Y.mean()
        if 'lag_inventory_ratio' in q:
            b=q.nlargest(n,'lag_inventory_ratio'); r['inventory_baseline_mean_Y']=b.Y.mean(); r['gain_vs_inventory']=m.Y.mean()-b.Y.mean()
        rows.append(r)
    x=pd.DataFrame(rows); x.to_csv(OUT/'topk_gain.csv',index=False,encoding='utf-8-sig'); return x

def stability(d,feats):
    X=d[feats].to_numpy(float); seeds=list(range(101,113)); arr=[]
    for s in seeds: arr.append(np.clip(fit_r(d,feats,s).predict(X),-25,25))
    ref=arr[0]; n=max(1,int(math.ceil(.2*len(d)))); refset=set(np.argsort(ref)[-n:]); rows=[]
    for s,t in zip(seeds,arr):
        rows.append(dict(seed=s,spearman_vs_seed101=spearmanr(ref,t).statistic,top20_overlap_vs_seed101=len(refset&set(np.argsort(t)[-n:]))/n,cate_mean=np.mean(t),cate_sd=np.std(t)))
    x=pd.DataFrame(rows); x.to_csv(OUT/'seed_stability.csv',index=False,encoding='utf-8-sig'); A=np.vstack(arr); c=d[['code','ym','T','Y']].copy(); c['tau_seed_mean']=A.mean(0); c['tau_seed_sd']=A.std(0); c.to_csv(OUT/'seed_consensus_predictions.csv',index=False,encoding='utf-8-sig'); return x

def overlap(d,feats,seed=42):
    X=d[feats].to_numpy(float); T=d['T'].to_numpy(int); Y=d.Y.to_numpy(float); n=len(d); e=np.full(n,np.nan); m1=np.full(n,np.nan); m0=np.full(n,np.nan)
    for tr,va in folds(d.code.values,5,seed):
        cl=lgb.LGBMClassifier(**CLF,random_state=seed); cl.fit(X[tr],T[tr]); e[va]=cl.predict_proba(X[va])[:,1]
        i1=tr[T[tr]==1]; i0=tr[T[tr]==0]; a=lgb.LGBMRegressor(**REG,random_state=seed); b=lgb.LGBMRegressor(**REG,random_state=seed); a.fit(X[i1],Y[i1]); b.fit(X[i0],Y[i0]); m1[va]=a.predict(X[va]); m0[va]=b.predict(X[va])
    e=np.clip(e,.02,.98); lo=max(e[T==1].min(),e[T==0].min()); hi=min(e[T==1].max(),e[T==0].max()); support=(e>=lo)&(e<=hi)
    def one(mask,label):
        ee=e[mask]; tt=T[mask]; yy=Y[mask]; a=m1[mask]; b=m0[mask]; psi=(a-b)+tt*(yy-a)/ee-(1-tt)*(yy-b)/(1-ee); ate=float(psi.mean()); se=float(psi.std(ddof=1)/np.sqrt(len(psi))); return dict(sample=label,n=int(mask.sum()),n_treat=int(tt.sum()),ate_aipw=ate,se=se,ci_low=ate-1.96*se,ci_high=ate+1.96*se)
    x=pd.DataFrame([one(np.ones(n,dtype=bool),'full'),one(support,'common_support')]); x['support_lo']=lo; x['support_hi']=hi; x['treated_outside_support_pct']=100*((~support)&(T==1)).sum()/max(1,(T==1).sum()); x.to_csv(OUT/'overlap_reestimate.csv',index=False,encoding='utf-8-sig')
    p=d[['code','ym','T','Y']].copy(); p['propensity_oof']=e; p['in_common_support']=support.astype(int); p.to_csv(OUT/'overlap_propensity.csv',index=False,encoding='utf-8-sig'); return x,p

def plots(mon,tk,st,ov,p):
    plt.rcParams['font.family']='DejaVu Sans'; plt.rcParams['svg.fonttype']='none'
    fig,ax=plt.subplots(figsize=(8.8,4.8)); ax.axhline(0,lw=1,ls='--'); ax.plot(mon.ym.astype(str),mon.lift_top30,marker='o'); ax.set(xlabel='Test month',ylabel='Top-30% Y lift vs remaining treated',title='Rolling out-of-time ranking lift'); ax.tick_params(axis='x',rotation=45); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figA_time_out_lift.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.8,4.7)); ax.plot(tk.top_pct,tk.model_gain_vs_all,marker='o',label='Model vs all treated');
    if 'gain_vs_state' in tk: ax.plot(tk.top_pct,tk.gain_vs_state,marker='s',label='Model vs state baseline')
    ax.axhline(0,lw=1,ls='--'); ax.set(xlabel='Top-k fraction (%)',ylabel='Mean next-period Y gain',title='Out-of-time Top-k ranking gain'); ax.legend(frameon=False); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figB_topk_gain.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.8,4.7)); ax.scatter(st.spearman_vs_seed101,st.top20_overlap_vs_seed101,s=45); ax.set(xlabel='Spearman vs seed 101',ylabel='Top-20% overlap vs seed 101',title='Ranking stability across seeds'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figC_seed_stability.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.2,4.7)); bins=np.linspace(p.propensity_oof.min(),p.propensity_oof.max(),28); ax.hist(p.loc[p['T']==0,'propensity_oof'],bins=bins,density=True,histtype='step',lw=1.8,label='Control'); ax.hist(p.loc[p['T']==1,'propensity_oof'],bins=bins,density=True,histtype='step',lw=1.8,label='Treated'); ax.axvline(float(ov.support_lo.iloc[0]),ls='--',lw=1); ax.axvline(float(ov.support_hi.iloc[0]),ls='--',lw=1); ax.set(xlabel='OOF propensity score',ylabel='Density',title='Common-support diagnostics'); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG/'figD_overlap_propensity.svg'); plt.close(fig)

def main():
    d,f=prepare(); mon,p=rolling(d,f); tk=topk(p); st=stability(d,f); ov,pp=overlap(d,f); plots(mon,tk,st,ov,pp)
    s={'analysis_n':len(d),'analysis_specs':int(d.code.nunique()),'analysis_months':int(d.ym.nunique()),'analysis_treated':int(d['T'].sum()),'oot_months':len(mon),'oot_treated_n':int((p['T']==1).sum()),'oot_lift_top30_mean':float(mon.lift_top30.mean()),'oot_lift_top30_median':float(mon.lift_top30.median()),'top20_gain_vs_all':float(tk.loc[tk.top_pct==20,'model_gain_vs_all'].iloc[0]),'top20_gain_vs_state':float(tk.loc[tk.top_pct==20,'gain_vs_state'].iloc[0]),'seed_spearman_median':float(st.loc[st.seed!=101,'spearman_vs_seed101'].median()),'seed_top20_overlap_median':float(st.loc[st.seed!=101,'top20_overlap_vs_seed101'].median()),'support_ate':float(ov.loc[ov['sample']=='common_support','ate_aipw'].iloc[0]),'support_ci_low':float(ov.loc[ov['sample']=='common_support','ci_low'].iloc[0]),'support_ci_high':float(ov.loc[ov['sample']=='common_support','ci_high'].iloc[0]),'treated_outside_support_pct':float(ov.treated_outside_support_pct.iloc[0])}; (OUT/'hard_experiments_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    h=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>v20-7四项硬实验</title><style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.7;max-width:1100px;margin:30px auto;padding:0 24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:8px}}img{{max-width:100%}}</style><body><h1>v20-7 四项硬实验重算报告</h1><p>分析子样本n={s['analysis_n']}，品规{s['analysis_specs']}个；时间外测试窗{s['oot_months']}个月，处理观测{s['oot_treated_n']}条。</p><h2>时间外验证</h2><p>Top-30%相对其余处理对象的下一期状态变化月均提升 {s['oot_lift_top30_mean']:.3f}，中位提升 {s['oot_lift_top30_median']:.3f}。</p><img src="figures/figA_time_out_lift.svg"><h2>Top-k增益</h2><p>Top-20%相对全部处理对象增益 {s['top20_gain_vs_all']:.3f}；相对处理前状态评分基线增益 {s['top20_gain_vs_state']:.3f}。</p><img src="figures/figB_topk_gain.svg">{tk.to_html(index=False,float_format=lambda x:f'{x:.3f}')}<h2>随机种子稳定性</h2><p>Spearman中位数 {s['seed_spearman_median']:.3f}；Top-20%重合率中位数 {s['seed_top20_overlap_median']:.3f}。</p><img src="figures/figC_seed_stability.svg"><h2>共同支持域内重估</h2><p>处理样本支持域外占比 {s['treated_outside_support_pct']:.2f}%；支持域内AIPW={s['support_ate']:.3f}，95%CI [{s['support_ci_low']:.3f}, {s['support_ci_high']:.3f}]。</p><img src="figures/figD_overlap_propensity.svg">{ov.to_html(index=False,float_format=lambda x:f'{x:.3f}')}</body></html>'''; (OUT/'hard_experiments_report.html').write_text(h,encoding='utf-8'); print(json.dumps(s,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
