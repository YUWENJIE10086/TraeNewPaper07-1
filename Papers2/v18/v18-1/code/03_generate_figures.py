# -*- coding: utf-8 -*-
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parents[1]; DATA=BASE/"data"; FIG=BASE/"figures"; FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.sans-serif":["Microsoft YaHei","SimHei","Arial Unicode MS"],"axes.unicode_minus":False,"figure.dpi":160,"savefig.dpi":300})
C1="#2F5D8A"; C2="#4FA3A5"; CA="#E08A4A"; CL="#9CB6D3"; CG="#777777"
d=pd.read_csv(DATA/"causal_forest_panel.csv",encoding="utf-8-sig"); imp=pd.read_csv(DATA/"feature_importance.csv",encoding="utf-8-sig"); smd=pd.read_csv(DATA/"psm_smd.csv",encoding="utf-8-sig")
M=json.loads((DATA/"metrics.json").read_text(encoding="utf-8"))
def finish(fig,name): fig.tight_layout(); fig.savefig(FIG/name,bbox_inches="tight"); plt.close(fig)
def clean(ax): ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y",alpha=.18)

fig,ax=plt.subplots(figsize=(9,4.8)); ax.axis("off")
ax.text(.02,.72,"原始月报\n品规×月份",ha="center",va="center",bbox=dict(boxstyle="round",fc="#EEF3F8",ec=C1))
ax.text(.28,.72,"处理前画像\n23维协变量",ha="center",va="center",bbox=dict(boxstyle="round",fc="#EEF3F8",ec=C1))
ax.text(.54,.72,"诚实因果森林\n品规分组交叉拟合",ha="center",va="center",bbox=dict(boxstyle="round",fc="#EAF5F5",ec=C2))
ax.text(.80,.72,"CATE排序\n三档复核清单",ha="center",va="center",bbox=dict(boxstyle="round",fc="#FFF3E9",ec=CA))
for x in [.12,.38,.64]: ax.annotate("",(x+.11,.72),(x,.72),arrowprops=dict(arrowstyle="->",color=CG,lw=1.5))
ax.text(.41,.25,"关键约束：不使用处理当期信息构造画像；结果为处理前至处理后一期的状态变化",ha="center",fontsize=10,color=CG)
finish(fig,"fig1_framework.png")

fig,ax=plt.subplots(figsize=(8,4.5)); ax.hist(d.CATE,bins=38,color=C1,alpha=.9); ax.axvline(M["ate"],color=CA,ls="--",label=f'ATE={M["ate"]:.2f}'); ax.axvspan(M["ate_ci"][0],M["ate_ci"][1],color=CA,alpha=.12,label="ATE 95%CI"); ax.set(xlabel="条件平均处理效应 CATE（分）",ylabel="品规—月份观测数",title="供给收缩效应的样本分布"); ax.legend(frameon=False); clean(ax); finish(fig,"fig2_cate_distribution.png")

order=["低敏感","中敏感","高敏感"]; fig,ax=plt.subplots(figsize=(8,4.5)); bp=ax.boxplot([d.loc[d.sensitivity.eq(x),"CATE"] for x in order],tick_labels=order,patch_artist=True,showfliers=False); 
for p,c in zip(bp["boxes"],[CL,C2,CA]):p.set_facecolor(c)
ax.axhline(0,color=CG,ls="--"); ax.set(ylabel="CATE（分）",title="三档复核组的估计效应分布"); clean(ax); finish(fig,"fig3_three_tiers.png")

names={"price_index_pre":"顺价指数","inventory_ratio_pre":"存销比","ord_success_pre":"订货成功率","fill_pre":"订单满足率","S_pre":"处理前状态评分","util_pre":"货源利用率","full_surf_pre":"订足面","channel_coverage_pre":"投放客户覆盖率","demand_gap_pre":"需求缺口率","amt_per_cust_pre":"户均订货金额","gross_margin_pre":"毛利率","unitval_pre":"单箱销售额","new_cust_pre":"新进货户数"}
top=imp.head(10).iloc[::-1]; fig,ax=plt.subplots(figsize=(8,5)); ax.barh(range(len(top)),top.importance,color=[CA if i==len(top)-1 else C1 for i in range(len(top))]); ax.set_yticks(range(len(top)),[names.get(x,x.replace("_pre","")) for x in top.feature]); ax.set(xlabel="因果森林分裂重要性",title="CATE异质性的主要经营条件"); clean(ax); finish(fig,"fig4_importance.png")

g=d.groupby("sensitivity").agg(S_pre=("S_prev","mean"),inventory_ratio=("inventory_ratio_pre","mean"),price_index=("price_index_pre","mean"),fill=("fill_pre","mean"),improve=("Y",lambda x:(x>0).mean())).reindex(order)
fig,ax=plt.subplots(figsize=(8,4.5)); z=(g-g.mean())/g.std(); z.T.plot(kind="bar",ax=ax,color=[CL,C2,CA]); ax.set(ylabel="标准化组均值",title="三档对象的处理前经营画像"); ax.legend(title="复核组",frameon=False); clean(ax); finish(fig,"fig5_profiles.png")

tr=d[d["T"].eq(1)]; cut=tr.CATE.quantile(2/3); a=tr[tr.CATE.ge(cut)]; b=tr[tr.CATE.lt(cut)]
fig,ax=plt.subplots(figsize=(7,4.5)); vals=[(a.Y>0).mean()*100,(b.Y>0).mean()*100]; bars=ax.bar(["高效应候选","其余实际缩投对象"],vals,color=[CA,C2]); ax.bar_label(bars,fmt="%.1f%%",padding=3); ax.set(ylabel="处理后状态改善率（%）",title="实际缩投样本的历史回溯比较"); ax.set_ylim(0,max(vals)*1.25); clean(ax); finish(fig,"fig6_backtest.png")

fig,ax=plt.subplots(figsize=(8,5)); s=smd.assign(abs_after=lambda x:x.after.abs()).nlargest(12,"abs_after").iloc[::-1]; y=np.arange(len(s)); ax.barh(y-.18,s.before,height=.34,color=CL,label="匹配前"); ax.barh(y+.18,s.after,height=.34,color=C1,label="匹配后"); ax.axvline(.1,color=CA,ls="--"); ax.axvline(-.1,color=CA,ls="--"); ax.set_yticks(y,[names.get(x,x.replace("_pre","")) for x in s.feature]); ax.set(xlabel="标准化差异 SMD",title="倾向得分匹配前后协变量平衡"); ax.legend(frameon=False); clean(ax); finish(fig,"fig7_psm_balance.png")

fig,ax=plt.subplots(figsize=(8,4.5)); sub=d.groupby("ym").agg(ate_proxy=("CATE","mean"),treated=("T","sum")); ax.plot(sub.index.astype(str),sub.ate_proxy,color=C1,marker="o",label="月均CATE"); ax.axhline(0,color=CG,ls="--"); ax.set_xticks(range(0,len(sub),2),sub.index.astype(str)[::2],rotation=45); ax.set(ylabel="月均CATE（分）",title="月度效应与处理事件分布"); ax2=ax.twinx(); ax2.bar(range(len(sub)),sub.treated,color=CL,alpha=.25,label="处理事件数"); ax2.set_ylabel("处理事件数"); clean(ax); finish(fig,"fig8_monthly_effect.png")
print("figures",len(list(FIG.glob('*.png'))))
