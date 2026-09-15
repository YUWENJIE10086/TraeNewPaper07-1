# -*- coding: utf-8 -*-
"""Regenerate v18-3 figures + table data from HONEST causal-forest rerun."""
import pandas as pd, numpy as np, json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

PRIMARY="#2F5D8A"; SECOND="#4FA3A5"; ACCENT="#E08A4A"; LIGHT="#7A9CC6"; GREY="#8a8f98"
plt.rcParams["font.family"]="Microsoft YaHei"
plt.rcParams["axes.unicode_minus"]=False

BASE=r"D:\TraeNewPaper07-1\Papers2\v18\v18-1\data"
OUT=r"D:\TraeNewPaper07-1\Papers2\v18\v18-3"
FOUT=os.path.join(OUT,"figures"); os.makedirs(FOUT,exist_ok=True)

d=pd.read_csv(os.path.join(BASE,"causal_forest_panel.csv"))
feat=pd.read_csv(os.path.join(BASE,"feature_importance.csv"))
smd=pd.read_csv(os.path.join(BASE,"psm_smd.csv"))
m=json.load(open(os.path.join(BASE,"metrics.json"),encoding="utf-8"))
sh=pd.read_csv(os.path.join(BASE,"causal_forest_shap_importance_v1.csv")) if os.path.exists(os.path.join(BASE,"causal_forest_shap_importance_v1.csv")) else np.nan

d["cat"]=d["cat"].fillna("三类烟")
d["price_band_cat"]=d["price_band_cat"].fillna("中档")
BMAP={"低档":0,"中低档":1,"中档":2,"中高档":3,"高档":4}
d["band_o"]=d["price_band_cat"].map(BMAP)
d["month_n"]=d["month"].astype(int)
d["season"]=np.where(d["month_n"].isin([1,2]),"元春","常规")
d["+1" if False else "Yp"]=d["Y"]

# ---------- Table numbers ----------
N={}
tier=d.groupby("sensitivity")["CATE"]
N["tier_mean"]={k:round(v,2) for k,v in tier.mean().items()}
N["tier_n"]={k:int(v) for k,v in d.groupby("sensitivity")["CATE"].count().items()}
gq=d.groupby("sensitivity")["CATE"].agg(['mean','std','min',lambda x:x.quantile(.25),lambda x:x.quantile(.5),lambda x:x.quantile(.75),'max']).round(2)
N["tier_stats"]=gq.to_dict("index")

band=d.groupby(["band_o","sensitivity"])["CATE"].agg(["mean","count"]).round(2)
N["band"]={}
for b in BMAP.values():
    N["band"][int(b)]={}
    for s in ["低敏感","中敏感","高敏感"]:
        if (b,s) in band.index:
            N["band"][int(b)][s]=[round(float(band.loc[(b,s),"mean"]),1),int(band.loc[(b,s),"count"])]
N["band"]["labels"]={v:k for k,v in BMAP.items()}
cat=d.groupby(["cat","sensitivity"])["CATE"].agg(["mean","count"])
N["cat"]={}
for k in cat.index.get_level_values(0).unique():
    N["cat"][k]={}
    for s in ["低敏感","中敏感","高敏感"]:
        if (k,s) in cat.index:
            N["cat"][k][s]=[round(float(cat.loc[(k,s),"mean"]),1),int(cat.loc[(k,s),"count"])]
season=d.groupby(["season","sensitivity"])["CATE"].agg(["mean","count"])
N["season"]={}
for k in season.index.get_level_values(0).unique():
    N["season"][k]={}
    for s in ["低敏感","中敏感","高敏感"]:
        if (k,s) in season.index:
            N["season"][k][s]=[round(float(season.loc[(k,s),"mean"]),1),int(season.loc[(k,s),"count"])]

treat=d[d["T"]==1]
exp=treat.groupby("sensitivity")["CATE"].mean().sort_values(ascending=False)
hi=exp.index[0]
oh=[x for x in ["低敏感","中敏感","高敏感"] if x!=hi]
N["backtest"]={"high_group":hi,"high_Y":round(float(treat[treat["sensitivity"]==hi]["Y"].mean()),2),
                "other_Y":round(float(treat[treat["sensitivity"].isin(oh)]["Y"].mean()),2),
                "high_n":int(treat[treat["sensitivity"]==hi]["Y"].count()),
                "other_n":int(treat[treat["sensitivity"].isin(oh)]["Y"].count()),
                "high_impr":round(float((treat[treat["sensitivity"]==hi]["Y"]>0).mean())*100,1),
                "other_impr":round(float((treat[treat["sensitivity"].isin(oh)]["Y"]>0).mean())*100,1)}

N["importance"]=feat.sort_values("importance",ascending=False).head(12).to_dict("records")
N["smd"]={"before":round(float(m["psm"]["mean_abs_smd_before"]),3),
          "after":round(float(m["psm"]["mean_abs_smd_after"]),3),
          "pairs":int(m["psm"]["pairs"]),
          "effect":round(float(m["psm"]["effect"]),2)}

# representative specs (real names) high & low
hi_rows=treat[treat["sensitivity"]==hi].sort_values("CATE")
def group_spec(g):
    nm=g["name"].mode().iloc[0] if len(g["name"].mode())>0 else ""
    return nm
rep_high=[]
for nm,g in treat[treat["sensitivity"]==hi].groupby("name"):
    if (g["Y"]>0).mean()>=0.6 and len(g)>=2:
        rep_high.append({"name":nm,"n":len(g),"meanCATE":round(g["CATE"].mean(),2),"meanY":round(g["Y"].mean(),1),"S_pre":round(g["S_pre"].mean(),1),"price":round(g["price_index_pre"].mean(),3)})
rep_high=sorted(rep_high,key=lambda x:x["meanY"],reverse=True)[:4]
rep_low=[]
for nm,g in treat.groupby("name"):
    if g["sensitivity"].mode().iloc[0] in oh and len(g)>=2:
        rep_low.append({"name":nm,"n":len(g),"meanCATE":round(g["CATE"].mean(),2),"meanY":round(g["Y"].mean(),1),"S_pre":round(g["S_pre"].mean(),1)})
rep_low=sorted(rep_low,key=lambda x:x["meanY"])[:4]
N["rep_high"]=rep_high; N["rep_low"]=rep_low

with open(os.path.join(OUT,"v18_3_numbers.json"),"w",encoding="utf-8") as f:
    json.dump({"ate":round(float(m["ate"]),2),"ate_ci":[round(float(m["ate_ci"][0]),2),round(float(m["ate_ci"][1]),2)],
               "cate_sd":round(float(m["cate_sd"]),1),"n":int(m["n"]),"products":int(m["products"]),
               "treated":int(m["treated"]),"backtest":N["backtest"],"tier":N,"band":N["band"],"cat":N["cat"],
               "season":N["season"],"importance":N["importance"],"smd":N["smd"],"rep_high":rep_high,"rep_low":rep_low},f,ensure_ascii=False,indent=1)
print("numbers saved.")

# ---------- FIGURES ----------
def style(ax):
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    ax.grid(axis="y",ls="--",alpha=.4); ax.set_axisbelow(True)

# fig2 CATE distribution
fig,ax=plt.subplots(figsize=(6.6,3.4),dpi=200)
bins=np.linspace(d.CATE.min()-0.2,0.5,40)
ax.hist(d.CATE,bins=bins,color=LIGHT,alpha=.7,label="品规CATE",zorder=2)
ax.axvline(0,color=GREY,ls=":",lw=1)
ax.axvline(float(d.CATE.mean()),color=ACCENT,ls="-",lw=1.6,label=f"均值{float(d.CATE.mean()):.2f}")
ax.axvline(float(m['ate_ci'][0]),color=PRIMARY,ls="--",lw=1.2,label="95%CI−3.64")
ax.axvline(float(m['ate_ci'][1]),color=PRIMARY,ls="--",lw=1.2,label="95%CI+0.52")
ax.set_xlabel("条件平均处理效应 CATE / 分"); ax.set_ylabel("品规—月份数 / 条")
ax.legend(fontsize=7,frameon=False); style(ax); ax.set_title("图2  缩投条件下品规级CATE分布",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig2_cate_distribution.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig3 density by sensitivity
fig,ax=plt.subplots(figsize=(6.6,3.4),dpi=200)
cols={"高敏感":ACCENT,"中敏感":SECOND,"低敏感":PRIMARY}
for s,c in cols.items():
    x=d[d["sensitivity"]==s]["CATE"]
    ax.hist(x,bins=30,density=True,alpha=.38,color=c,label=s+f"(均值{x.mean():.2f})")
ax.axvline(0,color=GREY,ls=":",lw=1)
ax.set_xlabel("CATE / 分"); ax.set_ylabel("核密度")
ax.legend(fontsize=7,frameon=False); style(ax); ax.set_title("图3  不同敏感组的CATE密度分布",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig3_cate_density_groups.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig4 absorption map: price band x category mean CATE
pv=d.pivot_table(index="cat",columns="band_o",values="CATE",aggfunc="mean")
pv=pv.reindex(sorted(pv.columns))
fig,ax=plt.subplots(figsize=(6.2,3.4),dpi=200)
im=ax.imshow(pv.values,cmap="RdYlBu_r",aspect="auto",vmax=0)
ax.set_xticks(range(len(pv.columns))); ax.set_xticklabels([BMAP.get(c,"") for c in pv.columns],fontsize=8)
ax.set_yticks(range(len(pv.index))); ax.set_yticklabels(pv.index,fontsize=8)
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        if not np.isnan(pv.values[i,j]):
            ax.text(j,i,f"{pv.values[i,j]:.1f}",ha="center",va="center",fontsize=7.5,
                    color="white" if abs(pv.values[i,j])>np.nanmax(np.abs(pv.values))/1.6 else "black")
ax.set_xlabel("价位段",fontsize=8); ax.set_ylabel("品类",fontsize=8)
fig.colorbar(im,ax=ax,shrink=.8).set_label("平均 CATE / 分",fontsize=8)
ax.set_title("图4  品类×价位段缩投收益吸收地图",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig4_effect_absorption_map.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig5 forest: band & cat & season mean CATE + CI(se)
rows=[]
for nm,g in d.groupby("price_band_cat"):
    rows.append(["价位段",nm,g["CATE"].mean(),g["CATE"].std()/math.sqrt(len(g)),len(g)])
for nm,g in d.groupby("cat"):
    rows.append(["品类",nm,g["CATE"].mean(),g["CATE"].std()/math.sqrt(len(g)),len(g)])
for nm,g in d.groupby("season"):
    rows.append(["时令",nm,g["CATE"].mean(),g["CATE"].std()/math.sqrt(len(g)),len(g)])
fr=pd.DataFrame(rows,columns=["k","name","mean","se","n"])
order=["价位段","品类","时令"]
fig,ax=plt.subplots(figsize=(6.8,3.8),dpi=200)
ypos=0; yt=[]; yl=[]
for k in order:
    sub=fr[fr["k"]==k]
    for _,r in sub.iterrows():
        ypos-=1; yt.append(ypos)
        c=PRIMARY if k=="价位段" else SECOND if k=="品类" else LIGHT
        ax.plot([r["mean"]-1.96*r["se"],r["mean"]+1.96*r["se"]],[ypos,ypos],color=c,lw=1.6)
        ax.plot(r["mean"],ypos,"o",color=c,ms=5)
        yl.append(f"{r['name']}  {r['mean']:.2f}({r['n']})")
    if k!=order[-1]:
        ypos-=0.6
ax.axvline(0,color=GREY,ls=":",lw=1)
ax.set_yticks(yt); ax.set_yticklabels(yl,fontsize=8)
ax.set_xlabel("平均 CATE（±95%CI）/ 分")
style(ax); ax.set_title("图5  价位段、品类与时令子组CATE森林图",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig5_subgroup_forest.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig6 heatmap band x sensitivity
piv=d.pivot_table(index="band_o",columns="sensitivity",values="CATE",aggfunc="mean")
piv=piv.sort_index()
fig,ax=plt.subplots(figsize=(5.6,3.2),dpi=200)
im=ax.imshow(piv.values,cmap="RdYlBu_r",aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(piv.columns,fontsize=8)
ax.set_yticks(range(len(piv))); ax.set_yticklabels([BMAP.get(i,"") for i in piv.index],fontsize=8)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        ax.text(j,i,f"{piv.values[i,j]:.1f}",ha="center",va="center",fontsize=8,
                color="white" if abs(piv.values[i,j])>np.nanmax(np.abs(piv.values))/1.5 else "black")
ax.set_xlabel("敏感组",fontsize=8); ax.set_ylabel("价位段",fontsize=8)
fig.colorbar(im,ax=ax,shrink=.8).set_label("平均 CATE / 分",fontsize=8)
ax.set_title("图6  价位段×敏感组平均CATE热力图",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig6_priceband_heatmap.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig7 representative high-sens spec trajectory
traj=d[d["name"]== (rep_high[0]["name"] if rep_high else d['name'].iloc[0])].sort_values("ym") if rep_high else d.head(20)
spec=traj["name"].iloc[0]
t0=d[d["name"]==spec].sort_values("ym").iloc[0]["ym"]
ev=traj[traj["T"]==1]["ym"].tolist()
fig,ax=plt.subplots(figsize=(6.6,3.3),dpi=200)
ax.plot(range(len(traj)),traj["S"].values,color=PRIMARY,lw=1.8,marker="o",ms=3,label=f"{spec} 的状态评分S")
for e in ev:
    ei=[i for i,y in enumerate(traj["ym"]) if y==e]
    for k in ei:
        ax.axvline(k,color=ACCENT,ls="--",lw=1.2,alpha=.8)
        ax.annotate("缩投",(k,traj["S"].values[k]),xytext=(k,traj["S"].values[k]-6),fontsize=7,color=ACCENT,ha="center")
ax.set_ylabel("状态评分 S / 分"); ax.set_xlabel("月份顺序")
style(ax); ax.legend(fontsize=7,frameon=False); ax.set_title(f"图7  高敏感代表品规「{spec}」月度状态轨迹",fontsize=10,pad=6)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig7_trajectory.png"),dpi=200,bbox_inches="tight"); plt.close()

# fig8 multi-spec grid
names=[r["name"] for r in rep_high]+[r["name"] for r in rep_low]
fig,axes=plt.subplots(2,2,figsize=(6.8,5.2),dpi=200)
names8=names[:4]
for ax,nm in zip(axes.ravel(),names8):
    g=d[d["name"]==nm].sort_values("ym")
    ax.plot(range(len(g)),g["S"].values,color=SECOND,lw=1.6)
    for e,k in zip(g["ym"].tolist(),range(len(g))):
        if g["T"].values[k]==1:
            ax.axvline(k,color=ACCENT,ls="--",lw=1)
    ax.set_title(nm,fontsize=8); style(ax)
    ax.set_ylabel("S",fontsize=8)
fig.suptitle("图8  代表性品规月度状态轨迹与缩投事件对照（实线=S评分，红虚=缩投月）",fontsize=10,y=1.0)
plt.tight_layout(); plt.savefig(os.path.join(FOUT,"fig8_product_panel.png"),dpi=200,bbox_inches="tight"); plt.close()
print("figures saved to",FOUT)