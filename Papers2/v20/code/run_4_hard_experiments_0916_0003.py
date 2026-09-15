# -*- coding: utf-8 -*-
"""Four hard validation experiments for v20.

Current manuscript definition:
- S*: treatment-definition-independent state score from price_index(+), gross_margin(+), inventory_ratio(-), sell_rate(+)
- T_t: fill <= same calendar-month P35 and fill_{t-1}-fill_t > 2 percentage points
- X: strictly t-1 operating profile
- Y: S*_{t+1} - S*_t

Experiments:
1) rolling out-of-time validation;
2) Top-k ranking gain / AUUC based on out-of-fold doubly-robust scores;
3) random-seed ranking stability;
4) common-support-domain re-estimation.
"""
from pathlib import Path
import json, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from econml.dml import CausalForestDML
import matplotlib.pyplot as plt

STAMP='0916_0003'
ROOT=Path(__file__).resolve().parents[2]  # Papers2
RAW=ROOT/'v18'/'data'/'raw_panel_v1.csv'
OUT=ROOT/'v20'/'experiments'/STAMP
FIG=OUT/'figures'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)

STATE=[('price_index',1),('gross_margin',1),('inventory_ratio',-1),('sell_rate',1)]
X_BASE=['util','full_surf','price_index','gross_margin','unitval','inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','sell_rate','salable_days','purch_surf','rep_rate2']


def robust_score(s, direction=1):
    s=pd.to_numeric(s,errors='coerce')
    lo,hi=s.quantile(.02),s.quantile(.98)
    z=s.clip(lo,hi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi-lo<1e-12:
        z=pd.Series(.5,index=s.index)
    else:
        z=(z-lo)/(hi-lo)
    if direction<0: z=1-z
    return z


def build_data():
    p=pd.read_csv(RAW,encoding='utf-8-sig',low_memory=False)
    p['ym']=p['ym'].astype(int); p=p.sort_values(['code','ym']).reset_index(drop=True)
    valid=[]
    for c,d in STATE:
        if c in p and p[c].notna().mean()>=.35 and p[c].nunique(dropna=True)>1:
            p['_z_'+c]=robust_score(p[c],d); valid.append(c)
    if len(valid)<3: raise RuntimeError(f'Insufficient state indicators: {valid}')
    p['S']=p[['_z_'+c for c in valid]].mean(axis=1)*100
    p['S_next']=p.groupby('code')['S'].shift(-1); p['Y']=p['S_next']-p['S']
    # treatment: same calendar month across years, matching legacy paper definition
    if 'month' not in p: p['month']=p['ym']%100
    q35=p.groupby('month')['fill'].transform(lambda x:x.quantile(.35))
    fill_prev=p.groupby('code')['fill'].shift(1)
    p['T']=((p['fill']<=q35)&((fill_prev-p['fill'])>2.0)).astype(int)
    # strictly lag all X
    xcols=[]
    for c in X_BASE:
        if c in p and p[c].notna().mean()>=.25 and p[c].nunique(dropna=True)>1:
            lc='L1_'+c; p[lc]=p.groupby('code')[c].shift(1); xcols.append(lc)
    # lagged state itself is allowed as pre-treatment baseline
    p['L1_S']=p.groupby('code')['S'].shift(1); xcols.append('L1_S')
    # static category / price-band dummies
    for c in ['cat','price_band_cat']:
        if c in p:
            dummies=pd.get_dummies(p[c],prefix=c,dtype=int)
            p=pd.concat([p,dummies],axis=1); xcols += list(dummies.columns)
    keep=['code','ym','name','cat','T','Y','S','fill']+xcols
    d=p[keep].dropna(subset=['Y','T']).copy()
    # robust outcome/inventory trimming as in legacy work, but no treatment-derived field in S
    yl,yh=d['Y'].quantile([.01,.99]); d=d[d['Y'].between(yl,yh)].copy()
    # impute using global median only for the exported analysis dataset; every fold also fits models only on train
    for c in xcols:
        med=pd.to_numeric(d[c],errors='coerce').median(); d[c]=pd.to_numeric(d[c],errors='coerce').fillna(med if np.isfinite(med) else 0)
    return d.reset_index(drop=True), xcols, valid


def new_cf(seed=42,n_estimators=400):
    return CausalForestDML(
        model_y=RandomForestRegressor(n_estimators=160,min_samples_leaf=12,max_features=.8,n_jobs=-1,random_state=seed),
        model_t=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced',random_state=seed)),
        discrete_treatment=True,
        n_estimators=n_estimators,min_samples_leaf=15,max_depth=12,max_samples=.45,
        honest=True,cv=3,random_state=seed,n_jobs=-1,inference=False
    )


def fit_cf_predict(train,test,xcols,seed=42,n_estimators=400):
    m=new_cf(seed,n_estimators); m.fit(train.Y.values,T=train.T.values,X=train[xcols].values)
    return np.asarray(m.effect(test[xcols].values)).reshape(-1),m


def dr_scores(train,test,xcols,seed=42):
    Xtr=train[xcols].values; Xte=test[xcols].values
    prop=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced',random_state=seed))
    prop.fit(Xtr,train.T); e=np.clip(prop.predict_proba(Xte)[:,1],.03,.97)
    m0=RandomForestRegressor(n_estimators=200,min_samples_leaf=10,max_features=.8,n_jobs=-1,random_state=seed)
    m1=RandomForestRegressor(n_estimators=200,min_samples_leaf=8,max_features=.8,n_jobs=-1,random_state=seed+1)
    m0.fit(Xtr[train.T.values==0],train.Y.values[train.T.values==0]); m1.fit(Xtr[train.T.values==1],train.Y.values[train.T.values==1])
    mu0=m0.predict(Xte); mu1=m1.predict(Xte); t=test.T.values; y=test.Y.values
    return (mu1-mu0)+t*(y-mu1)/e-(1-t)*(y-mu0)/(1-e), e


def topk_metrics(tau,score,ks=(.1,.2,.3)):
    order=np.argsort(-tau); base=float(np.mean(score)); rows=[]
    for k in ks:
        n=max(1,int(np.ceil(k*len(order)))); val=float(np.mean(score[order[:n]]))
        rows.append((k,n,val,base,val-base))
    centered=score-base; cg=np.cumsum(centered[order])/len(order); frac=np.arange(1,len(order)+1)/len(order)
    auuc=float(np.trapz(cg,frac))
    return rows,auuc,frac,cg


def cluster_boot_gain(df,tau,score,k=.2,B=400,seed=2026):
    rng=np.random.default_rng(seed); codes=np.array(df.code.unique()); vals=[]
    tmp=df[['code']].copy(); tmp['tau']=tau; tmp['score']=score
    for _ in range(B):
        pick=rng.choice(codes,size=len(codes),replace=True)
        chunks=[]
        for j,c in enumerate(pick):
            q=tmp[tmp.code==c].copy(); q['_boot']=j; chunks.append(q)
        b=pd.concat(chunks,ignore_index=True); n=max(1,int(np.ceil(k*len(b))))
        top=b.nlargest(n,'tau'); vals.append(top.score.mean()-b.score.mean())
    return np.quantile(vals,[.025,.975]).tolist()


def main():
    d,xcols,state_used=build_data()
    d.to_csv(OUT/f'analysis_panel_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # 1. rolling out-of-time validation
    folds=[(202509,[202510,202511]),(202511,[202512,202601]),(202601,[202602,202603]),(202603,[202604,202605])]
    time_rows=[]; all_test=[]
    for fi,(cut,months) in enumerate(folds,1):
        tr=d[d.ym<=cut].copy(); te=d[d.ym.isin(months)].copy()
        if len(tr)<300 or len(te)<50 or tr.T.sum()<20 or te.T.sum()<3: continue
        tau,_=fit_cf_predict(tr,te,xcols,100+fi,320); dr,e=dr_scores(tr,te,xcols,200+fi)
        rho=float(spearmanr(tau,dr,nan_policy='omit').statistic)
        rows,auuc,frac,cg=topk_metrics(tau,dr); k20=[r for r in rows if abs(r[0]-.2)<1e-9][0]
        q=np.quantile(tau,.8); trt=te[te.T==1].copy(); trt_tau=tau[te.T.values==1]
        desc=(float(trt.Y.values[trt_tau>=q].mean()-trt.Y.values[trt_tau<q].mean()) if np.any(trt_tau>=q) and np.any(trt_tau<q) else np.nan)
        time_rows.append([fi,cut,','.join(map(str,months)),len(tr),len(te),int(te.T.sum()),rho,k20[4],auuc,desc])
        z=te[['code','ym','T','Y']].copy(); z['tau']=tau; z['dr_score']=dr; z['fold']=fi; all_test.append(z)
    time_df=pd.DataFrame(time_rows,columns=['fold','train_through','test_months','n_train','n_test','n_treated_test','spearman_tau_dr','top20_dr_gain','auuc','treated_top20_Y_diff'])
    time_df.to_csv(OUT/f'time_validation_{STAMP}.csv',index=False,encoding='utf-8-sig')
    if all_test: pd.concat(all_test).to_csv(OUT/f'time_validation_predictions_{STAMP}.csv',index=False,encoding='utf-8-sig')

    # 2. 5-fold specification-block OOF Top-k ranking gain
    n=len(d); tau_oof=np.full(n,np.nan); dr_oof=np.full(n,np.nan)
    gkf=GroupKFold(n_splits=5)
    for fi,(tr_idx,te_idx) in enumerate(gkf.split(d,d.T,groups=d.code),1):
        tr=d.iloc[tr_idx]; te=d.iloc[te_idx]
        tau,_=fit_cf_predict(tr,te,xcols,300+fi,320); dr,_=dr_scores(tr,te,xcols,400+fi)
        tau_oof[te_idx]=tau; dr_oof[te_idx]=dr
    top_rows,auuc_oof,frac,cg=topk_metrics(tau_oof,dr_oof)
    top_df=pd.DataFrame(top_rows,columns=['top_fraction','n','mean_dr_top','mean_dr_all','dr_gain'])
    ci20=cluster_boot_gain(d,tau_oof,dr_oof,.2,400,555)
    top_df['gain_ci_low']=np.nan; top_df['gain_ci_high']=np.nan
    m=np.isclose(top_df.top_fraction,.2); top_df.loc[m,'gain_ci_low']=ci20[0]; top_df.loc[m,'gain_ci_high']=ci20[1]
    top_df['auuc']=auuc_oof; top_df.to_csv(OUT/f'topk_gain_{STAMP}.csv',index=False,encoding='utf-8-sig')
    oof=d[['code','ym','T','Y']].copy(); oof['tau_oof']=tau_oof; oof['dr_score_oof']=dr_oof; oof.to_csv(OUT/f'oof_predictions_{STAMP}.csv',index=False,encoding='utf-8-sig')

    # 3. random-seed stability (full-data ranking; model-internal randomness only)
    seeds=[11,23,37,51,67,79,97,113,131,149]; preds=[]
    for s in seeds:
        tau,_=fit_cf_predict(d,d,xcols,s,320); preds.append(tau)
    P=np.vstack(preds); cor=np.corrcoef(np.argsort(np.argsort(P,axis=1),axis=1))
    # pairwise Spearman and top20 Jaccard
    rhos=[]; jacs=[]
    sets=[]
    k=max(1,int(.2*n))
    for row in P: sets.append(set(np.argpartition(row,-k)[-k:]))
    for i in range(len(seeds)):
        for j in range(i+1,len(seeds)):
            rhos.append(spearmanr(P[i],P[j]).statistic); jacs.append(len(sets[i]&sets[j])/len(sets[i]|sets[j]))
    seed_summary=pd.DataFrame([{
        'n_seeds':len(seeds),'pairwise_spearman_median':np.median(rhos),'pairwise_spearman_min':np.min(rhos),
        'top20_jaccard_median':np.median(jacs),'top20_jaccard_min':np.min(jacs),
        'median_rowwise_cate_sd':np.median(P.std(axis=0)),'p90_rowwise_cate_sd':np.quantile(P.std(axis=0),.9)
    }])
    seed_summary.to_csv(OUT/f'seed_stability_{STAMP}.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(P.T,columns=[f'seed_{s}' for s in seeds]).assign(code=d.code.values,ym=d.ym.values).to_csv(OUT/f'seed_predictions_{STAMP}.csv',index=False,encoding='utf-8-sig')

    # 4. common-support-domain re-estimation
    prop_oof=np.full(n,np.nan)
    for tr_idx,te_idx in gkf.split(d,d.T,groups=d.code):
        m=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced'))
        m.fit(d.iloc[tr_idx][xcols],d.iloc[tr_idx].T); prop_oof[te_idx]=m.predict_proba(d.iloc[te_idx][xcols])[:,1]
    tmask=d.T.values==1; cmask=~tmask
    low=max(np.min(prop_oof[tmask]),np.min(prop_oof[cmask]),.05); high=min(np.max(prop_oof[tmask]),np.max(prop_oof[cmask]),.95)
    support=(prop_oof>=low)&(prop_oof<=high); ds=d[support].copy()
    tau_full,_=fit_cf_predict(d,d,xcols,777,500); tau_sup,_=fit_cf_predict(ds,ds,xcols,778,500)
    def cluster_ci(vals,codes,B=600,seed=9):
        rng=np.random.default_rng(seed); uc=np.array(pd.unique(codes)); by={c:np.asarray(vals)[np.asarray(codes)==c] for c in uc}; means=[]
        for _ in range(B):
            pick=rng.choice(uc,len(uc),replace=True); means.append(np.mean(np.concatenate([by[c] for c in pick])))
        return np.quantile(means,[.025,.975])
    ci_full=cluster_ci(tau_full,d.code.values); ci_sup=cluster_ci(tau_sup,ds.code.values)
    overlap=pd.DataFrame([
        ['full',len(d),int(d.T.sum()),1.0,float(np.mean(tau_full)),ci_full[0],ci_full[1],np.nan,np.nan],
        ['common_support',len(ds),int(ds.T.sum()),len(ds)/len(d),float(np.mean(tau_sup)),ci_sup[0],ci_sup[1],low,high]
    ],columns=['sample','n','n_treated','retained_share','mean_cate','ci_low','ci_high','propensity_low','propensity_high'])
    overlap.to_csv(OUT/f'overlap_reestimate_{STAMP}.csv',index=False,encoding='utf-8-sig')
    prop=pd.DataFrame({'code':d.code,'ym':d.ym,'T':d.T,'propensity_oof':prop_oof,'in_support':support}); prop.to_csv(OUT/f'propensity_support_{STAMP}.csv',index=False,encoding='utf-8-sig')

    # -------- figures --------
    plt.rcParams['font.sans-serif']=['DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
    # time validation
    if len(time_df):
        fig,ax=plt.subplots(figsize=(8.8,5.2)); x=np.arange(len(time_df)); ax.axhline(0,color='0.5',lw=1)
        ax.plot(x,time_df.top20_dr_gain,marker='o',lw=1.8,label='Top-20% DR gain'); ax.plot(x,time_df.spearman_tau_dr,marker='s',lw=1.5,label='Spearman(tau, DR)')
        ax.set_xticks(x,[f"F{int(v)}\n{m}" for v,m in zip(time_df.fold,time_df.test_months)]); ax.set_title('Out-of-time ranking validation'); ax.legend(frameon=False); ax.grid(alpha=.2)
        fig.tight_layout(); fig.savefig(FIG/f'fig6_time_validation_{STAMP}.svg'); plt.close(fig)
    # top-k cumulative gain
    fig,ax=plt.subplots(figsize=(8.8,5.2)); ax.plot(frac,cg,lw=2); ax.axhline(0,color='0.5',lw=1); ax.set_xlabel('Fraction reviewed (sorted by OOF CATE)'); ax.set_ylabel('Cumulative centered DR gain'); ax.set_title(f'OOF cumulative ranking gain (AUUC={auuc_oof:.3f})'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/f'fig7_topk_gain_{STAMP}.svg'); plt.close(fig)
    # seed stability heatmap
    R=np.ones((len(seeds),len(seeds)))
    for i in range(len(seeds)):
        for j in range(len(seeds)): R[i,j]=spearmanr(P[i],P[j]).statistic
    fig,ax=plt.subplots(figsize=(7.2,6.2)); im=ax.imshow(R,vmin=0,vmax=1,cmap='viridis'); ax.set_xticks(range(len(seeds)),seeds,rotation=45); ax.set_yticks(range(len(seeds)),seeds); ax.set_title('Random-seed ranking stability (Spearman)'); fig.colorbar(im,ax=ax,fraction=.046,pad=.04); fig.tight_layout(); fig.savefig(FIG/f'fig8_seed_stability_{STAMP}.svg'); plt.close(fig)
    # propensity overlap
    fig,ax=plt.subplots(figsize=(8.8,5.2)); bins=np.linspace(0,1,35); ax.hist(prop_oof[d.T.values==0],bins=bins,density=True,histtype='step',lw=1.8,label='Control'); ax.hist(prop_oof[d.T.values==1],bins=bins,density=True,histtype='step',lw=1.8,label='Treated'); ax.axvspan(low,high,alpha=.12,label='Common-support domain'); ax.set_xlabel('OOF propensity score'); ax.set_ylabel('Density'); ax.set_title('Propensity-score overlap and retained support domain'); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG/f'fig9_overlap_{STAMP}.svg'); plt.close(fig)
    # ATE comparison forest
    fig,ax=plt.subplots(figsize=(7.8,4.2)); yy=[1,0]
    for y0,row in zip(yy,overlap.itertuples()): ax.plot([row.ci_low,row.ci_high],[y0,y0],lw=2); ax.scatter([row.mean_cate],[y0],s=45)
    ax.axvline(0,color='0.5',ls='--'); ax.set_yticks(yy,['Full sample','Common support']); ax.set_xlabel('Mean CATE (cluster-bootstrap 95% CI)'); ax.set_title('Full-sample vs common-support re-estimation'); ax.grid(axis='x',alpha=.2); fig.tight_layout(); fig.savefig(FIG/f'fig10_overlap_reestimate_{STAMP}.svg'); plt.close(fig)

    summary={
        'timestamp':STAMP,'n':len(d),'n_specs':int(d.code.nunique()),'n_treated':int(d.T.sum()),'state_indicators':state_used,'n_x':len(xcols),
        'time_validation_folds':int(len(time_df)),
        'time_spearman_median':float(time_df.spearman_tau_dr.median()) if len(time_df) else None,
        'time_top20_gain_mean':float(time_df.top20_dr_gain.mean()) if len(time_df) else None,
        'oof_top20_gain':float(top_df.loc[np.isclose(top_df.top_fraction,.2),'dr_gain'].iloc[0]),
        'oof_top20_gain_ci':ci20,'oof_auuc':auuc_oof,
        'seed_spearman_median':float(seed_summary.pairwise_spearman_median.iloc[0]),'seed_top20_jaccard_median':float(seed_summary.top20_jaccard_median.iloc[0]),
        'support_retained_share':float(len(ds)/len(d)),'support_treated_retained_share':float(ds.T.sum()/max(1,d.T.sum())),
        'full_mean_cate':float(np.mean(tau_full)),'support_mean_cate':float(np.mean(tau_sup)),'support_mean_cate_ci':ci_sup.tolist(),
        'support_bounds':[float(low),float(high)]
    }
    (OUT/f'experiment_summary_{STAMP}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame([summary]).to_csv(OUT/f'experiment_summary_{STAMP}.csv',index=False,encoding='utf-8-sig')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
