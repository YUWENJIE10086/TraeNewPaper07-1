# -*- coding: utf-8 -*-
"""
v20-7 四项硬实验（真实仓库面板重算）
1) 滚动时间外验证
2) Top-k 排序增益
3) 随机种子稳定性
4) 共同支持域内 AIPW 重估

数据：Papers2/v18/data/causal_forest_panel_v1.csv
关键设计：对动态经营协变量统一使用 t-1 期值；T 使用 t 期既有代理事件；Y 使用既有下一期状态变化。
输出：Papers2/v20/experiments/0916_0811/
"""
from pathlib import Path
import json, math, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

warnings.filterwarnings('ignore')
STAMP='0916_0811'
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'Papers2'/'v18'/'data'/'causal_forest_panel_v1.csv'
OUT=ROOT/'Papers2'/'v20'/'experiments'/STAMP
FIG=OUT/'figures'
OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(parents=True,exist_ok=True)

BASE_REG=dict(objective='regression',n_estimators=180,learning_rate=0.05,num_leaves=20,
              min_child_samples=25,subsample=0.85,colsample_bytree=0.85,verbose=-1,n_jobs=2)
BASE_CLF=dict(objective='binary',n_estimators=180,learning_rate=0.05,num_leaves=20,
              min_child_samples=25,subsample=0.85,colsample_bytree=0.85,verbose=-1,n_jobs=2)

DYN=['util','fill','full_surf','ord_success','price_index','gross_margin','unitval',
     'inventory_ratio','channel_coverage','demand_gap','amt_per_cust','new_cust','S']


def group_folds(groups,n_splits=5,seed=42):
    uniq=np.array(pd.unique(groups)); rng=np.random.RandomState(seed); rng.shuffle(uniq)
    buckets=np.array_split(uniq,n_splits)
    folds=[]
    g=np.asarray(groups)
    for b in buckets:
        va=np.flatnonzero(np.isin(g,b)); tr=np.flatnonzero(~np.isin(g,b)); folds.append((tr,va))
    return folds


def prepare():
    d=pd.read_csv(DATA,encoding='utf-8-sig').sort_values(['code','ym']).reset_index(drop=True)
    # 静态结构哑变量直接使用；动态经营画像全部滞后一期，避免同期期后信息进入排序。
    static=[c for c in d.columns if c.startswith('cat_') or c.startswith('band_')]
    lag_cols=[]
    for c in DYN:
        if c in d.columns:
            lc='lag_'+c; d[lc]=d.groupby('code')[c].shift(1); lag_cols.append(lc)
    feats=lag_cols+static
    keep=['code','ym','T','Y']+feats
    x=d[keep].copy().dropna(subset=['T','Y'])
    for c in feats:
        if x[c].isna().mean()>0.45:
            continue
        x[c]=x[c].fillna(x[c].median())
    feats=[c for c in feats if c in x.columns and x[c].notna().mean()>=0.55 and x[c].nunique()>1]
    x=x[['code','ym','T','Y']+feats].dropna().copy()
    # 保持与原v18稳健处理一致：Y 1%-99%缩尾区间内，库存极端1%剔除。
    ylo,yhi=np.percentile(x['Y'],[1,99]); x=x[x['Y'].between(ylo,yhi)].copy()
    if 'lag_inventory_ratio' in x.columns:
        cap=np.percentile(x['lag_inventory_ratio'],99); x=x[x['lag_inventory_ratio']<cap].copy()
    x['ym']=x['ym'].astype(int); x['T']=x['T'].astype(int)
    return x.reset_index(drop=True),feats


def fit_rlearner(train,feats,seed=42):
    X=train[feats].to_numpy(float); T=train.T.to_numpy() if False else train['T'].to_numpy(float); Y=train['Y'].to_numpy(float)
    n=len(train); mu=np.full(n,np.nan); ep=np.full(n,np.nan)
    for tr,va in group_folds(train['code'].values,5,seed):
        ry=lgb.LGBMRegressor(**BASE_REG,random_state=seed); ry.fit(X[tr],Y[tr]); mu[va]=ry.predict(X[va])
        cl=lgb.LGBMClassifier(**BASE_CLF,random_state=seed); cl.fit(X[tr],T[tr].astype(int)); ep[va]=cl.predict_proba(X[va])[:,1]
    ep=np.clip(ep,0.01,0.99); yt=Y-mu; tt=T-ep
    rho=yt/np.where(np.abs(tt)<1e-4,np.sign(tt)*1e-4+1e-4,tt)
    lo,hi=np.percentile(rho,[3,97]); rho=np.clip(rho,lo,hi); w=tt**2
    mod=lgb.LGBMRegressor(**BASE_REG,random_state=seed); mod.fit(X,rho,sample_weight=w)
    return mod


def rolling_oot(d,feats):
    months=sorted(d['ym'].unique())
    rows=[]; preds=[]
    for m in months:
        train=d[d.ym<m]; test=d[d.ym==m]
        if train.ym.nunique()<8 or train['T'].sum()<25 or test['T'].sum()<3: continue
        mod=fit_rlearner(train,feats,42); tau=np.clip(mod.predict(test[feats].to_numpy(float)),-25,25)
        z=test[['code','ym','T','Y']].copy(); z['tau_oot']=tau
        if 'lag_S' in test: z['lag_S']=test['lag_S'].values
        if 'lag_inventory_ratio' in test: z['lag_inventory_ratio']=test['lag_inventory_ratio'].values
        preds.append(z)
        tr=z[z.T.eq(1)] if False else z[z['T']==1]
        n=len(tr); k=max(1,int(math.ceil(.30*n))); top=tr.nlargest(k,'tau_oot'); rest=tr.drop(top.index)
        rows.append({'ym':m,'n_train':len(train),'n_test':len(test),'n_treat_test':n,
                     'top30_n':len(top),'top30_mean_Y':top.Y.mean(),
                     'rest_mean_Y':rest.Y.mean() if len(rest) else np.nan,
                     'lift_top30':top.Y.mean()-(rest.Y.mean() if len(rest) else np.nan),
                     'top30_improve_rate':(top.Y>0).mean(),
                     'rest_improve_rate':(rest.Y>0).mean() if len(rest) else np.nan})
    monthly=pd.DataFrame(rows); p=pd.concat(preds,ignore_index=True) if preds else pd.DataFrame()
    monthly.to_csv(OUT/'time_out_monthly.csv',index=False,encoding='utf-8-sig'); p.to_csv(OUT/'time_out_predictions.csv',index=False,encoding='utf-8-sig')
    return monthly,p


def topk(p):
    tr=p[p['T']==1].copy(); base=tr.Y.mean(); rows=[]
    for pct in [10,20,30,40,50]:
        n=max(3,int(math.ceil(len(tr)*pct/100)))
        model=tr.nlargest(n,'tau_oot')
        rec={'top_pct':pct,'n':n,'all_treated_mean_Y':base,'model_mean_Y':model.Y.mean(),
             'model_gain_vs_all':model.Y.mean()-base,'model_improve_rate':(model.Y>0).mean()}
        if 'lag_S' in tr:
            b=tr.nlargest(n,'lag_S'); rec['state_baseline_mean_Y']=b.Y.mean(); rec['gain_vs_state']=model.Y.mean()-b.Y.mean()
        if 'lag_inventory_ratio' in tr:
            b=tr.nlargest(n,'lag_inventory_ratio'); rec['inventory_baseline_mean_Y']=b.Y.mean(); rec['gain_vs_inventory']=model.Y.mean()-b.Y.mean()
        rows.append(rec)
    out=pd.DataFrame(rows); out.to_csv(OUT/'topk_gain.csv',index=False,encoding='utf-8-sig'); return out


def seed_stability(d,feats,nseeds=20):
    taus=[]; seeds=list(range(101,101+nseeds))
    X=d[feats].to_numpy(float)
    for s in seeds:
        mod=fit_rlearner(d,feats,s); taus.append(np.clip(mod.predict(X),-25,25))
    ref=taus[0]; n20=max(1,int(math.ceil(.20*len(d)))); ref_idx=set(np.argsort(ref)[-n20:])
    rows=[]
    for s,t in zip(seeds,taus):
        rho=spearmanr(ref,t).statistic; idx=set(np.argsort(t)[-n20:]); ov=len(ref_idx&idx)/n20
        rows.append({'seed':s,'spearman_vs_seed101':rho,'top20_overlap_vs_seed101':ov,'cate_mean':np.mean(t),'cate_sd':np.std(t)})
    stab=pd.DataFrame(rows); stab.to_csv(OUT/'seed_stability.csv',index=False,encoding='utf-8-sig')
    # consensus diagnostics across seeds
    A=np.vstack(taus); mean_tau=A.mean(axis=0); sd_tau=A.std(axis=0)
    cons=d[['code','ym','T','Y']].copy(); cons['tau_seed_mean']=mean_tau; cons['tau_seed_sd']=sd_tau
    cons.to_csv(OUT/'seed_consensus_predictions.csv',index=False,encoding='utf-8-sig')
    return stab


def aipw_overlap(d,feats,seed=42):
    X=d[feats].to_numpy(float); T=d['T'].to_numpy(int); Y=d['Y'].to_numpy(float); n=len(d)
    e=np.full(n,np.nan); m1=np.full(n,np.nan); m0=np.full(n,np.nan)
    for tr,va in group_folds(d['code'].values,5,seed):
        cl=lgb.LGBMClassifier(**BASE_CLF,random_state=seed); cl.fit(X[tr],T[tr]); e[va]=cl.predict_proba(X[va])[:,1]
        tr1=tr[T[tr]==1]; tr0=tr[T[tr]==0]
        r1=lgb.LGBMRegressor(**BASE_REG,random_state=seed); r0=lgb.LGBMRegressor(**BASE_REG,random_state=seed)
        r1.fit(X[tr1],Y[tr1]); r0.fit(X[tr0],Y[tr0]); m1[va]=r1.predict(X[va]); m0[va]=r0.predict(X[va])
    e=np.clip(e,.02,.98)
    lo=max(e[T==1].min(),e[T==0].min()); hi=min(e[T==1].max(),e[T==0].max())
    support=(e>=lo)&(e<=hi)
    def calc(mask,label):
        ee=e[mask]; tt=T[mask]; yy=Y[mask]; a=m1[mask]; b=m0[mask]
        psi=(a-b)+tt*(yy-a)/ee-(1-tt)*(yy-b)/(1-ee)
        ate=float(np.mean(psi)); se=float(np.std(psi,ddof=1)/np.sqrt(len(psi)))
        return {'sample':label,'n':int(mask.sum()),'n_treat':int(tt.sum()),'ate_aipw':ate,'se':se,'ci_low':ate-1.96*se,'ci_high':ate+1.96*se}
    rows=[calc(np.ones(n,dtype=bool),'full'),calc(support,'common_support')]
    res=pd.DataFrame(rows); res['support_lo']=lo; res['support_hi']=hi
    res['treated_outside_support_pct']=100*(~support & (T==1)).sum()/max(1,(T==1).sum())
    res.to_csv(OUT/'overlap_reestimate.csv',index=False,encoding='utf-8-sig')
    pp=d[['code','ym','T','Y']].copy(); pp['propensity_oof']=e; pp['in_common_support']=support.astype(int)
    pp.to_csv(OUT/'overlap_propensity.csv',index=False,encoding='utf-8-sig')
    return res,pp


def figures(monthly,tk,stab,ov,pp):
    plt.rcParams['font.family']='DejaVu Sans'; plt.rcParams['axes.unicode_minus']=False; plt.rcParams['svg.fonttype']='none'
    # A rolling out-of-time lift
    fig,ax=plt.subplots(figsize=(8.8,4.8)); ax.axhline(0,lw=1,ls='--'); ax.plot(monthly['ym'].astype(str),monthly['lift_top30'],marker='o'); ax.set_ylabel('Top-30% Y lift vs remaining treated'); ax.set_xlabel('Test month'); ax.tick_params(axis='x',rotation=45); ax.set_title('Rolling out-of-time ranking lift'); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figA_time_out_lift.svg'); plt.close(fig)
    # B top-k gain
    fig,ax=plt.subplots(figsize=(7.8,4.7)); ax.plot(tk.top_pct,tk.model_gain_vs_all,marker='o',label='Model vs all treated');
    if 'gain_vs_state' in tk: ax.plot(tk.top_pct,tk.gain_vs_state,marker='s',label='Model vs state-score baseline')
    ax.axhline(0,lw=1,ls='--'); ax.set_xlabel('Top-k fraction (%)'); ax.set_ylabel('Mean next-period Y gain'); ax.set_title('Out-of-time Top-k ranking gain'); ax.legend(frameon=False); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figB_topk_gain.svg'); plt.close(fig)
    # C seed stability
    fig,ax=plt.subplots(figsize=(7.8,4.7)); ax.scatter(stab.spearman_vs_seed101,stab.top20_overlap_vs_seed101,s=45); ax.set_xlabel('Spearman correlation vs seed 101'); ax.set_ylabel('Top-20% overlap vs seed 101'); ax.set_title('Ranking stability across random seeds'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIG/'figC_seed_stability.svg'); plt.close(fig)
    # D propensity overlap
    fig,ax=plt.subplots(figsize=(8.2,4.7)); bins=np.linspace(pp.propensity_oof.min(),pp.propensity_oof.max(),28); ax.hist(pp.loc[pp.T==0,'propensity_oof'],bins=bins,density=True,histtype='step',lw=1.8,label='Control'); ax.hist(pp.loc[pp.T==1,'propensity_oof'],bins=bins,density=True,histtype='step',lw=1.8,label='Treated'); lo=float(ov.support_lo.iloc[0]); hi=float(ov.support_hi.iloc[0]); ax.axvline(lo,ls='--',lw=1); ax.axvline(hi,ls='--',lw=1); ax.set_xlabel('OOF propensity score'); ax.set_ylabel('Density'); ax.set_title('Common-support diagnostics'); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG/'figD_overlap_propensity.svg'); plt.close(fig)


def report(d,feats,monthly,p,tk,stab,ov):
    s={
      'analysis_n':int(len(d)),'analysis_specs':int(d.code.nunique()),'analysis_months':int(d.ym.nunique()),'analysis_treated':int(d.T.sum()),
      'oot_months':int(len(monthly)),'oot_treated_n':int((p.T==1).sum()),
      'oot_lift_top30_mean':float(monthly.lift_top30.mean()),'oot_lift_top30_median':float(monthly.lift_top30.median()),
      'top20_gain_vs_all':float(tk.loc[tk.top_pct==20,'model_gain_vs_all'].iloc[0]),
      'top20_gain_vs_state':float(tk.loc[tk.top_pct==20,'gain_vs_state'].iloc[0]) if 'gain_vs_state' in tk else None,
      'seed_spearman_median':float(stab.loc[stab.seed!=101,'spearman_vs_seed101'].median()),
      'seed_top20_overlap_median':float(stab.loc[stab.seed!=101,'top20_overlap_vs_seed101'].median()),
      'support_ate':float(ov.loc[ov['sample']=='common_support','ate_aipw'].iloc[0]),
      'support_ci_low':float(ov.loc[ov['sample']=='common_support','ci_low'].iloc[0]),
      'support_ci_high':float(ov.loc[ov['sample']=='common_support','ci_high'].iloc[0]),
      'treated_outside_support_pct':float(ov.treated_outside_support_pct.iloc[0])
    }
    (OUT/'hard_experiments_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    def f(v): return 'NA' if v is None or (isinstance(v,float) and np.isnan(v)) else f'{v:.3f}'
    html=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>v20-7四项硬实验</title><style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.7;max-width:1100px;margin:30px auto;padding:0 24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:8px}}th{{background:#f3f3f3}}img{{max-width:100%}}.box{{border-left:4px solid #333;padding:10px 14px;background:#f7f7f7}}</style></head><body>
<h1>v20-7 四项硬实验重算报告（0916_0811）</h1><div class="box">数据直接读取仓库 v18 因果森林面板；动态经营画像统一改为 t−1 期，避免同期期后信息进入排序。</div>
<h2>1 滚动时间外验证</h2><p>分析子样本 n={s['analysis_n']}，覆盖{s['analysis_specs']}个品规；可形成{s['oot_months']}个月度时间外测试窗，时间外处理观测{s['oot_treated_n']}条。Top-30%排序相对其余处理对象的下一期状态变化月均提升为 {f(s['oot_lift_top30_mean'])}，月度中位提升为 {f(s['oot_lift_top30_median'])}。</p><img src="figures/figA_time_out_lift.svg">
<h2>2 Top-k排序增益</h2><p>严格时间外预测汇总后，Top-20%模型排序相对全部处理对象的平均下一期状态变化增益为 {f(s['top20_gain_vs_all'])}；相对仅按处理前状态评分排序的增益为 {f(s['top20_gain_vs_state'])}。</p><img src="figures/figB_topk_gain.svg">{tk.to_html(index=False,float_format=lambda x:f'{x:.3f}')}
<h2>3 随机种子稳定性</h2><p>20个随机种子重复估计中，相对seed=101的CATE排序Spearman相关系数中位数为 {f(s['seed_spearman_median'])}，Top-20%对象重合率中位数为 {f(s['seed_top20_overlap_median'])}。</p><img src="figures/figC_seed_stability.svg">
<h2>4 共同支持域内重估</h2><p>OOF倾向得分共同支持域外的处理样本占比为 {f(s['treated_outside_support_pct'])}%。在共同支持域内采用交叉拟合AIPW重估，总体平均效应为 {f(s['support_ate'])}，95% CI [{f(s['support_ci_low'])}, {f(s['support_ci_high'])}]。</p><img src="figures/figD_overlap_propensity.svg">{ov.to_html(index=False,float_format=lambda x:f'{x:.3f}')}
<h2>5 解释边界</h2><p>时间外排序增益回答“模型能否在未来月份把更值得复核的对象排到前面”；随机种子实验回答“排序是否依赖偶然初始化”；共同支持域重估回答“剔除明显外推后总体效应是否改变”。它们均不把代理事件等同于真实审批减量动作。</p></body></html>'''
    (OUT/'hard_experiments_report.html').write_text(html,encoding='utf-8')
    return s


def main():
    d,feats=prepare(); print('analysis',len(d),'features',len(feats),'treated',d.T.sum())
    monthly,p=rolling_oot(d,feats); tk=topk(p); stab=seed_stability(d,feats,20); ov,pp=aipw_overlap(d,feats,42); figures(monthly,tk,stab,ov,pp); s=report(d,feats,monthly,p,tk,stab,ov); print(json.dumps(s,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
