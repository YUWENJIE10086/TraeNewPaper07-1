# -*- coding: utf-8 -*-
from pathlib import Path
import shutil
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'Papers2'/'v20'/'experiments'/'0916_0827'
OUT=ROOT/'Papers2'/'v20'/'experiments'/'0916_0831'; FIG=OUT/'figures'; OUT.mkdir(parents=True,exist_ok=True); FIG.mkdir(exist_ok=True)
mon=pd.read_csv(SRC/'oot_dr_monthly.csv'); topk=pd.read_csv(SRC/'topk_dr_gain.csv'); seeds=pd.read_csv(SRC/'seed_stability.csv'); eff=pd.read_csv(SRC/'aipw_and_negative_control.csv'); cases=pd.read_csv(SRC/'representative_cases_final.csv')
plt.rcParams['font.family']='DejaVu Sans'; plt.rcParams['axes.unicode_minus']=False; plt.rcParams['svg.fonttype']='none'
def save(fig,n): fig.savefig(FIG/n,format='svg',bbox_inches='tight'); plt.close(fig)
# Fig1
fig,ax=plt.subplots(figsize=(11.5,4.8));ax.set_axis_off();nodes=[('Raw panel','3149 rows'),('Independent S*','price/margin/inventory/sell-through'),('Proxy T','YM P35 + >2pp drop'),('Lagged X','t-1 operating profile'),('R-learner','group cross-fitting'),('Hard validation','OOT-DR / Top-k / seed / support'),('Manual review','no auto volume')];xs=np.linspace(.07,.93,len(nodes))
for i,(a,b) in enumerate(nodes):
 ax.text(xs[i],.62,a,ha='center',fontsize=11,fontweight='bold',bbox=dict(boxstyle='round,pad=.4',fc='white',ec='black'));ax.text(xs[i],.37,b,ha='center',fontsize=8.8)
 if i<len(nodes)-1:ax.annotate('',xy=(xs[i+1]-.055,.53),xytext=(xs[i]+.055,.53),arrowprops=dict(arrowstyle='->',lw=1.1))
ax.text(.5,.1,'Timeline: X(t-1) -> proxy T(t) -> Y=S*(t+1)-S*(t); negative control=S*(t-1)-S*(t-2)',ha='center',fontsize=9);ax.set_title('Final evidence chain',fontsize=15);save(fig,'fig1_最终研究设计_0916_0831.svg')
# Fig2
fig,ax=plt.subplots(figsize=(8.8,5));labels=['Y full','Y common support','Pre-control full','Pre-control support'];yy=np.arange(4)[::-1]
for y,(_,r) in zip(yy,eff.iterrows()):ax.plot([r.ci_low,r.ci_high],[y,y],lw=2);ax.scatter(r.estimate,y,s=50)
ax.axvline(0,ls='--',lw=1);ax.set_yticks(yy,labels);ax.set_xlabel('AIPW estimate (95% CI)');ax.set_title('Main outcome and pre-treatment negative control');ax.grid(axis='x',alpha=.2);save(fig,'fig2_AIPW与负对照_0916_0831.svg')
# Fig3
fig,ax=plt.subplots(figsize=(9.8,5.2));x=np.arange(len(mon));ax.axhline(0,lw=1);ax.vlines(x,0,mon.dr_lift,lw=1.5);ax.scatter(x,mon.dr_lift,s=55)
for i,r in mon.iterrows():ax.annotate(f'T={int(r.n_treat)}',(i,r.dr_lift),xytext=(0,7 if r.dr_lift>=0 else -12),textcoords='offset points',ha='center',fontsize=8)
ax.set_xticks(x,mon.ym.astype(str),rotation=35,ha='right');ax.set_xlabel('Out-of-time test month');ax.set_ylabel('Top-30% DR lift vs rest');ax.set_title('Rolling out-of-time DR ranking validation');ax.grid(axis='y',alpha=.2);save(fig,'fig3_滚动时间外DR_0916_0831.svg')
# Fig4
fig,ax=plt.subplots(figsize=(9,5.1));ax.axhline(0,lw=1);ax.plot(topk.top_pct,topk.gain_vs_all,marker='o',label='vs all');ax.plot(topk.top_pct,topk.gain_vs_state,marker='s',label='vs state score');ax.plot(topk.top_pct,topk.gain_vs_inventory,marker='^',label='vs inventory ratio');ax.set_xlabel('Top-k review coverage (%)');ax.set_ylabel('DR-score gain');ax.set_title('Non-monotonic Top-k ranking gain');ax.legend(frameon=False);ax.grid(alpha=.2);save(fig,'fig4_TopK增益_0916_0831.svg')
# Fig5
q=seeds[seeds.seed!=101];fig,ax=plt.subplots(figsize=(8,5));ax.scatter(q.spearman,q.top20_overlap,s=55)
for _,r in q.iterrows():ax.annotate(str(int(r.seed)),(r.spearman,r.top20_overlap),xytext=(4,4),textcoords='offset points',fontsize=8)
ax.axvline(q.spearman.median(),ls='--',lw=1);ax.axhline(q.top20_overlap.median(),ls='--',lw=1);ax.set_xlabel('Spearman vs seed 101');ax.set_ylabel('Top-20% list overlap');ax.set_title('Random-seed ranking stability');ax.grid(alpha=.2);save(fig,'fig5_随机种子稳定性_0916_0831.svg')
# Fig6, anonymized labels in figure; names remain in case CSV
fig,ax=plt.subplots(figsize=(8.6,5.6));ax.axhline(0,lw=1);ax.axvline(0,lw=1);ax.scatter(cases.tau_oot,cases.Y,s=60)
for i,r in cases.iterrows():ax.annotate(f'P{i+1}',(r.tau_oot,r.Y),xytext=(4,4),textcoords='offset points',fontsize=8)
ax.set_xlabel('Strict OOT tau ranking signal');ax.set_ylabel('Observed next-period state change');ax.set_title('Transparent high/low ranking cases');ax.grid(alpha=.2);save(fig,'fig6_真实品规案例_0916_0831.svg')
# Copy final experiment tables
for f in ['oot_dr_monthly.csv','topk_dr_gain.csv','seed_stability.csv','aipw_and_negative_control.csv','representative_cases_final.csv','final_summary.json']:
 shutil.copy2(SRC/f,OUT/f)
(OUT/'README.md').write_text('''# v20-8 final experiment assets — 0916_0831\n\nSource experiment: `../0916_0827/` (corrected P35 by `ym`).\n\n- `fig1...fig6`: figures used by v20-8 manuscript.\n- `oot_dr_monthly.csv`: strict rolling out-of-time DR results.\n- `topk_dr_gain.csv`: Top-k comparison with overall/state/inventory baselines.\n- `seed_stability.csv`: random-seed ranking stability.\n- `aipw_and_negative_control.csv`: common-support AIPW + genuine pre-treatment negative control.\n- `representative_cases_final.csv`: top/bottom five OOT treated cases, selected by tau only.\n\nEstimator: R-learner with LightGBM base learners; dynamic X is t-1; S* excludes fill; P35 is calculated separately within each `ym`.\n''',encoding='utf-8')
print('built',OUT)
