# -*- coding: utf-8 -*-
"""Strict v2 hard experiments for v20.
Design: X_{t-1} -> proxy treatment T_t -> outcome Y=S_{t+1}-S_{t-1}.
State score excludes treatment-definition fields and uses price, margin, inventory, sales momentum.
"""
from pathlib import Path
import json, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from econml.dml import CausalForestDML
import matplotlib.pyplot as plt

STAMP='0916_0014'
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'v18'/'data'/'raw_panel_v1.csv'
OUT=ROOT/'v20'/'experiments'/STAMP; FIG=OUT/'figures'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)
STATE=[('price_index',1),('gross_margin',1),('inventory_ratio',-1),('unit_growth',1)]
X_BASE=['util','full_surf','price_index','gross_margin','unitval','inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','unit_growth','salable_days','purch_surf','rep_rate2']

def robust_score(s,direction=1):
    s=pd.to_numeric(s,errors='coerce'); lo,hi=s.quantile(.02),s.quantile(.98); z=s.clip(lo,hi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi-lo<1e-12: z=pd.Series(.5,index=s.index)
    else: z=(z-lo)/(hi-lo)
    return 1-z if direction<0 else z

def build_data():
    p=pd.read_csv(RAW,encoding='utf-8-sig',low_memory=False); p['ym']=p['ym'].astype(int); p=p.sort_values(['code','ym']).reset_index(drop=True)
    used=[]; zcols=[]
    for c,direction in STATE:
        if c in p and p[c].notna().mean()>=.35 and p[c].nunique(dropna=True)>1:
            z='_z_'+c; p[z]=robust_score(p[c],direction); used.append(c); zcols.append(z)
    if len(used)<4: raise RuntimeError(f'Expected four state indicators, got {used}')
    p['_state_n']=p[zcols].notna().sum(axis=1); p['S']=p[zcols].mean(axis=1)*100; p.loc[p['_state_n']<3,'S']=np.nan
    p['L1_S']=p.groupby('code')['S'].shift(1); p['S_next']=p.groupby('code')['S'].shift(-1); p['Y']=p['S_next']-p['L1_S']
    # proxy event: true monthly cross-section P35, plus >2 percentage-point drop from previous month
    q35=p.groupby('ym')['fill'].transform(lambda x:x.quantile(.35)); fill_prev=p.groupby('code')['fill'].shift(1)
    valid=p['fill'].notna()&fill_prev.notna(); cond=(p['fill']<=q35)&((fill_prev-p['fill'])>2.0)
    p['T']=np.where(valid,cond.astype(int),np.nan)
    xcols=[]
    for c in X_BASE:
        if c in p and p[c].notna().mean()>=.25 and p[c].nunique(dropna=True)>1:
            lc='L1_'+c; p[lc]=p.groupby('code')[c].shift(1); xcols.append(lc)
    xcols.append('L1_S')
    # static and treatment-month seasonality dummies
    p['month_of_year']=p['ym']%100
    for c in ['cat','price_band_cat','month_of_year']:
        if c in p:
            dd=pd.get_dummies(p[c],prefix=c,dtype=int); p=pd.concat([p,dd],axis=1); xcols += list(dd.columns)
    keep=['code','ym','name','cat','T','Y','S','L1_S','fill']+list(dict.fromkeys(xcols))
    d=p[keep].dropna(subset=['T','Y']).copy(); yl,yh=d['Y'].quantile([.01,.99]); d=d[d['Y'].between(yl,yh)].reset_index(drop=True)
    return d,list(dict.fromkeys(xcols)),used

def matrices(train,test,xcols):
    a=train[xcols].apply(pd.to_numeric,errors='coerce'); b=test[xcols].apply(pd.to_numeric,errors='coerce')
    med=a.median().replace([np.inf,-np.inf],np.nan).fillna(0); return a.fillna(med).values,b.fillna(med).values

def cf(seed=42,n_estimators=320):
    return CausalForestDML(model_y=RandomForestRegressor(n_estimators=140,min_samples_leaf=12,max_features=.8,n_jobs=-1,random_state=seed),model_t=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced',random_state=seed)),discrete_treatment=True,n_estimators=n_estimators,min_samples_leaf=15,max_depth=12,max_samples=.45,honest=True,cv=3,random_state=seed,n_jobs=-1,inference=False)

def fit_tau(train,test,xcols,seed=42,n_estimators=320):
    Xtr,Xte=matrices(train,test,xcols); m=cf(seed,n_estimators); m.fit(train['Y'].values,T=train['T'].astype(int).values,X=Xtr); return np.asarray(m.effect(Xte)).reshape(-1)

def dr_score(train,test,xcols,seed=42):
    Xtr,Xte=matrices(train,test,xcols); ttr=train['T'].astype(int).values; ytr=train['Y'].values; t=test['T'].astype(int).values; y=test['Y'].values
    prop=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced',random_state=seed)); prop.fit(Xtr,ttr); e=np.clip(prop.predict_proba(Xte)[:,1],.03,.97)
    m0=RandomForestRegressor(n_estimators=180,min_samples_leaf=10,max_features=.8,n_jobs=-1,random_state=seed); m1=RandomForestRegressor(n_estimators=180,min_samples_leaf=8,max_features=.8,n_jobs=-1,random_state=seed+1)
    m0.fit(Xtr[ttr==0],ytr[ttr==0]); m1.fit(Xtr[ttr==1],ytr[ttr==1]); mu0=m0.predict(Xte); mu1=m1.predict(Xte)
    return (mu1-mu0)+t*(y-mu1)/e-(1-t)*(y-mu0)/(1-e),e

def topk(tau,score,ks=(.1,.2,.3)):
    order=np.argsort(-tau); base=float(np.mean(score)); rows=[]
    for k in ks:
        n=max(1,int(np.ceil(k*len(order)))); v=float(np.mean(score[order[:n]])); rows.append([k,n,v,base,v-base])
    cg=np.cumsum((score-base)[order])/len(order); frac=np.arange(1,len(order)+1)/len(order); auuc=float(np.trapezoid(cg,frac)); return rows,auuc,frac,cg

def cluster_ci(values,codes,B=500,seed=123):
    values=np.asarray(values); codes=np.asarray(codes); uc=np.unique(codes); rng=np.random.default_rng(seed); groups={c:values[codes==c] for c in uc}; z=[]
    for _ in range(B): z.append(np.mean(np.concatenate([groups[c] for c in rng.choice(uc,len(uc),replace=True)])))
    return np.quantile(z,[.025,.975])

def cluster_gain_ci(df,tau,score,k=.2,B=400):
    rng=np.random.default_rng(456); codes=np.array(df.code.unique()); tmp=df[['code']].copy(); tmp['tau']=tau; tmp['score']=score; z=[]
    for _ in range(B):
        chunks=[]
        for j,c in enumerate(rng.choice(codes,len(codes),replace=True)):
            q=tmp[tmp.code==c].copy(); q['_b']=j; chunks.append(q)
        b=pd.concat(chunks,ignore_index=True); n=max(1,int(np.ceil(k*len(b)))); z.append(b.nlargest(n,'tau').score.mean()-b.score.mean())
    return np.quantile(z,[.025,.975])

def main():
    d,xcols,state_used=build_data(); d.to_csv(OUT/f'analysis_panel_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # 1 rolling out-of-time
    folds=[(202509,[202510,202511]),(202511,[202512,202601]),(202601,[202602,202603]),(202603,[202604,202605])]; time=[]; time_preds=[]
    for fi,(cut,months) in enumerate(folds,1):
        tr=d[d.ym<=cut]; te=d[d.ym.isin(months)]
        if len(tr)<300 or len(te)<50 or tr['T'].sum()<20 or te['T'].sum()<3: continue
        tau=fit_tau(tr,te,xcols,100+fi); dr,_=dr_score(tr,te,xcols,200+fi); rows,auuc,_,_=topk(tau,dr); k20=rows[1]
        rho=float(spearmanr(tau,dr).statistic); time.append([fi,cut,'/'.join(map(str,months)),len(tr),len(te),int(te['T'].sum()),rho,k20[4],auuc])
        z=te[['code','ym','T','Y']].copy(); z['tau']=tau; z['dr']=dr; z['fold']=fi; time_preds.append(z)
    time_df=pd.DataFrame(time,columns=['fold','train_through','test_months','n_train','n_test','n_treated_test','spearman_tau_dr','top20_dr_gain','auuc']); time_df.to_csv(OUT/f'time_validation_{STAMP}.csv',index=False,encoding='utf-8-sig'); pd.concat(time_preds).to_csv(OUT/f'time_predictions_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # 2 specification-block OOF
    n=len(d); tau=np.full(n,np.nan); dr=np.full(n,np.nan); gkf=GroupKFold(5)
    for fi,(a,b) in enumerate(gkf.split(d,d['T'],groups=d.code),1):
        tau[b]=fit_tau(d.iloc[a],d.iloc[b],xcols,300+fi); dr[b]=dr_score(d.iloc[a],d.iloc[b],xcols,400+fi)[0]
    rows,auuc,frac,cg=topk(tau,dr); top=pd.DataFrame(rows,columns=['top_fraction','n','mean_dr_top','mean_dr_all','dr_gain']); ci=cluster_gain_ci(d,tau,dr,.2); top['ci_low']=np.nan; top['ci_high']=np.nan; top.loc[np.isclose(top.top_fraction,.2),['ci_low','ci_high']]=ci; top['auuc']=auuc
    # simple ranking baselines at top20
    baselines=[]
    for label,col in [('Causal forest','_tau'),('Pre-state S','L1_S'),('Inventory pressure','L1_inventory_ratio')]:
        rank=tau if col=='_tau' else pd.to_numeric(d[col],errors='coerce').fillna(pd.to_numeric(d[col],errors='coerce').median()).values
        r=topk(rank,dr,ks=(.2,))[0][0]; baselines.append([label,r[2],r[3],r[4]])
    pd.DataFrame(baselines,columns=['ranking','mean_dr_top20','mean_dr_all','top20_gain']).to_csv(OUT/f'baseline_comparison_{STAMP}.csv',index=False,encoding='utf-8-sig'); top.to_csv(OUT/f'topk_gain_{STAMP}.csv',index=False,encoding='utf-8-sig')
    oof=d[['code','ym','T','Y']].copy(); oof['tau_oof']=tau; oof['dr_oof']=dr; oof.to_csv(OUT/f'oof_predictions_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # 3 seed stability, same fixed sample
    seeds=[11,23,37,51,67,79,97,113,131,149]; P=np.vstack([fit_tau(d,d,xcols,s,300) for s in seeds]); rhos=[]; jacs=[]; k=max(1,int(.2*n)); sets=[set(np.argpartition(row,-k)[-k:]) for row in P]
    for i in range(len(seeds)):
        for j in range(i+1,len(seeds)): rhos.append(spearmanr(P[i],P[j]).statistic); jacs.append(len(sets[i]&sets[j])/len(sets[i]|sets[j]))
    seed=pd.DataFrame([{'n_seeds':10,'spearman_median':np.median(rhos),'spearman_min':np.min(rhos),'top20_jaccard_median':np.median(jacs),'top20_jaccard_min':np.min(jacs),'median_cate_sd':np.median(P.std(0)),'p90_cate_sd':np.quantile(P.std(0),.9)}]); seed.to_csv(OUT/f'seed_stability_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # 4 common support: OOF propensity, then re-run full OOF inside retained domain
    prop=np.full(n,np.nan)
    for a,b in gkf.split(d,d['T'],groups=d.code):
        Xtr,Xte=matrices(d.iloc[a],d.iloc[b],xcols); m=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,class_weight='balanced')); m.fit(Xtr,d.iloc[a]['T'].astype(int)); prop[b]=m.predict_proba(Xte)[:,1]
    tm=d['T'].values==1; cm=~tm; lo=max(prop[tm].min(),prop[cm].min(),.05); hi=min(prop[tm].max(),prop[cm].max(),.95); mask=(prop>=lo)&(prop<=hi); ds=d[mask].reset_index(drop=True)
    def oof_on(sample):
        N=len(sample); tt=np.full(N,np.nan); rr=np.full(N,np.nan); gg=GroupKFold(5)
        for fi,(a,b) in enumerate(gg.split(sample,sample['T'],groups=sample.code),1): tt[b]=fit_tau(sample.iloc[a],sample.iloc[b],xcols,700+fi); rr[b]=dr_score(sample.iloc[a],sample.iloc[b],xcols,800+fi)[0]
        return tt,rr
    ts,rs=oof_on(ds); full_ate=float(np.mean(dr)); sup_ate=float(np.mean(rs)); cif=cluster_ci(dr,d.code); cis=cluster_ci(rs,ds.code)
    overlap=pd.DataFrame([['full',len(d),int(d['T'].sum()),1.0,full_ate,cif[0],cif[1],float(np.mean(tau))],np.nan,np.nan],['common_support',len(ds),int(ds['T'].sum()),len(ds)/len(d),sup_ate,cis[0],cis[1],float(np.mean(ts)),lo,hi]],columns=['sample','n','n_treated','retained_share','dr_ate','ci_low','ci_high','mean_oof_cate','prop_low','prop_high']); overlap.to_csv(OUT/f'overlap_reestimate_{STAMP}.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'code':d.code,'ym':d.ym,'T':d.T,'propensity':prop,'in_support':mask}).to_csv(OUT/f'propensity_support_{STAMP}.csv',index=False,encoding='utf-8-sig')
    # figures
    plt.rcParams['axes.unicode_minus']=False
    fig,ax=plt.subplots(figsize=(8.8,5.2)); xx=np.arange(len(time_df)); ax.axhline(0,lw=1); ax.plot(xx,time_df.top20_dr_gain,marker='o'); ax.set_xticks(xx,[f"F{int(r.fold)}\n{r.test_months}" for r in time_df.itertuples()]); [ax.text(i,v,f"rho={time_df.iloc[i].spearman_tau_dr:.2f}",ha='center',va='bottom',fontsize=8) for i,v in enumerate(time_df.top20_dr_gain)]; ax.set_ylabel('Top-20% DR gain'); ax.set_title('Rolling out-of-time ranking validation'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/f'fig6_time_validation_{STAMP}.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.8,5.2)); ax.plot(frac,cg,label='Causal forest'); ax.axhline(0,lw=1); ax.set_xlabel('Fraction reviewed'); ax.set_ylabel('Cumulative centered DR gain'); ax.set_title(f'OOF cumulative ranking gain (AUUC={auuc:.3f})'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/f'fig7_topk_gain_{STAMP}.svg'); plt.close(fig)
    R=np.array([[spearmanr(P[i],P[j]).statistic for j in range(len(seeds))] for i in range(len(seeds))]); fig,ax=plt.subplots(figsize=(7,6)); im=ax.imshow(R,vmin=0,vmax=1); ax.set_xticks(range(10),seeds,rotation=45); ax.set_yticks(range(10),seeds); ax.set_title('Seed stability of CATE ranking'); fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(FIG/f'fig8_seed_stability_{STAMP}.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.8,5.2)); bins=np.linspace(0,1,35); ax.hist(prop[d['T'].values==0],bins=bins,density=True,histtype='step',label='Control'); ax.hist(prop[d['T'].values==1],bins=bins,density=True,histtype='step',label='Treated'); ax.axvspan(lo,hi,alpha=.12,label='Common support'); ax.set_xlabel('OOF propensity score'); ax.set_ylabel('Density'); ax.set_title('Propensity overlap'); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG/f'fig9_overlap_{STAMP}.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.8,4.2)); yy=[1,0]; vals=[(full_ate,cif[0],cif[1]),(sup_ate,cis[0],cis[1])];
    for y0,(e,l,h) in zip(yy,vals): ax.plot([l,h],[y0,y0],lw=2); ax.scatter([e],[y0],s=45)
    ax.axvline(0,ls='--',lw=1); ax.set_yticks(yy,['Full sample','Common support']); ax.set_xlabel('DR ATE (cluster-bootstrap 95% interval)'); ax.set_title('Common-support re-estimation'); ax.grid(axis='x',alpha=.2); fig.tight_layout(); fig.savefig(FIG/f'fig10_overlap_reestimate_{STAMP}.svg'); plt.close(fig)
    summary={'timestamp':STAMP,'n':len(d),'n_specs':int(d.code.nunique()),'n_treated':int(d['T'].sum()),'state_indicators':state_used,'n_x':len(xcols),'time_folds':len(time_df),'time_spearman_median':float(time_df.spearman_tau_dr.median()),'time_top20_gain_mean':float(time_df.top20_dr_gain.mean()),'oof_top20_gain':float(top.loc[np.isclose(top.top_fraction,.2),'dr_gain'].iloc[0]),'oof_top20_gain_ci':ci.tolist(),'oof_auuc':auuc,'seed_spearman_median':float(seed.spearman_median.iloc[0]),'seed_top20_jaccard_median':float(seed.top20_jaccard_median.iloc[0]),'support_retained_share':float(len(ds)/len(d)),'treated_retained_share':float(ds['T'].sum()/d['T'].sum()),'full_dr_ate':full_ate,'full_dr_ate_ci':cif.tolist(),'support_dr_ate':sup_ate,'support_dr_ate_ci':cis.tolist(),'support_bounds':[float(lo),float(hi)]}
    (OUT/f'experiment_summary_{STAMP}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); pd.DataFrame([summary]).to_csv(OUT/f'experiment_summary_{STAMP}.csv',index=False,encoding='utf-8-sig'); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
