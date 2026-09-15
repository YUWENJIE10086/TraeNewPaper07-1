# -*- coding: utf-8 -*-
"""v18-3 高级图 1:1 复刻（数据换为诚实口径）——按照原 v18-2/v18-4 高级母版版式生成。
图1 研究框架框图（三栏）→ fig1_framework.png
图2 CATE直方+KDE+CDF → fig2_cate_dist.png
图3 四组密度 → fig3_cate_density_groups.png
图4 政策收益吸收地图(散点) → fig4_effect_absorption_map.png
图5 价位段×敏感组热力图+梯度 → fig5_priceband_heatmap.png
图6 价位段/品类/时令森林图 → fig6_subgroup_forest.png
图7 高敏感代表品规轨迹 → fig7_trajectory.png
图8 10个代表性品规轨迹面板 → fig8_product_panel.png
数据: 诚实因果森林重跑 v18-1/data 面板
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
from matplotlib.patches import FancyBboxPatch, Rectangle

BASE = r"D:\TraeNewPaper07-1\Papers2\v18\v18-1\data"
FIG  = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\figures"
os.makedirs(FIG, exist_ok=True)

C_PRIMARY="#2F5D8A"; C_SECOND="#4FA3A5"; C_ACCENT="#E08A4A"; C_LIGHT="#7A9CC6"
C_GRAY="#8C8C8C"; C_DARK="#1A1A1A"

for f in ["Microsoft YaHei","SimHei","SimSun"]:
    if any(x.name==f for x in fm.fontManager.ttflist):
        rcParams["font.sans-serif"]=[f]; break
rcParams["axes.unicode_minus"]=False
rcParams["font.size"]=11; rcParams["axes.linewidth"]=0.9
rcParams["axes.edgecolor"]="#555555"; rcParams["figure.dpi"]=300; rcParams["savefig.dpi"]=300
rcParams["font.family"]="sans-serif"; rcParams["axes.titlesize"]=11; rcParams["axes.labelsize"]=10.5

def chart_title(ax,title): ax.set_title(title,fontsize=11,pad=10,color=C_DARK,weight="bold")
def set_style(ax):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8); ax.spines["bottom"].set_linewidth(0.8)
    ax.grid(axis="y",ls="--",lw=0.6,alpha=0.35,color="#B0B0B0"); ax.set_axisbelow(True)

data = pd.read_csv(os.path.join(BASE,"causal_forest_panel.csv"), encoding="utf-8-sig")
data["cat"]=data["cat"].fillna("三类烟"); data["price_band_cat"]=data["price_band_cat"].fillna("中档")
panel = data.copy()
panel["price_band"]=panel["price_band_cat"].map({"低档":1,"中低档":2,"中档":3,"中高档":4,"高档":5})
for _c in ["util","fill","full_surf","ord_success","price_index","gross_margin","unitval",
           "inventory_ratio","channel_coverage","demand_gap","amt_per_cust","new_cust"]:
    if _c+"_pre" in data.columns:
        data[_c]=data[_c+"_pre"]
GROUP_ORDER=["低敏感","中敏感","高敏感"]

# =====================================================================
# 图1 三栏研究框架框图（复刻上传母版：研究动机 → 研究框架 → 实证应用）
# =====================================================================
def fig1():
    fig,ax=plt.subplots(figsize=(14,8.5)); ax.set_xlim(0,14); ax.set_ylim(0,8.5); ax.axis("off")
    ax.text(7,8.18,"卷烟品规差异化调控研究框架",ha="center",fontsize=13,weight="bold",color=C_DARK)
    # 顶部横幅：三阶段
    for x0,w,label in [(0.35,2.7,"研究动机"),(3.5,8.0,"研究框架"),(11.35,2.3,"实证应用")]:
        ax.add_patch(Rectangle((x0,7.7),w,0.42,fc="#EEF2F7",ec="#2F5D8A",lw=0.9))
        ax.text(x0+w/2,7.91,label,ha="center",va="center",fontsize=10.5,color=C_PRIMARY,weight="bold")
    def box(x,y,w,h,text,fc="#FFFFFF",ec="#2F5D8A",tc="#1A1A1A",fs=9,lw=1.2,dashed=False):
        ls=(0,(4,2)) if dashed else "solid"
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02",fc=fc,ec=ec,lw=lw,linestyle=ls))
        ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,color=tc,linespacing=1.5)
    def arrow(x1,y1,x2,y2,color="#2F5D8A",style="->"):
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle=style,color=color,lw=1.4))
    # 左栏 研究动机
    box(0.35,5.4,2.7,1.6,"实际问题\n同一缩投动作\n品规响应不同",ec="#8C8C8C",fs=9.2,dashed=True)
    box(0.35,3.0,2.7,1.6,"研究现状\n依赖经验与平均指标\n难以判断各品规缩投成效",ec="#8C8C8C",fs=8.8,dashed=True)
    arrow(1.7,5.4,1.7,4.75,"#8C8C8C"); arrow(1.7,3.0,1.7,2.35,"#8C8C8C")
    # 中栏 研究框架 四层
    lx, lw_ = 3.5, 8.0
    box(lx,6.62,lw_,0.82,"数据输入","#FFFFFF",ec="#C9D4E3",tc=C_DARK,fs=9.4)
    ax.text(lx+0.25,7.0,"多指标销售　品牌月进货　多规格日度　动销与趋势",ha="left",va="center",fontsize=8.4,color="#444")
    box(lx,5.28,lw_,1.02,"变量构造：经营状态量化","#7A9CC6",ec=C_PRIMARY,tc="#FFFFFF",fs=9.4)
    ax.text(lx+0.25,5.62,"缩投前画像 X ＋供给收缩 T → 下期状态变化 Y",ha="left",va="center",fontsize=8.7,color="#FFFFFF")
    box(lx,3.94,lw_,1.02,"核心创新：定制化生态因果森林识别CATE","#2F5D8A",tc="#FFFFFF",fs=9.6)
    ax.text(lx+0.25,4.28,"R-learner → 交叉拟合 → 诚实因果树 → 品规级 CATE",ha="left",va="center",fontsize=8.6,color="#FFFFFF")
    box(lx,2.6,lw_,1.02,"结果转化","#4FA3A5",tc="#FFFFFF",fs=9.4)
    ax.text(lx+0.25,2.94,"SHAP归因 → 规则阈值 → 回溯验证 → 三档复核",ha="left",va="center",fontsize=8.6,color="#FFFFFF")
    for y in [6.62,5.28,3.94,2.6]:
        arrow(7.5,y,7.5,y-0.17)
    # 右栏 实证应用
    box(11.35,5.5,2.3,1.5,"指导对象\n全市品规\n价位段　品类","#FFFFFF",ec="#8C8C8C",fs=9,dashed=True)
    box(11.35,2.6,2.3,1.7,"反馈应用\n投放月\n下期反馈\n滚动复盘","#FFFFFF",ec="#8C8C8C",fs=9,dashed=True)
    arrow(7.5,3.1,11.35,4.4,"#4FA3A5","<->")
    arrow(7.5,3.0,11.35,3.4,"#4FA3A5","<->")
    arrow(7.5,2.9,7.5,2.2,"#2F5D8A"); 
    ax.annotate("",xy=(7.5,1.0),xytext=(7.5,2.2),arrowprops=dict(arrowstyle="->",color="#2F5D8A",lw=1.4))
    ax.text(7,1.55,"下期数据回流 → 样本更新 → 滚动复盘",ha="center",va="center",fontsize=8.6,color=C_SECOND)
    # 双语图注（与母版一致，独立成注）
    ax.text(7,0.55,"图1　卷烟品规差异化调控研究框架",ha="center",fontsize=9.2,color=C_DARK)
    ax.text(7,0.18,"Fig. 1  Research framework for differentiated regulation of cigarette specifications",ha="center",fontsize=8.6,color="#333")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG,"fig1_framework.png"),bbox_inches="tight"); plt.close(fig); print("fig1 框图 ok")

# =====================================================================
# 图2 CATE直方图+KDE(上) + CDF(下)  —— 诚实口径
# =====================================================================
def fig2():
    tau=data["CATE"]
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(9.2,6.6),gridspec_kw={"height_ratios":[1.45,0.7]},sharex=True)
    q_hi=np.quantile(tau,0.667); q_lo=np.quantile(tau,0.333)
    bins=np.linspace(tau.min(),tau.max(),46)
    ax1.hist(tau[tau<=q_hi],bins=bins,color=C_PRIMARY,alpha=0.88,label="低/中敏感")
    ax1.hist(tau[tau>q_hi],bins=bins,color=C_ACCENT,alpha=0.95,label="高敏感 (CATE>%.2f)"%q_hi)
    from scipy.stats import gaussian_kde
    xg=np.linspace(tau.min(),tau.max(),300); kde=gaussian_kde(tau,bw_method=0.2)
    ax1_r=ax1.twinx(); ax1_r.plot(xg,kde(xg),color=C_SECOND,lw=1.9,label="KDE密度")
    ax1_r.set_ylabel("核密度",color=C_SECOND,fontsize=9.8); ax1_r.tick_params(axis="y",labelcolor=C_SECOND)
    ax1_r.spines["top"].set_visible(False); ax1_r.spines["right"].set_color(C_SECOND)
    for x,c,txt in [(np.mean(tau),C_GRAY,f"ATE均值={np.mean(tau):.2f}"),(q_lo,C_LIGHT,f"低敏感上界={q_lo:.2f}"),(q_hi,C_ACCENT,f"高敏感下界={q_hi:.2f}")]:
        ax1.axvline(x,color=c,ls="--" if c!=C_ACCENT else "-",lw=1.4)
        ax1.text(x,ax1.get_ylim()[1]*0.97,txt,fontsize=8.2,color=c,ha="left",va="top",rotation=90)
    ax1.set_ylabel("品规-月样本数"); set_style(ax1)
    ax1.legend(loc="upper left",frameon=False,fontsize=8.3); ax1_r.legend(loc="upper right",frameon=False,fontsize=8.3)
    chart_title(ax1,"供给收缩调控下品规CATE分布")
    xs=np.sort(tau.values); ecdf=np.arange(1,len(xs)+1)/len(xs)
    ax2.plot(xs,ecdf,color=C_DARK,lw=1.6); ax2.fill_between(xs,0,ecdf,color="#D9E2EE",alpha=0.65)
    ax2.axvline(q_lo,color=C_LIGHT,lw=1.2,ls="--"); ax2.axvline(q_hi,color=C_ACCENT,lw=1.2,ls="-")
    ax2.text(q_lo,0.22,"低敏感上界",fontsize=8.1,color=C_LIGHT,rotation=90,va="bottom")
    ax2.text(q_hi,0.66,"高敏感下界",fontsize=8.1,color=C_ACCENT,rotation=90,va="bottom")
    ax2.set_ylabel("累计占比"); ax2.set_xlabel("条件平均处理效应 CATE（供给收缩对下月状态评分变化的影响）")
    ax2.set_ylim(0,1.02); set_style(ax2); ax2.grid(axis="x",ls="--",lw=0.45,alpha=0.22,color="#B0B0B0")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig2_cate_dist.png"),bbox_inches="tight"); plt.close(fig); print("fig2 ok")

# =====================================================================
# 图3 四组密度图（母版：低/中/高敏感+总体 直方密度平滑）
# =====================================================================
def fig3():
    fig,ax=plt.subplots(figsize=(7.6,5.2))
    colors={"低敏感":C_LIGHT,"中敏感":C_SECOND,"高敏感":C_ACCENT,"总体":"#B4555B"}
    lo,hi=float(data.CATE.min()),float(data.CATE.max())
    bins=np.linspace(lo,hi,34); centers=(bins[:-1]+bins[1:])/2
    for g in GROUP_ORDER:
        vals=data.loc[data.sensitivity==g,"CATE"].to_numpy(float)
        hist,_=np.histogram(vals,bins=bins,density=True)
        smooth=np.convolve(hist,np.ones(3)/3,mode="same")
        ax.fill_between(centers,0,smooth,step="mid",color=colors[g],alpha=.16)
        ax.plot(centers,smooth,color=colors[g],lw=1.8,label=g)
        ax.axvline(np.median(vals),color=colors[g],lw=.8,alpha=.75)
    vals=data.CATE.to_numpy(float)
    hist,_=np.histogram(vals,bins=bins,density=True)
    smooth=np.convolve(hist,np.ones(3)/3,mode="same")
    ax.plot(centers,smooth,color=colors["总体"],lw=1.7,label="总体")
    ax.fill_between(centers,0,smooth,step="mid",color=colors["总体"],alpha=.10)
    ax.axvline(0,color="#666",ls="--",lw=1.1)
    ax.set_xlabel("处理效应CATE"); ax.set_ylabel("密度"); set_style(ax)
    ax.legend(frameon=False,fontsize=8.5); chart_title(ax,"不同敏感组处理效应密度分布")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig3_cate_density_groups.png"),bbox_inches="tight"); plt.close(fig); print("fig3 ok")

# =====================================================================
# 图4 政策收益吸收地图（二维能力定位+色阶CATE+象限标注）
# =====================================================================
def fig4():
    from sklearn.preprocessing import StandardScaler
    work=data.copy()
    xcols=["price_index","ord_success","channel_coverage","util"]
    ycols=["fill","demand_gap","inventory_ratio","S_pre"]
    xx=work[xcols].apply(lambda s:s.fillna(s.median())); yy=work[ycols].apply(lambda s:s.fillna(s.median()))
    yy["inventory_ratio"]*=-1
    work["连接嵌入"]=StandardScaler().fit_transform(xx).mean(axis=1)
    work["状态吸收"]=StandardScaler().fit_transform(yy).mean(axis=1)
    fig,ax=plt.subplots(figsize=(7.6,5.8))
    sc=ax.scatter(work["连接嵌入"],work["状态吸收"],c=work.CATE,cmap="RdYlBu_r",s=15,alpha=.72,edgecolors="none")
    ax.axhline(0,color="#666",ls="--",lw=1); ax.axvline(0,color="#666",ls="--",lw=1)
    top=work.sort_values("CATE",ascending=False).drop_duplicates("name").head(4)
    for _,r in top.iterrows():
        ax.text(r["连接嵌入"]+.04,r["状态吸收"]+.04,str(r["name"])[:9],fontsize=7,color=C_DARK)
    ax.text(.02,.96,"高承接-高吸收\n优先缩投观察区",transform=ax.transAxes,fontsize=8.5,color=C_PRIMARY,va="top")
    ax.text(.67,.08,"弱吸收区\n转向动销/去库存",transform=ax.transAxes,fontsize=8.5,color=C_SECOND,va="bottom")
    ax.set_xlabel("市场连接与供给嵌入能力（标准化综合得分）")
    ax.set_ylabel("资源调度与状态吸收能力（标准化综合得分）")
    set_style(ax); cb=fig.colorbar(sc,ax=ax,fraction=.046,pad=.03); cb.set_label("品规层面CATE")
    chart_title(ax,"政策收益吸收地图")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig4_effect_absorption_map.png"),bbox_inches="tight"); plt.close(fig); print("fig4 ok")

# =====================================================================
# 图5 价位段×敏感组热力图 + 梯度柱 (原fig8)
# =====================================================================
def fig5():
    raw=data[["code","ym","CATE","sensitivity"]].merge(panel[["code","ym","price_band"]],on=["code","ym"],how="left")
    raw=raw.dropna(subset=["price_band","sensitivity","CATE"]).copy(); raw["price_band"]=raw["price_band"].astype(int)
    band_map={2:"中低档",3:"中档",4:"中高档",5:"高档"}
    sens_order=["低敏感","中敏感","高敏感"]; band_order=[2,3,4,5]
    mean_pivot=raw.groupby(["price_band","sensitivity"])["CATE"].mean().unstack().reindex(index=band_order,columns=sens_order)
    cnt_pivot=raw.groupby(["price_band","sensitivity"])["CATE"].size().unstack().reindex(index=band_order,columns=sens_order).fillna(0).astype(int)
    fig,(ax,ax2)=plt.subplots(1,2,figsize=(11.2,5.5),gridspec_kw={"width_ratios":[0.95,1.05]})
    arr=mean_pivot.values
    im=ax.imshow(arr,cmap="RdBu_r",aspect="auto")
    ax.set_xticks(np.arange(len(sens_order))); ax.set_xticklabels(sens_order,fontsize=10)
    ax.set_yticks(np.arange(len(band_order))); ax.set_yticklabels([band_map[b] for b in band_order],fontsize=10)
    ax.set_xlabel("调控敏感组别"); ax.set_ylabel("价位段"); chart_title(ax,"不同价位段在敏感组中的CATE分化")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val=arr[i,j]; cnt=cnt_pivot.iloc[i,j]
            txt_color="#FFFFFF" if np.isnan(val) or abs(val)>1.2 else C_DARK
            ax.text(j,i,f"{val:.2f}\n(n={cnt})",ha="center",va="center",fontsize=8.2,color=txt_color)
    cbar=fig.colorbar(im,ax=ax,fraction=.046,pad=.04); cbar.set_label("平均CATE")
    ax.set_xticks(np.arange(-.5,len(sens_order),1),minor=True); ax.set_yticks(np.arange(-.5,len(band_order),1),minor=True)
    ax.grid(which="minor",color="#FFFFFF",linestyle="-",linewidth=1.0); ax.tick_params(which="minor",bottom=False,left=False)
    ax.text(0.02,-0.16,"注：单元格为该价位段对应敏感组平均CATE，括号内为样本量。",transform=ax.transAxes,fontsize=8.4,color="#666666")
    long_df=mean_pivot.reset_index().melt(id_vars="price_band",var_name="敏感组",value_name="平均CATE")
    long_df["价位段"]=long_df["price_band"].map(band_map)
    xpos=np.arange(len(band_order)); width=0.22
    color_map={"低敏感":C_LIGHT,"中敏感":C_SECOND,"高敏感":C_ACCENT}
    for j,s in enumerate(sens_order):
        vals=long_df[long_df["敏感组"]==s]["平均CATE"].values
        ax2.bar(xpos+(j-1)*width,vals,width=width,color=color_map[s],edgecolor="#FFFFFF",label=s)
        ax2.plot(xpos+(j-1)*width,vals,color=color_map[s],lw=0.9,alpha=0.7)
    ax2.axhline(0,color="#666666",lw=0.9)
    ax2.set_xticks(xpos); ax2.set_xticklabels([band_map[b] for b in band_order],fontsize=9.2)
    ax2.set_ylabel("平均CATE"); set_style(ax2); ax2.grid(axis="x",visible=False)
    ax2.legend(frameon=False,fontsize=8.8,ncol=3,loc="upper left")
    ax2.set_title("不同价位段的敏感度梯度",fontsize=10.2,pad=8,color=C_DARK)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig5_priceband_heatmap.png"),bbox_inches="tight"); plt.close(fig); print("fig5 ok")

# =====================================================================
# 图6 价位段/品类/时令森林图
# =====================================================================
def fig6():
    work=data.copy(); work["时令"]=np.where(work["month"].astype(int).isin([1,2]),"元春","常规")
    rows=[]
    for dim,col in [("价位段","price_band_cat"),("品类","cat"),("时令","时令")]:
        for name,g in work.groupby(col):
            vals=g.CATE.to_numpy(float); se=np.std(vals,ddof=1)/np.sqrt(len(vals)) if len(vals)>1 else 0
            rows.append((dim,str(name),len(vals),np.mean(vals),np.mean(vals)-1.96*se,np.mean(vals)+1.96*se))
    z=pd.DataFrame(rows,columns=["维度","子组","n","均值","下限","上限"]).tail(14)
    y=np.arange(len(z)); fig,ax=plt.subplots(figsize=(7.8,5.8))
    ax.errorbar(z["均值"],y,xerr=[z["均值"]-z["下限"],z["上限"]-z["均值"]],fmt="o",color=C_PRIMARY,
                ecolor=C_LIGHT,elinewidth=1.3,capsize=3,ms=4.5)
    ax.axvline(0,color="#666",ls="--",lw=1)
    ax.set_yticks(y); ax.set_yticklabels(z["维度"]+"-"+z["子组"]+" (n="+z["n"].astype(str)+")",fontsize=8.3)
    ax.set_xlabel("平均CATE及95%置信区间"); set_style(ax)
    ax.grid(axis="x",ls="--",lw=.55,alpha=.25); chart_title(ax,"价位段、品类与时令异质性森林图")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig6_subgroup_forest.png"),bbox_inches="tight"); plt.close(fig); print("fig6 ok")

# =====================================================================
# 图7 高敏感代表品规月度状态轨迹
# =====================================================================
def fig7():
    trt=data[data["T"]==1]; target="天子(中支)"
    code=panel[panel["name"].astype(str)==target]["code"].iloc[0]
    sub=panel[panel["code"]==code].sort_values("ym")
    if len(sub)<6:
        code=data["code"].value_counts().index[0]; sub=panel[panel["code"]==code].sort_values("ym")
    sdp=sub[["ym","code"]].copy(); sdp=sdp.merge(panel[["code","ym","S"]].drop_duplicates(["code","ym"]),on=["code","ym"])
    treat_map=trt[trt["code"]==code][["ym","T","CATE"]].drop_duplicates("ym")
    sdp=sdp.merge(treat_map,on="ym",how="left"); sdp["T"]=sdp["T"].fillna(0); sdp["CATE"]=sdp["CATE"].fillna(0)
    sdp["S"]=(sdp["S"]-sdp["S"].min())/max((sdp["S"].max()-sdp["S"].min()),1e-6)*40+30
    sdp["ymlbl"]=sdp["ym"].astype(str)
    fig,ax=plt.subplots(figsize=(9.6,4.8))
    q1,q2=sdp["S"].quantile([0.33,0.67]).values
    ax.axhspan(sdp["S"].min()-1,q1,color="#EEF3F8",alpha=0.65,lw=0)
    ax.axhspan(q1,q2,color="#F8FAFC",alpha=0.80,lw=0); ax.axhspan(q2,sdp["S"].max()+1,color="#F2F6FB",alpha=0.55,lw=0)
    ax.plot(range(len(sdp)),sdp["S"],color=C_PRIMARY,lw=2.2,marker="o",ms=5,label="市场状态评分S")
    treat_months=set(sdp.loc[sdp["T"]==1,"ymlbl"].tolist())
    for i,lab in enumerate(sdp["ymlbl"]):
        if lab in treat_months:
            ax.axvspan(i-0.23,i+0.23,color=C_ACCENT,alpha=0.11,lw=0); ax.text(i,sdp["S"].max()+1.2,"缩",ha="center",va="bottom",fontsize=7.8,color=C_ACCENT)
    best=sdp["S"].idxmax(); worst=sdp["S"].idxmin()
    ax.plot(best,sdp.loc[best,"S"],"o",color=C_ACCENT,ms=9,zorder=5); ax.plot(worst,sdp.loc[worst,"S"],"o",color=C_LIGHT,ms=7,zorder=5)
    ax.annotate("状态改善峰值\n+%.1f分"%(sdp.loc[best,"S"]-sdp["S"].min()),xy=(best,sdp.loc[best,"S"]),
                xytext=(best+1.5,sdp["S"].max()*0.9),arrowprops=dict(arrowstyle="->",color=C_ACCENT),fontsize=9,color=C_ACCENT)
    ax.annotate("阶段低点\n%.1f分"%sdp.loc[worst,"S"],xy=(worst,sdp.loc[worst,"S"]),
                xytext=(max(worst-1.2,0),sdp.loc[worst,"S"]-6.5),arrowprops=dict(arrowstyle="->",color=C_LIGHT),fontsize=8.3,color=C_LIGHT)
    for idx in sdp.index[sdp["T"]==1].tolist()[:2]:
        ax.text(idx,sdp.loc[idx,"S"]+2.0,f"CATE={sdp.loc[idx,'CATE']:.1f}",fontsize=7.6,color=C_ACCENT,ha="center")
    ax.set_xticks(range(len(sdp))); ax.set_xticklabels(sdp["ymlbl"],rotation=45,fontsize=9)
    ax.set_xlabel("月份"); ax.set_ylabel("市场状态评分（归一化到30-70区间）")
    ax.set_title(f"图7　高敏感代表品规（{str(sub.iloc[0]['name'])[:14]}）月度状态轨迹",fontsize=10,pad=10,color=C_DARK,weight="bold")
    set_style(ax); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig7_trajectory.png"),bbox_inches="tight"); plt.close(fig); print("fig7 ok")

# =====================================================================
# 图8 10个代表性品规轨迹面板
# =====================================================================
def fig8():
    pan=panel.copy(); pan["ym"]=pan["ym"].astype(str)
    treated=pan[pan["T"]==1].copy()
    name_rank=treated.groupby("name",as_index=False).agg(mean_cate=("CATE","mean"),treat_cnt=("T","sum"))
    hi_names=name_rank.sort_values(["mean_cate","treat_cnt"],ascending=[False,False])["name"].dropna().drop_duplicates().head(5).tolist()
    lo_names=name_rank.sort_values(["mean_cate","treat_cnt"],ascending=[True,False])["name"].dropna().drop_duplicates().head(5).tolist()
    names_pick=hi_names+lo_names
    sub=pan[pan["name"].isin(names_pick)].copy()
    sub["dt"]=pd.to_datetime(sub["ym"]+"01",format="%Y%m%d")
    s_min,s_max=sub["S"].min(),sub["S"].max(); sub["S_plot"]=(sub["S"]-s_min)/max((s_max-s_min),1e-9)*100
    fig,axes=plt.subplots(5,2,figsize=(11.6,16.5),sharex=False,sharey=True); axes=axes.ravel()
    hi_set=set(hi_names)
    for ax,name in zip(axes,names_pick):
        d=sub[sub["name"]==name].sort_values("dt").copy()
        if d.empty: ax.axis("off"); continue
        is_hi=name in hi_set; main_color=C_PRIMARY if is_hi else C_SECOND
        ax.set_facecolor("#FCFDFE")
        lq1,lq2=d["S_plot"].quantile([0.33,0.67]).values
        ax.axhspan(0,lq1,color="#F3F7FB",alpha=0.55,lw=0); ax.axhspan(lq1,lq2,color="#FAFBFD",alpha=0.72,lw=0)
        for _,r in d.iterrows():
            x0=r["dt"]-pd.Timedelta(days=14); x1=r["dt"]+pd.Timedelta(days=14)
            bg=C_ACCENT if float(r.get("T",0) or 0)==1 else C_LIGHT
            ax.axvspan(x0,x1,color=bg,alpha=0.10 if bg==C_ACCENT else 0.08,lw=0)
        ax.plot(d["dt"],d["S_plot"],color=main_color,lw=1.8,marker="o",ms=2.8,zorder=3)
        tmask=d["T"].fillna(0)==1
        ax.scatter(d.loc[tmask,"dt"],d.loc[tmask,"S_plot"],color=C_ACCENT,s=24,zorder=4)
        for _,r in d.loc[tmask].head(3).iterrows():
            ax.annotate("缩",(r["dt"],r["S_plot"]),xytext=(0,7),textcoords="offset points",ha="center",fontsize=7.2,color=C_ACCENT)
        max_idx=d["S_plot"].idxmax(); min_idx=d["S_plot"].idxmin(); end_idx=d.index[-1]
        ax.text(d.loc[max_idx,"dt"],d.loc[max_idx,"S_plot"]+4,f"{d.loc[max_idx,'S_plot']:.1f}",fontsize=6.8,color=C_ACCENT if is_hi else C_PRIMARY,ha="center")
        ax.text(d.loc[min_idx,"dt"],d.loc[min_idx,"S_plot"]-6,f"{d.loc[min_idx,'S_plot']:.1f}",fontsize=6.8,color=C_LIGHT,ha="center")
        ax.text(d.loc[end_idx,"dt"],d.loc[end_idx,"S_plot"]+2.2,f"{d.loc[end_idx,'S_plot']:.1f}",fontsize=6.8,color=main_color,ha="left")
        cat=str(d["cat"].dropna().iloc[0]) if d["cat"].notna().any() else "-"
        sens="高敏感代表" if is_hi else "低敏感代表"
        ax.set_title(f"{name}（{cat}，{sens}）",fontsize=8.9,color=C_DARK,pad=4)
        ax.grid(axis="y",ls="--",lw=0.55,alpha=0.28,color="#B0B0B0"); ax.grid(axis="x",ls="--",lw=0.45,alpha=0.18,color="#B0B0B0")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x",rotation=45,labelsize=7.1); ax.tick_params(axis="y",labelsize=7.6); ax.set_ylim(0,110)
    for ax in axes[::2]: ax.set_ylabel("综合评分",fontsize=8.8)
    for ax in axes[-2:]: ax.set_xlabel("月份",fontsize=9)
    for ax in axes[len(names_pick):]: ax.axis("off")
    fig.text(0.5,0.968,"高敏感代表样本",ha="center",va="top",fontsize=10.4,color=C_PRIMARY,weight="bold")
    fig.text(0.5,0.028,"低敏感代表样本",ha="center",va="center",fontsize=10.4,color=C_SECOND,weight="bold")
    fig.suptitle("10个代表性品规月度综合评分轨迹与缩投事件对照",fontsize=11.6,color=C_DARK,y=0.995,weight="bold")
    fig.tight_layout(rect=[0,0,1,0.985]); fig.savefig(os.path.join(FIG,"fig8_product_panel.png"),bbox_inches="tight"); plt.close(fig); print("fig8 ok")

if __name__=="__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8()
    print("\n高级图表全部生成完成 →",FIG)