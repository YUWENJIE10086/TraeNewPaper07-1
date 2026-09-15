# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

STAMP="0915_2339"
ROOT=Path(__file__).resolve().parent
FIG=ROOT/"figures"
FIG.mkdir(exist_ok=True)

cases=pd.read_csv(ROOT/"v20_4_实际品规案例明细.csv")

mpl.rcParams["font.family"]="AR PL SungtiL GB"
mpl.rcParams["axes.unicode_minus"]=False
mpl.rcParams["svg.fonttype"]="path"

def save(fig,name):
    fig.savefig(FIG/name,format="svg",bbox_inches="tight")
    plt.close(fig)

fig,ax=plt.subplots(figsize=(11.5,4.8)); ax.set_axis_off()
nodes=[("数据与时间轴","203品规×18个月\n仅使用处理前画像"),("状态评分","顺价·毛利·库存消化·动销\n不含处理定义字段"),("代理事件识别","订单满足率月内P35\n且环比下降>2个百分点"),("异质性排序","诚实因果森林\n按品规分组交叉拟合"),("证据约束","共同支持·负对照\nPSM·阈值敏感性"),("人工复核","优先复核/观察/暂缓\n不自动给减量幅度")]
xs=np.linspace(.07,.93,len(nodes))
for i,(t,b) in enumerate(nodes):
    ax.text(xs[i],.62,t,ha="center",va="center",fontsize=11,fontweight="bold",bbox=dict(boxstyle="round,pad=.45",fc="white",ec="black",lw=1))
    ax.text(xs[i],.35,b,ha="center",va="center",fontsize=9.2)
    if i<len(nodes)-1: ax.annotate("",xy=(xs[i+1]-.07,.53),xytext=(xs[i]+.07,.53),arrowprops=dict(arrowstyle="->",lw=1.1))
ax.text(.5,.08,"研究边界：代理事件用于探索性关联排序；正式因果决策仍需真实调控日志与前瞻试验",ha="center",fontsize=9.5)
ax.set_title("研究设计与证据链",fontsize=14,pad=10)
save(fig,f"fig1_研究设计_{STAMP}.svg")

labels=["诚实因果森林 ATE","双向固定效应"]
est=[0.659,1.195]; lo=[-1.679,-0.119]; hi=[2.997,2.510]
fig,ax=plt.subplots(figsize=(8.8,4.8)); y=np.arange(2)[::-1]
for yi,e,l,h in zip(y,est,lo,hi):
    ax.plot([l,h],[yi,yi],lw=1.6); ax.scatter([e],[yi],s=45)
ax.axvline(0,lw=1,ls="--"); ax.set_yticks(y,labels); ax.set_xlabel("效应估计（95% CI）"); ax.set_title("总体效应估计及不确定性"); ax.grid(axis="x",alpha=.2)
save(fig,f"fig2_总体效应森林图_{STAMP}.svg")

diag=pd.DataFrame({"诊断":["PSM前|SMD|","PSM后|SMD|","低共同支持样本占比","处理前负对照"],"值":[0.178,0.057,0.148,3.278]})
fig,ax=plt.subplots(figsize=(9.5,4.8)); ax.bar(np.arange(len(diag)),diag["值"]); ax.set_xticks(np.arange(len(diag)),diag["诊断"],rotation=12,ha="right"); ax.set_title("识别风险与稳健性诊断（不同量纲，仅作并列展示）"); ax.set_ylabel("统计量"); ax.grid(axis="y",alpha=.2)
save(fig,f"fig3_稳健性诊断_{STAMP}.svg")

fig,ax=plt.subplots(figsize=(9.6,6.3)); x=np.log1p(cases["存销比"]); y=cases["供给收缩前S*"]; sizes=55+40*np.abs(cases["CATE"]); sc=ax.scatter(x,y,s=sizes,c=cases["CATE"],alpha=.8)
for _,r in cases.iterrows(): ax.annotate(r["品规"],(np.log1p(r["存销比"]),r["供给收缩前S*"]),xytext=(4,4),textcoords="offset points",fontsize=7.6)
ax.set_xlabel("log(存销比)"); ax.set_ylabel("处理前状态评分 S*"); ax.set_title("代表性品规的处理前经营画像与CATE排序"); fig.colorbar(sc,ax=ax,fraction=.04,pad=.02,label="CATE"); ax.grid(alpha=.18)
save(fig,f"fig4_品规经营画像_{STAMP}.svg")

fig,ax=plt.subplots(figsize=(9.3,6.0)); ax.scatter(cases["CATE"],cases["下期变化"],s=70)
for _,r in cases.iterrows(): ax.annotate(r["品规"],(r["CATE"],r["下期变化"]),xytext=(4,4),textcoords="offset points",fontsize=7.6)
ax.axhline(0,lw=1); ax.axvline(0,lw=1); ax.set_xlabel("CATE排序信号"); ax.set_ylabel("下一期实际状态变化"); ax.set_title("代表性品规：排序信号与下一期实际变化"); ax.grid(alpha=.18)
save(fig,f"fig5_排序与实际变化_{STAMP}.svg")
