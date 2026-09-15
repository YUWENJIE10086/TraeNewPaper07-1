# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "v20_4_实际品规案例明细.csv"
FIG = ROOT.parent / "figures"
FIG.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
mpl.rcParams["font.family"] = "AR PL SungtiL GB"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "path"

# 图6：模型排序与下一期实际变化的一致性/偏离
tmp = df.sort_values("CATE").reset_index(drop=True)
cate_z = (tmp["CATE"] - tmp["CATE"].mean()) / tmp["CATE"].std(ddof=0)
out_z = (tmp["下期变化"] - tmp["下期变化"].mean()) / tmp["下期变化"].std(ddof=0)
fig, ax = plt.subplots(figsize=(11.2, 7.6))
y = np.arange(len(tmp))
for yi, a, b in zip(y, cate_z, out_z):
    ax.plot([a,b], [yi,yi], lw=1.6, alpha=.55)
ax.scatter(cate_z, y, s=72, label="CATE（标准化）")
ax.scatter(out_z, y, s=72, label="下一期实际变化（标准化）")
ax.axvline(0, lw=1)
ax.set_yticks(y, tmp["品规"])
ax.set_xlabel("标准化位置")
ax.set_title("代表性品规模型排序与下一期实际变化的一致性/偏离")
ax.legend(frameon=False)
ax.grid(axis="x", alpha=.18)
fig.savefig(FIG / "fig6_case_consistency_slope.svg", format="svg", bbox_inches="tight")
plt.close(fig)

# 图7：库存压力—状态位势—CATE联合画像
fig, ax = plt.subplots(figsize=(10.8,7.4))
x = np.log1p(df["存销比"])
y = df["供给收缩前S*"]
size = 70 + 45*np.abs(df["CATE"])
sc = ax.scatter(x, y, s=size, c=df["CATE"], alpha=.78)
for _,r in df.iterrows():
    ax.annotate(r["品规"], (np.log1p(r["存销比"]), r["供给收缩前S*"]),
                xytext=(5,5), textcoords="offset points", fontsize=8.2)
ax.set_xlabel("log(存销比)")
ax.set_ylabel("供给收缩前状态 S*")
ax.set_title("代表性品规的库存压力—状态位势—CATE联合画像")
fig.colorbar(sc, ax=ax, fraction=.035, pad=.02, label="CATE")
ax.grid(alpha=.18)
fig.savefig(FIG / "fig7_inventory_state_map.svg", format="svg", bbox_inches="tight")
plt.close(fig)
