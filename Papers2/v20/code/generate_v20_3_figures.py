# -*- coding: utf-8 -*-
"""
v20-3 全新高级图生图脚本
数据来源：论文 v18 表16/17 的可追溯代表性品规案例。
注意：
1) “月份”表示论文中按代理规则识别的供给收缩事件月份，并非真实审批日志；
2) “下一期变化”是观测事实，不是无偏因果效应；
3) 脚本不使用 v18 的旧图片，所有图均从表格数据重新生成。
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "v20_3_代表性品规真实案例数据.csv"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
mpl.rcParams["font.family"] = "AR PL SungtiL GB"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "path"

def save(fig, name):
    fig.savefig(FIG / name, format="svg", bbox_inches="tight")
    plt.close(fig)

# 图1：证据链框图
fig, ax = plt.subplots(figsize=(12, 5.7))
ax.set_axis_off()
steps = [
    ("业务输入", "品规×月份面板\n价格·库存·动销·渠道"),
    ("处理前画像", "t−1期特征\n避免处理后信息泄漏"),
    ("响应估计", "诚实因果森林\n品规分组交叉拟合"),
    ("可信约束", "共同支持\n排序稳定性\n负对照"),
    ("业务复核", "优先复核\n观察复核\n暂缓收缩"),
]
xpos = np.linspace(0.08, 0.92, len(steps))
for i, ((title, body), x) in enumerate(zip(steps, xpos)):
    ax.text(x, 0.63, title, ha="center", va="center", fontsize=13, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.55", alpha=0.12))
    ax.text(x, 0.43, body, ha="center", va="center", fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.55", alpha=0.06))
    if i < len(steps)-1:
        ax.annotate("", xy=(xpos[i+1]-0.07, 0.53), xytext=(x+0.07, 0.53),
                    arrowprops=dict(arrowstyle="->", lw=1.6))
ax.text(0.5, 0.19, "证据边界：代理收缩事件 ≠ 随机处理；模型输出用于复核排序，不直接给出减量幅度",
        ha="center", va="center", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.55", alpha=0.08))
ax.set_title("卷烟品规供给收缩差异化复核：证据链与业务链总体设计", fontsize=16, pad=18)
save(fig, "fig1_evidence_chain.svg")

# 图2：CATE—实际变化四象限气泡图
fig, ax = plt.subplots(figsize=(10.5, 7.2))
sizes = 70 + 180 * (np.log1p(df["存销比"]) - np.log1p(df["存销比"]).min()) / (
    np.log1p(df["存销比"]).max() - np.log1p(df["存销比"]).min()
)
for grp, g in df.groupby("排序组"):
    ax.scatter(g["CATE"], g["下期变化"], s=sizes.loc[g.index], alpha=0.72, label=grp)
for _, r in df.iterrows():
    ax.annotate(r["品规"], (r["CATE"], r["下期变化"]), xytext=(5,5),
                textcoords="offset points", fontsize=8.5)
ax.axvline(0, lw=1); ax.axhline(0, lw=1)
ax.set_xlabel("CATE 排序信号"); ax.set_ylabel("下一期实际状态变化")
ax.set_title("代表性品规的模型排序与下一期实际状态变化")
ax.legend(frameon=False); ax.grid(alpha=0.18)
save(fig, "fig2_cate_outcome_quadrant.svg")

# 图3：经营画像证据矩阵
cols = ["供给收缩前S*","顺价指数","存销比","CATE","下期变化"]
M = df[cols].copy()
M["存销比"] = np.log1p(M["存销比"])
Z = (M - M.mean()) / M.std(ddof=0)
fig, ax = plt.subplots(figsize=(11.2, 7.4))
im = ax.imshow(Z.values, aspect="auto")
ax.set_xticks(range(len(cols)), ["处理前S*","顺价指数","log(存销比)","CATE","下一期变化"])
ax.set_yticks(range(len(df)), df["品规"])
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        ax.text(j, i, f"{Z.iloc[i,j]:.1f}", ha="center", va="center", fontsize=8)
ax.set_title("代表性品规经营画像—排序—结果的标准化证据矩阵")
fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label="标准化值（z-score）")
save(fig, "fig3_profile_evidence_matrix.svg")

# 图4：代理收缩事件时间线
tmp = df.copy()
tmp["日期"] = pd.to_datetime(tmp["月份"].astype(str) + "01", format="%Y%m%d")
tmp = tmp.sort_values(["日期","CATE"])
fig, ax = plt.subplots(figsize=(11.5, 6.8))
y = np.arange(len(tmp))
ax.hlines(y=y, xmin=tmp["日期"].min()-pd.Timedelta(days=20), xmax=tmp["日期"], lw=1.3, alpha=0.5)
ax.scatter(tmp["日期"], y, s=65 + 18*np.abs(tmp["CATE"]), alpha=0.78)
for yi, (_, r) in enumerate(tmp.iterrows()):
    ax.text(r["日期"] + pd.Timedelta(days=8), yi,
            f'{r["品规"]}  CATE={r["CATE"]:.2f}  Δ={r["下期变化"]:.2f}',
            va="center", fontsize=8.5)
ax.set_yticks(y, [d.strftime("%Y-%m") for d in tmp["日期"]])
ax.set_xlabel("代理供给收缩事件月份"); ax.set_ylabel("事件月份")
ax.set_title("10个代表性品规的代理收缩事件与后续状态变化时间线")
ax.grid(axis="x", alpha=0.18)
save(fig, "fig4_event_timeline.svg")

# 图5：状态位势—响应排序哑铃图
tmp = df.sort_values("CATE")
s = (tmp["供给收缩前S*"] - tmp["供给收缩前S*"].mean()) / tmp["供给收缩前S*"].std(ddof=0)
c = (tmp["CATE"] - tmp["CATE"].mean()) / tmp["CATE"].std(ddof=0)
fig, ax = plt.subplots(figsize=(10.5, 7.2))
y = np.arange(len(tmp))
for yi, a, b in zip(y, s, c):
    ax.plot([a,b],[yi,yi], lw=1.8, alpha=0.65)
ax.scatter(s, y, s=65, label="处理前状态S*（标准化）")
ax.scatter(c, y, s=65, label="CATE（标准化）")
ax.axvline(0, lw=1)
ax.set_yticks(y, tmp["品规"])
ax.set_xlabel("标准化位置")
ax.set_title("代表性品规：处理前状态位势与响应排序的错位/一致关系")
ax.legend(frameon=False); ax.grid(axis="x", alpha=0.18)
save(fig, "fig5_state_cate_dumbbell.svg")

print("Done:", FIG)
