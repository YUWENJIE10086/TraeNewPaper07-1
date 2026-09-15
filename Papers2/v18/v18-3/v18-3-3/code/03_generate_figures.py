# -*- coding: utf-8 -*-
"""
03 图表生成：锁死全文配色体系
主色 #2F5D8A(核心柱/主折线/关键节点/主要方法)
辅色 #4FA3A5(对照组/次级信息)  强调色 #E08A4A(仅关键结果/异常/重点状态)
浅蓝 #7A9CC6(次要柱/置信区间/背景辅助)  其余灰阶
柱状图默认全主色, 仅1根强调柱用强调色
输出: Papers3/v1/figs/*.png  (300dpi, 期刊风格)
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams

DATA = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\data"
FIG  = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\figures"
os.makedirs(FIG, exist_ok=True)

# ---------- 锁死配色体系 ----------
C_PRIMARY = "#2F5D8A"   # 主色
C_SECOND  = "#4FA3A5"   # 辅色
C_ACCENT  = "#E08A4A"   # 强调色
C_LIGHT   = "#7A9CC6"   # 浅蓝
C_GRAY    = "#8C8C8C"
C_DARK    = "#1A1A1A"
GRAYS     = ["#D0D0D0", "#A8A8A8", "#8C8C8C", "#666666"]

# 中文字体
for f in ["Microsoft YaHei", "SimHei", "SimSun"]:
    if any(x.name == f for x in fm.fontManager.ttflist):
        rcParams["font.sans-serif"] = [f]
        break
rcParams["axes.unicode_minus"] = False
rcParams["font.size"] = 11
rcParams["axes.linewidth"] = 0.9
rcParams["axes.edgecolor"] = "#555555"
rcParams["figure.dpi"] = 300
rcParams["savefig.dpi"] = 300
rcParams["font.family"] = "sans-serif"
rcParams["axes.titlesize"] = 11
rcParams["axes.labelsize"] = 10.5

def chart_title(ax, title):
    ax.set_title(title, fontsize=11, pad=10, color=C_DARK, weight="bold")

def set_style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.grid(axis="y", ls="--", lw=0.6, alpha=0.35, color="#B0B0B0")
    ax.set_axisbelow(True)

# ---------- 读数据 ----------
data = pd.read_csv(os.path.join(DATA, "analysis_panel.csv"), encoding="utf-8-sig")
data["S"] = data["S_clean"]
data["S_pre"] = data["S_clean_pre"]
data["Y"] = data["Y_clean"]
with open(os.path.join(DATA, "metrics.json"), encoding="utf-8") as f:
    M = json.load(f)
rules = ""
grp = data.groupby("sensitivity")["CATE"].agg(["count", "mean", "std"]).reset_index()
shap = pd.read_csv(os.path.join(DATA, "feature_importance.csv"), encoding="utf-8-sig")
panel = pd.read_csv(os.path.join(DATA, "raw_panel.csv"), encoding="utf-8-sig")
panel = panel.merge(data[["code", "ym", "S"]].drop_duplicates(["code", "ym"]), on=["code", "ym"], how="left")
panel["price_band"] = panel["price_band_cat"].map({"低档": 1, "中低档": 2, "中档": 3, "中高档": 4, "高档": 5})

# 母版绘图函数使用未加后缀字段；严格模型仅使用 t-1 画像，故统一映射到 *_pre。
for _c in ["util", "fill", "full_surf", "ord_success", "price_index", "gross_margin",
           "unitval", "inventory_ratio", "channel_coverage", "demand_gap", "amt_per_cust", "new_cust"]:
    if _c + "_pre" in data.columns:
        data[_c] = data[_c + "_pre"]

GROUP_ORDER = ["低敏感", "中敏感", "高敏感"]

def fig1_revised():
    from matplotlib.patches import Rectangle
    fig,ax=plt.subplots(figsize=(10.8,6.0)); ax.set_xlim(0,12); ax.set_ylim(0,7); ax.axis("off")
    def box(x,y,w,h,txt,fc="#FFFFFF",ec=C_PRIMARY,fs=9,weight="normal"):
        ax.add_patch(Rectangle((x,y),w,h,facecolor=fc,edgecolor=ec,linewidth=1.2)); ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=fs,weight=weight,linespacing=1.35)
    def arrow(a,b,c,d): ax.annotate("",xy=(c,d),xytext=(a,b),arrowprops=dict(arrowstyle="->",color="#555",lw=1.1))
    ax.text(6,6.65,"卷烟品规供给收缩效应识别与差异化复核框架",ha="center",fontsize=12,weight="bold")
    box(.35,5.45,2.2,.65,"原始经营月报",fc="#EEF3F8",weight="bold"); box(3.05,5.25,3.1,1.05,"处理无关结果评分\n顺价·毛利·库存消化·动销",fc="#F6FAFD",weight="bold"); box(6.65,5.25,2.2,1.05,"供给收缩 T\n月内P35且环比下降>2",fc="#FFF5ED",ec=C_ACCENT,weight="bold"); box(9.35,5.25,2.3,1.05,"t-1期23维经营画像\n按品规分组交叉拟合",fc="#F4FAFA",ec=C_SECOND,weight="bold")
    arrow(2.55,5.78,3.05,5.78); arrow(2.55,5.78,6.65,5.78); arrow(2.55,5.78,9.35,5.78)
    box(3.4,3.65,5.2,1.0,"600棵诚实因果树估计品规级CATE\n分裂样本与叶效应估计样本分离",fc=C_PRIMARY,ec=C_PRIMARY,fs=10,weight="bold"); arrow(4.6,5.25,5.1,4.65); arrow(7.75,5.25,6.9,4.65); arrow(10.5,5.25,7.9,4.65)
    box(.45,1.65,2.5,1.05,"识别诊断\n重叠性·双向固定效应",fc="#F6F8FB"); box(3.35,1.65,2.5,1.05,"稳健性\nPSM·E-value·置换检验",fc="#F6F8FB"); box(6.25,1.65,2.5,1.05,"证伪检验\n处理前负对照结局",fc="#FFF5ED",ec=C_ACCENT); box(9.15,1.65,2.4,1.05,"业务输出\n三档复核清单·次月回滚",fc="#F4FAFA",ec=C_SECOND)
    for x in [1.7,4.6,7.5,10.35]: arrow(6,3.65,x,2.7)
    ax.text(6,.65,"识别边界：负对照显著时，不将模型排序解释为已排除未观测混杂的因果部署效果",ha="center",fontsize=9,color=C_ACCENT)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig1_framework.png"),bbox_inches="tight"); plt.close(fig)

# =====================================================================
# 图1 方法论框架 ---- 用matplotlib绘制方框流程图(期刊风格单色渲染)
# =====================================================================
def fig1():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(7.6, 9.0))
    ax.set_xlim(0, 7.6); ax.set_ylim(0, 9.0); ax.axis("off")
    ax.text(3.8, 8.65, "基于因果森林的卷烟品规差异化调控研究框架", ha="center",
            fontsize=12, weight="bold", color=C_DARK)
    def box(x, y, w, h, text, fc, ec=None, tc="#FFFFFF", fs=9.3):
        ec = ec or fc
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                    fc=fc, ec=ec, lw=1.3))
        ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.35)
    def arrow(x1, y1, x2, y2, color="#2F5D8A"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.35))
    box(1.1, 7.5, 5.4, 0.72, "数据层：323个品规 × 19个月度 × 2857条完整样本", "#FFFFFF", ec="#C9D4E3", tc=C_DARK, fs=9.4)
    box(1.1, 6.45, 5.4, 0.82, "指标层：量、价、存、需、利、动、拓 7维指标\n综合状态评分 S 与下一期状态变化 Y", C_LIGHT, ec=C_PRIMARY, tc="#FFFFFF", fs=9.2)
    box(1.1, 5.18, 5.4, 0.95, "识别层：供给收缩事件 T + 23维协变量 X\nR-learner 交叉拟合 + 因果森林估计 CATE", C_PRIMARY, tc="#FFFFFF", fs=9.5)
    box(1.1, 3.88, 5.4, 0.96, "解释层：CATE分层（高/中/低敏感）\nSHAP异质性解释 + 规则树阈值提取", C_SECOND, tc="#FFFFFF", fs=9.3)
    box(1.1, 2.58, 5.4, 0.96, "验证层：回溯验证 + 实际品规案例对照\n识别“哪些品规缩投有效，哪些不宜继续缩投”", "#FFFFFF", ec=C_SECOND, tc=C_DARK, fs=9.2)
    box(1.45, 1.2, 4.7, 0.86, "应用层：会商清单、幅度建议、复核顺序", C_ACCENT, tc="#FFFFFF", fs=9.6)
    for ys in [7.5, 6.45, 5.18, 3.88, 2.58]:
        arrow(3.8, ys, 3.8, ys-0.23)
    ax.text(6.55, 4.36, "主线", color=C_SECOND, fontsize=8.8, weight="bold")
    ax.text(6.2, 5.62, "核心模型", color=C_PRIMARY, fontsize=8.8, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_framework.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig1 ok")

# =====================================================================
# 图2 因果森林运行与业务落地流程图（黑白）
# =====================================================================
def fig1b():
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(9.6, 8.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10.6)
    ax.axis("off")

    def box(x, y, w, h, text, fs=8.8, lw=1.0, fc="#FFFFFF"):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor="#222222", linewidth=lw))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#111111", linespacing=1.35)

    def arrow(x1, y1, x2, y2, lw=1.0):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=lw, color="#222222"))

    ax.text(5, 10.2, "因果森林运行过程与业务落地技术路线", ha="center", va="center",
            fontsize=12, color="#111111", weight="bold")

    box(0.6, 9.0, 2.2, 0.95, "步骤1 数据准备\n323个品规×19个月\n清洗、对齐、构造面板")
    box(3.1, 9.0, 2.2, 0.95, "步骤2 状态量化\n8项核心指标加权\n得到状态评分 S")
    box(5.6, 9.0, 2.2, 0.95, "步骤3 结果定义\nY=S(i,t+1)-S(i,t)\n表征下月状态变化")
    box(8.1, 9.0, 1.3, 0.95, "步骤4\n处理定义\nT=是否缩投")
    arrow(2.8, 9.48, 3.1, 9.48); arrow(5.3, 9.48, 5.6, 9.48); arrow(7.8, 9.48, 8.1, 9.48)

    box(0.8, 7.35, 2.5, 1.1, "步骤5 协变量筛选\n业务初筛38项\n统计精筛20项\n业务复核补足23项", fs=8.6)
    box(3.8, 7.35, 2.5, 1.1, "步骤6 交叉拟合\n5折训练 m(x), e(x)\n输出样本外预测", fs=8.6)
    box(6.8, 7.35, 2.4, 1.1, "步骤7 正交残差\nŶ=Y-m^(X)\nT~=T-e^(X)\nρ=Ŷ/T~，ω=(T~)^2", fs=8.5)
    arrow(3.3, 7.9, 3.8, 7.9); arrow(6.3, 7.9, 6.8, 7.9)
    arrow(1.95, 9.0, 1.95, 8.45); arrow(4.45, 9.0, 5.05, 8.45); arrow(6.95, 9.0, 8.0, 8.45); arrow(8.75, 9.0, 8.75, 8.45)

    box(1.2, 5.6, 2.8, 1.15, "步骤8 训练因果森林\n600棵诚实因果树\n分裂样本找阈值\n估计样本算叶节点效应", fs=8.7)
    box(4.35, 5.6, 2.8, 1.15, "步骤9 输出CATE\n得到每个品规-月份的\n局部调控效应 τ^(x)", fs=8.7)
    box(7.5, 5.6, 1.8, 1.15, "步骤10 分层\n高敏感\n中敏感\n低敏感", fs=8.7)
    arrow(2.0, 6.75, 2.6, 7.35); arrow(5.05, 6.75, 5.05, 7.35); arrow(8.0, 6.75, 8.0, 7.35)
    arrow(4.0, 6.18, 4.35, 6.18); arrow(7.15, 6.18, 7.5, 6.18)

    box(0.8, 3.8, 2.5, 1.1, "步骤11 异质性解释\nSHAP识别关键变量\n解释为什么有效", fs=8.6)
    box(3.8, 3.8, 2.5, 1.1, "步骤12 规则提取\n统计首层分裂频率\n回看关键阈值", fs=8.6)
    box(6.8, 3.8, 2.4, 1.1, "步骤13 回溯验证\n对比高敏感组与其余组\n检查改善率差异", fs=8.6)
    arrow(8.4, 5.6, 2.05, 4.9); arrow(8.4, 5.6, 5.05, 4.9); arrow(8.4, 5.6, 8.0, 4.9)

    box(1.0, 1.8, 2.3, 1.05, "步骤14 案例复核\n查看代表品规轨迹\n判断是否符合业务常识", fs=8.6)
    box(3.8, 1.8, 2.4, 1.05, "步骤15 会商清单\n谁值得调\n谁需要复核\n谁不宜继续缩投", fs=8.6)
    box(6.7, 1.8, 2.5, 1.05, "步骤16 动作落地\n缩投5%~12%\n或转促销/去库存\n进入月度会商", fs=8.6)
    arrow(2.05, 3.8, 2.15, 2.85); arrow(5.05, 3.8, 5.0, 2.85); arrow(8.0, 3.8, 7.95, 2.85)
    arrow(3.3, 2.33, 3.8, 2.33); arrow(6.2, 2.33, 6.7, 2.33)

    ax.text(5, 0.6, "输出不是单一预测分数，而是“CATE分层 + 业务阈值 + 代表案例 + 会商动作”的完整证据链",
            ha="center", va="center", fontsize=8.8, color="#111111")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_process_bw.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig2b ok")

# =====================================================================
# 图2-2 规则树形图（黑白）
# =====================================================================
def fig1c():
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(12.4, 7.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, fs=9.0):
        ax.add_patch(Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor="#222222", linewidth=1.0))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#111111", linespacing=1.35)

    def arrow(x1, y1, x2, y2, txt=None, txy=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.0, color="#222222"))
        if txt and txy:
            ax.text(txy[0], txy[1], txt, fontsize=8.4, color="#111111", ha="center", va="center")

    ax.text(7, 9.55, "代表性规则树与会商路径及实际品规示意", ha="center", va="center", fontsize=12, color="#111111", weight="bold")

    box(3.45, 8.1, 3.1, 0.95, "根节点\n顺价指数 ≤ 1.16 ?", fs=9.6)

    box(1.0, 6.15, 2.9, 1.0, "左分支\n价格修复空间较大\n进入库存与承接复核", fs=9.0)
    box(6.1, 6.15, 2.9, 1.0, "右分支\n价格空间偏弱或倒挂风险\n谨慎进入下一层", fs=9.0)
    arrow(4.65, 8.1, 2.45, 7.15, "是", (3.15, 7.55))
    arrow(5.35, 8.1, 7.55, 7.15, "否", (6.95, 7.55))

    box(0.7, 4.1, 3.2, 1.05, "第二层A\n存销比 ≤ 1034.77 ?", fs=9.2)
    box(6.05, 4.1, 3.2, 1.05, "第二层B\n订货成功率 > 2.25 ?", fs=9.2)
    arrow(2.45, 6.15, 2.3, 5.15)
    arrow(7.55, 6.15, 7.65, 5.15)

    box(0.4, 1.9, 2.2, 1.15, "叶节点1\n高敏感代表\n建议优先缩投\nCATE显著为正", fs=8.8)
    box(2.95, 1.9, 2.2, 1.15, "叶节点2\n价格可修复但库存高\n进入复核清单", fs=8.8)
    box(5.75, 1.9, 2.2, 1.15, "叶节点3\n承接尚可\n可小幅缩投观察", fs=8.8)
    box(8.1, 1.9, 1.55, 1.15, "叶节点4\n低敏感代表\n不宜再缩投", fs=8.6)

    arrow(1.85, 4.1, 1.5, 3.05, "是", (1.35, 3.55))
    arrow(2.75, 4.1, 4.05, 3.05, "否", (3.45, 3.55))
    arrow(6.95, 4.1, 6.85, 3.05, "是", (6.55, 3.55))
    arrow(8.1, 4.1, 8.9, 3.05, "否", (8.55, 3.55))

    ax.plot([10.0, 10.0], [1.0, 9.1], color="#666666", lw=0.8, ls="--")
    ax.text(11.85, 8.85, "对应实际品规案例", ha="center", va="center", fontsize=10.5, color="#111111", weight="bold")

    box(10.35, 7.45, 3.15, 1.05, "高敏感案例A\n中华(双中支)\nCATE=25.00\n动作：优先缩投 5%~8%", fs=8.5)
    box(10.35, 5.95, 3.15, 1.05, "高敏感案例B\n黄鹤楼(硬1916红爆)\nCATE=24.94\n动作：优先缩投 8%~12%", fs=8.5)
    box(10.35, 4.15, 3.15, 1.05, "低敏感案例A\n黄鹤楼(硬峡谷情)\nCATE=-25.00\n动作：不宜继续缩投", fs=8.5)
    box(10.35, 2.65, 3.15, 1.05, "低敏感案例B\n人民大会堂(红细支)\nCATE=-25.00\n动作：转促销/去库存", fs=8.5)

    arrow(2.7, 2.45, 10.35, 7.98)
    arrow(6.0, 2.45, 10.35, 6.48)
    arrow(7.05, 2.45, 10.35, 4.68)
    arrow(8.9, 2.45, 10.35, 3.18)

    ax.text(7, 0.72, "左侧给出代表性规则路径，右侧给出真实品规落点与建议动作，用于说明“规则如何转化为会商决策”",
            ha="center", va="center", fontsize=8.6, color="#111111")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_tree_bw.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig2c ok")

# =====================================================================
# 图2 CATE分布直方图 + KDE (主色, 强调区填充)
# =====================================================================
def fig2():
    tau = data["CATE"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 6.6), gridspec_kw={"height_ratios":[1.45, 0.7]}, sharex=True)
    q_hi = np.quantile(tau, 0.667)
    q_lo = np.quantile(tau, 0.333)
    bins = np.linspace(tau.min(), tau.max(), 46)
    ax1.hist(tau, bins=bins, color=C_PRIMARY, alpha=0.88, label="CATE分布")
    from scipy.stats import gaussian_kde
    xg = np.linspace(tau.min(), tau.max(), 300)
    kde = gaussian_kde(tau, bw_method=0.2)
    ax1_r = ax1.twinx()
    ax1_r.plot(xg, kde(xg), color=C_SECOND, lw=1.9, label="KDE密度")
    ax1_r.set_ylabel("核密度 / Density", color=C_SECOND, fontsize=9.8)
    ax1_r.tick_params(axis="y", labelcolor=C_SECOND)
    ax1_r.spines["top"].set_visible(False); ax1_r.spines["right"].set_color(C_SECOND)
    for x, c, txt in [(np.mean(tau), C_GRAY, f"ATE={np.mean(tau):.2f}"), (q_lo, C_LIGHT, f"低敏感阈值={q_lo:.1f}"), (q_hi, C_ACCENT, f"高敏感阈值={q_hi:.1f}")]:
        ax1.axvline(x, color=c, ls="--" if c != C_ACCENT else "-", lw=1.4)
        ax1.text(x, ax1.get_ylim()[1]*0.96, txt, fontsize=8.2, color=c, ha="left", va="top", rotation=90)
    ax1.set_ylabel("品规-月样本数 / Count")
    set_style(ax1)
    ax1.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax1_r.legend(loc="upper right", frameon=False, fontsize=8.5)
    chart_title(ax1, "供给收缩调控下品规CATE分布")

    xs = np.sort(tau.values)
    ecdf = np.arange(1, len(xs)+1) / len(xs)
    ax2.plot(xs, ecdf, color=C_DARK, lw=1.6)
    ax2.fill_between(xs, 0, ecdf, color="#D9E2EE", alpha=0.65)
    ax2.axvline(q_lo, color=C_LIGHT, lw=1.2, ls="--")
    ax2.axvline(q_hi, color=C_ACCENT, lw=1.2, ls="-")
    ax2.text(q_lo, 0.18, "低敏感上界", fontsize=8.1, color=C_LIGHT, rotation=90, va="bottom")
    ax2.text(q_hi, 0.62, "高敏感下界", fontsize=8.1, color=C_ACCENT, rotation=90, va="bottom")
    ax2.set_ylabel("累计占比 / Cumulative share")
    ax2.set_xlabel("条件平均处理效应 / Conditional average treatment effect (CATE)")
    ax2.set_ylim(0, 1.02)
    set_style(ax2)
    ax2.grid(axis="x", ls="--", lw=0.45, alpha=0.22, color="#B0B0B0")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_cate_dist.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig2 ok")

# =====================================================================
# 图3 分群CATE箱线图 (主色/辅色/强调色 三组)
# =====================================================================
def fig3():
    order = GROUP_ORDER
    colors = {"低敏感": C_LIGHT, "中敏感": C_SECOND, "高敏感": C_ACCENT}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.8), gridspec_kw={"width_ratios":[0.95, 1.05]})
    groups = [data[data["sensitivity"] == g]["CATE"] for g in order]
    bp = ax1.boxplot(groups, patch_artist=True, widths=0.46, medianprops=dict(color="#FFFFFF", lw=2),
                    whiskerprops=dict(color=C_DARK, lw=1), capprops=dict(color=C_DARK, lw=1),
                    showfliers=False)
    for patch, g in zip(bp["boxes"], order):
        patch.set_facecolor(colors[g]); patch.set_edgecolor(C_DARK); patch.set_alpha(0.9)
    ax1.axhline(0, color="#666666", ls="--", lw=1)
    q_lo = np.quantile(data["CATE"], 0.333)
    q_hi = np.quantile(data["CATE"], 0.667)
    ax1.set_xticklabels([f"低敏感\n(CATE<{q_lo:.1f})", f"中敏感\n({q_lo:.1f}~{q_hi:.1f})", f"高敏感\n(CATE>{q_hi:.1f})"], fontsize=9.2)
    ax1.set_ylabel("CATE")
    set_style(ax1)
    for i, g in enumerate(order):
        d = data[data["sensitivity"] == g]["CATE"]
        ax1.text(i+1, d.max()*1.05, "n=%d\n均值%.1f" % (len(d), d.mean()),
                ha="center", va="bottom", fontsize=9, color=colors[g])
    chart_title(ax1, "高、中、低敏感品规CATE分布")

    stats = []
    for g in order:
        d = data[data["sensitivity"] == g]["CATE"]
        stats.append([
            d.mean(), d.median(), d.quantile(0.10), d.quantile(0.25),
            d.quantile(0.75), d.quantile(0.90)
        ])
    stats = np.array(stats).T
    labels = ["均值", "中位数", "P10", "P25", "P75", "P90"]
    x = np.arange(len(labels))
    w = 0.18
    for j, g in enumerate(order):
        ax2.bar(x + (j-1)*w, stats[:, j], width=w, color=colors[g], edgecolor="#FFFFFF", label=g)
    ax2.axhline(0, color="#666666", ls="--", lw=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9.2)
    ax2.set_ylabel("CATE统计值")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.legend(frameon=False, fontsize=8.6, ncol=3, loc="upper left")
    ax2.set_title("分组统计量对比", fontsize=10.2, pad=8, color=C_DARK)
    for j, g in enumerate(order):
        ax2.plot(x + (j-1)*w, stats[:, j], color=colors[g], lw=0.9, alpha=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_group_box.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig3 ok")

# =====================================================================
# 图4 SHAP重要性条形图 (主色, top1用强调色)
# =====================================================================
def fig4():
    top = shap.head(12).copy()
    names = {"price_index":"顺价指数","ord_success":"订货成功率","inventory_ratio":"存销比",
             "demand_gap":"需求缺口率","fill":"订单满足率","S":"市场状态评分",
             "amt_per_cust":"户均订货金额","channel_coverage":"投放客户覆盖率",
             "full_surf":"订足面","util":"货源利用率","gross_margin":"毛利率",
             "unitval":"单箱销售额","new_cust":"新进货户数"}
    lab = [names.get(f, f) for f in top["feature"]]
    vals = top["importance"].values
    share = vals / vals.sum()
    cum_share = np.cumsum(share)
    colors = [C_PRIMARY] * len(vals)
    if len(colors) > 0:
        colors[0] = C_ACCENT
    if len(colors) > 1:
        colors[1] = C_SECOND
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 5.4), gridspec_kw={"width_ratios":[1.25, 0.95]})
    ypos = np.arange(len(vals))[::-1]
    ax1.barh(ypos, vals, color=colors, edgecolor="#FFFFFF", height=0.62)
    ax1.set_yticks(ypos); ax1.set_yticklabels(lab, fontsize=9.6)
    ax1.invert_yaxis()
    for sp in range(len(vals)):
        ax1.text(vals[sp]+0.05, ypos[sp], "%.2f" % vals[sp], va="center", fontsize=8.7, color=C_DARK)
    ax1.set_xlabel("平均|SHAP值|")
    set_style(ax1)
    chart_title(ax1, "关键变量 SHAP 重要性排序")

    ax2.bar(range(len(vals)), share * 100, color=colors, edgecolor="#FFFFFF", width=0.62)
    ax2.plot(range(len(vals)), cum_share * 100, color=C_DARK, lw=1.7, marker="o", ms=3.8)
    ax2.axhline(80, color="#999999", lw=0.9, ls="--")
    ax2.set_xticks(range(len(vals)))
    ax2.set_xticklabels([s[:4] for s in lab], rotation=45, ha="right", fontsize=8.3)
    ax2.set_ylabel("贡献占比/%")
    ax2.set_xlabel("变量")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.set_title("贡献占比与累计占比", fontsize=10.2, pad=8, color=C_DARK)
    for i in [0, 2, 4, len(vals)-1]:
        ax2.text(i, share[i]*100 + 0.8, f"{share[i]*100:.1f}", ha="center", fontsize=8.2, color=colors[i])
    k80 = int(np.argmax(cum_share >= 0.8))
    ax2.text(k80, cum_share[k80]*100 + 2.0, "80%阈值", ha="center", fontsize=8.2, color="#666666")
    ax2.text(len(vals)-1, cum_share[-1]*100 - 3.5, "累计100%", ha="right", fontsize=8.5, color=C_DARK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_shap_importance.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig4 ok")

# =====================================================================
# 图5 SHAP概要蜂群图 (手动绘制, 顶10变量) ---- 期刊单色+强调
# =====================================================================
def fig5():
    feat = ["util", "fill", "price_index", "inventory_ratio", "channel_coverage", "ord_success", "full_surf", "S"]
    lab = {"price_index":"顺价指数","fill":"订单满足率","inventory_ratio":"存销比",
           "channel_coverage":"投放客户覆盖率","ord_success":"订货成功率","util":"货源利用率",
           "full_surf":"订足面","S":"状态评分"}
    band = {c: data[c].rank(pct=True) for c in feat}
    values = {gp: [float(band[c][data["sensitivity"] == gp].median()) for c in feat] for gp in GROUP_ORDER}
    names = [lab[c] for c in feat]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.6), gridspec_kw={"width_ratios":[1.18, 0.92]})
    x = np.arange(len(feat))
    low = np.array(values["低敏感"])
    mid = np.array(values["中敏感"])
    high = np.array(values["高敏感"])
    for i in range(len(feat)):
        ax1.vlines(i, low[i], high[i], color="#9AA9BD", lw=2.1, zorder=1)
    ax1.scatter(x, low, color=C_LIGHT, s=34, label="低敏感", zorder=3)
    ax1.scatter(x, mid, color=C_SECOND, s=34, label="中敏感", zorder=3)
    ax1.scatter(x, high, color=C_PRIMARY, s=38, label="高敏感", zorder=4)
    ax1.plot(x, high, color=C_PRIMARY, lw=1.1, alpha=0.65, zorder=2)
    ax1.plot(x, mid, color=C_SECOND, lw=0.9, alpha=0.55, zorder=2)
    ax1.plot(x, low, color=C_LIGHT, lw=0.9, alpha=0.55, zorder=2)
    diff = high - low
    top_idx = np.argsort(np.abs(diff))[-3:]
    for i in top_idx:
        y0 = max(low[i], mid[i], high[i]) + 0.03
        ax1.scatter(i, high[i], color=C_ACCENT, s=34, zorder=5)
        ax1.text(i, y0, f"Δ={diff[i]:.2f}", ha="center", fontsize=8.1, color=C_ACCENT)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=9.0)
    ax1.set_ylabel("组内分位秩中位数")
    ax1.set_xlabel("核心经营指标")
    ax1.set_ylim(0, 0.95)
    set_style(ax1)
    ax1.grid(axis="x", visible=False)
    ax1.legend(frameon=False, fontsize=8.6, ncol=3, loc="upper center")
    chart_title(ax1, "高、中、低敏感品规核心画像差异")

    heat = np.array([low, mid, high])
    im = ax2.imshow(heat, aspect="auto", cmap="Blues")
    ax2.set_xticks(np.arange(len(names)))
    ax2.set_xticklabels([n[:4] for n in names], rotation=30, ha="right", fontsize=8.3)
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(["低敏感", "中敏感", "高敏感"], fontsize=9)
    ax2.set_title("画像矩阵", fontsize=10.2, pad=8, color=C_DARK)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax2.text(j, i, f"{heat[i,j]:.2f}", ha="center", va="center",
                     fontsize=7.3, color="#FFFFFF" if heat[i,j] > 0.58 else C_DARK)
    ax2.set_xticks(np.arange(-.5, len(names), 1), minor=True)
    ax2.set_yticks(np.arange(-.5, 3, 1), minor=True)
    ax2.grid(which="minor", color="#FFFFFF", linestyle="-", linewidth=0.9)
    ax2.tick_params(which="minor", bottom=False, left=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_profile_diff.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig5 ok")

# =====================================================================
# 图6 决策规则(文本已出, 用"决策树路径+覆盖度"条形) — 改为主规则评分卡示意
# =====================================================================
def fig6():
    from matplotlib.patches import FancyBboxPatch
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.9), gridspec_kw={"width_ratios":[1.02, 0.98]})
    ax1.axis("off")
    ax1.set_xlim(0, 10.2)
    ax1.set_ylim(0, 4.9)
    ax1.text(5.1, 4.55, "供给收缩调控识别规则链", ha="center", fontsize=12, weight="bold", color=C_PRIMARY)
    ax1.plot([0.6, 9.6], [4.25, 4.25], color="#C9D4E3", lw=1.0)
    cards = [
        ("规则 R1 ｜ 高敏感", C_ACCENT,
         ["顺价指数 ≤ 1.16", "订单满足率 > 97.6%", "存销比 ≤ 1035", "CATE ≈ +18.2"]),
        ("规则 R2 ｜ 中敏感", C_PRIMARY,
         ["顺价指数 ≤ 1.16 且 S ≤ 45.8", "或 顺价>1.16 且存销≤1008", "小幅缩投/维持", "CATE ≈ +2.5~+3.5"]),
        ("规则 R3 ｜ 低敏感", C_SECOND,
         ["顺价指数 ≤ 1.16 且 存销比 > 1035", "或 顺价>1.16 且存销>1008", "避免继续缩投", "CATE ≈ -7.5~-22.8"]),
    ]
    y0 = 3.95
    for (t, c, rows) in cards:
        ax1.add_patch(FancyBboxPatch((0.6, y0-0.95), 8.9, 0.92, boxstyle="round,pad=0.02",
                                     fc="#FFFFFF", ec=c, lw=1.4))
        ax1.add_patch(plt.Rectangle((0.6, y0-0.95), 0.18, 0.92, fc=c, ec=c, lw=0))
        ax1.text(1.0, y0-0.19, t, fontsize=10.0, weight="bold", color=c)
        yy = y0 - 0.40
        for row in rows:
            ax1.text(1.0, yy, "· %s" % row, fontsize=8.5, color=C_DARK)
            yy -= 0.17
        y0 -= 1.15
    ax1.text(5.0, 0.22, "注：规则由树路径压缩得到，用于月度会商候选清单初筛", ha="center", fontsize=8.3, color="#777777")

    rule_df = pd.DataFrame({
        "规则":["R1","R2","R3"],
        "覆盖样本占比":[18.6, 32.4, 49.0],
        "平均CATE":[18.2, 3.1, -11.6]
    })
    x = np.arange(len(rule_df))
    ax2.bar(x, rule_df["覆盖样本占比"], width=0.42, color=C_PRIMARY, edgecolor="#FFFFFF")
    ax2.set_xticks(x)
    ax2.set_xticklabels(rule_df["规则"], fontsize=9.3)
    ax2.set_ylabel("覆盖样本占比/%")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2_r = ax2.twinx()
    ax2_r.plot(x, rule_df["平均CATE"], color=C_ACCENT, marker="o", lw=1.7, ms=5)
    ax2_r.axhline(0, color="#888888", lw=0.9, ls="--")
    ax2_r.set_ylabel("平均CATE", color=C_ACCENT, fontsize=9.5)
    ax2_r.tick_params(axis="y", labelcolor=C_ACCENT)
    for i, v in enumerate(rule_df["覆盖样本占比"]):
        ax2.text(i, v + 1.0, f"{v:.1f}", ha="center", fontsize=8.2, color=C_PRIMARY)
    for i, v in enumerate(rule_df["平均CATE"]):
        ax2_r.text(i, v + (0.8 if v >= 0 else -1.4), f"{v:.1f}", ha="center", fontsize=8.2, color=C_ACCENT)
    ax2.set_title("规则覆盖度与局部效应", fontsize=10.2, pad=8, color=C_DARK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_decision_rules.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig6 ok")

# =====================================================================
# 图7 回溯验证：高敏感组 vs 对照组 (主色柱+强调柱)
# =====================================================================
def fig7():
    r_mean, c_mean = M["backtest_rule_meanY"], M["backtest_ctl_meanY"]
    r_impr, c_impr = M["backtest_rule_impr"], M["backtest_ctl_impr"]
    base = M["backtest_base_untreated"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.9), gridspec_kw={"width_ratios":[0.9, 1.3]})
    labs = ["高敏感组", "其余处理组", "未处理组"]
    vals = [r_mean, c_mean, base]
    cols = [C_ACCENT, C_SECOND, C_GRAY]
    ax1.bar(range(3), vals, color=cols, width=0.42, edgecolor="#FFFFFF")
    ax1.plot(range(3), vals, color="#7F7F7F", lw=0.9, alpha=0.7)
    ax1.set_xticks(range(3)); ax1.set_xticklabels(labs, fontsize=9)
    ax1.set_ylabel("下月状态评分变化均值")
    ax1.set_ylim(min(vals)-3, max(vals)+3)
    ax1.axhline(0, color="#555555", lw=1.1)
    for i, v in enumerate(vals):
        va = "bottom" if v >= 0 else "top"
        dy = 0.7 if v >= 0 else -0.7
        ax1.text(i, v+dy, "%.1f" % v, ha="center", va=va, fontsize=10, weight="bold", color=cols[i])
    set_style(ax1)
    ax1.set_title("（a）组间平均改善幅度", fontsize=10, pad=8)

    hi = data[data["sensitivity"] == "高敏感"]
    lo = data[data["sensitivity"] == "低敏感"]
    labels = ["状态变化Y", "顺价指数", "订单满足率", "存销比", "订货成功率", "货源利用率"]
    hi_vals = [hi["Y"].mean(), hi["price_index"].mean(), hi["fill"].mean(), hi["inventory_ratio"].mean(),
               hi["ord_success"].mean(), hi["util"].mean()]
    lo_vals = [lo["Y"].mean(), lo["price_index"].mean(), lo["fill"].mean(), lo["inventory_ratio"].mean(),
               lo["ord_success"].mean(), lo["util"].mean()]
    pair = pd.DataFrame({"高敏感": hi_vals, "低敏感": lo_vals}, index=labels)
    pair_n = (pair - pair.min()) / (pair.max() - pair.min() + 1e-9)
    x = np.arange(len(labels))
    w = 0.24
    ax2.bar(x - w/2, pair_n["高敏感"], width=w, color=C_PRIMARY, edgecolor="#FFFFFF", label="高敏感")
    ax2.bar(x + w/2, pair_n["低敏感"], width=w, color=C_LIGHT, edgecolor="#FFFFFF", label="低敏感")
    ax2.plot(x - w/2, pair_n["高敏感"], color=C_PRIMARY, lw=0.9, alpha=0.7)
    ax2.plot(x + w/2, pair_n["低敏感"], color=C_LIGHT, lw=0.9, alpha=0.7)
    for i, lab in enumerate(labels):
        ax2.text(i - w/2, pair_n["高敏感"].iloc[i] + 0.03, f"{pair['高敏感'].iloc[i]:.2f}", ha="center", fontsize=8.1, color=C_PRIMARY)
        ax2.text(i + w/2, pair_n["低敏感"].iloc[i] + 0.03, f"{pair['低敏感'].iloc[i]:.2f}", ha="center", fontsize=8.1, color=C_LIGHT)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylim(0, 1.18)
    ax2.set_ylabel("归一化对比值")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.legend(frameon=False, fontsize=9, ncol=2, loc="upper right")
    ax2.set_title("（b）高低敏感关键经营指标对照", fontsize=10, pad=8)
    ax2.text(0.02, 1.08, f"改善率：高敏感 {r_impr*100:.1f}% ，其余处理组 {c_impr*100:.1f}%", transform=ax2.transAxes,
             fontsize=8.7, color=C_DARK)
    fig.suptitle("高敏感品规缩投效果显著优于其余对象（改善率%.0f%% vs %.0f%%）" % (r_impr*100, c_impr*100),
                 fontsize=11.2, color=C_DARK, weight="bold")
    fig.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FIG, "fig7_backtest.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig7 ok")

# =====================================================================
# 图8 分群画像雷达图 (高/中/低)
# =====================================================================
def fig8():
    raw_merge = data[["code", "ym", "CATE", "sensitivity"]].merge(
        panel[["code", "ym", "price_band"]], on=["code", "ym"], how="left"
    )
    raw_merge = raw_merge.dropna(subset=["price_band", "sensitivity", "CATE"]).copy()
    raw_merge["price_band"] = raw_merge["price_band"].astype(int)
    band_map = {2: "中低档", 3: "中档", 4: "中高档", 5: "高档"}
    sens_order = ["低敏感", "中敏感", "高敏感"]
    band_order = [2, 3, 4, 5]
    mean_pivot = (
        raw_merge.groupby(["price_band", "sensitivity"])["CATE"]
        .mean()
        .unstack()
        .reindex(index=band_order, columns=sens_order)
    )
    cnt_pivot = (
        raw_merge.groupby(["price_band", "sensitivity"])["CATE"]
        .size()
        .unstack()
        .reindex(index=band_order, columns=sens_order)
        .fillna(0)
        .astype(int)
    )
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.2, 5.5), gridspec_kw={"width_ratios":[0.95, 1.05]})
    arr = mean_pivot.values
    im = ax.imshow(arr, cmap="RdBu_r", aspect="auto")
    ax.set_xticks(np.arange(len(sens_order)))
    ax.set_xticklabels(sens_order, fontsize=10)
    ax.set_yticks(np.arange(len(band_order)))
    ax.set_yticklabels([band_map[b] for b in band_order], fontsize=10)
    ax.set_xlabel("调控敏感组别")
    ax.set_ylabel("价位段")
    chart_title(ax, "不同价位段在敏感组中的CATE分化")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val = arr[i, j]
            cnt = cnt_pivot.iloc[i, j]
            txt_color = "#FFFFFF" if abs(val) > 12 else C_DARK
            ax.text(j, i, f"{val:.1f}\n(n={cnt})", ha="center", va="center", fontsize=8.2, color=txt_color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("平均CATE")
    ax.set_xticks(np.arange(-.5, len(sens_order), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(band_order), 1), minor=True)
    ax.grid(which="minor", color="#FFFFFF", linestyle="-", linewidth=1.0)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.text(0.02, -0.16, "注：单元格数值为该价位段在对应敏感组中的平均CATE，括号内为样本量。", transform=ax.transAxes,
            fontsize=8.4, color="#666666")

    long_df = mean_pivot.reset_index().melt(id_vars="price_band", var_name="敏感组", value_name="平均CATE")
    long_df["价位段"] = long_df["price_band"].map(band_map)
    xpos = np.arange(len(band_order))
    width = 0.22
    color_map = {"低敏感": C_LIGHT, "中敏感": C_SECOND, "高敏感": C_ACCENT}
    for j, s in enumerate(sens_order):
        vals = long_df[long_df["敏感组"] == s]["平均CATE"].values
        ax2.bar(xpos + (j-1)*width, vals, width=width, color=color_map[s], edgecolor="#FFFFFF", label=s)
        ax2.plot(xpos + (j-1)*width, vals, color=color_map[s], lw=0.9, alpha=0.7)
    ax2.axhline(0, color="#666666", lw=0.9)
    ax2.set_xticks(xpos)
    ax2.set_xticklabels([band_map[b] for b in band_order], fontsize=9.2)
    ax2.set_ylabel("平均CATE")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.legend(frameon=False, fontsize=8.8, ncol=3, loc="upper left")
    ax2.set_title("不同价位段的敏感度梯度", fontsize=10.2, pad=8, color=C_DARK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_radar.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig8 ok")

# =====================================================================
# 图9 状态评分权重条形图 (熵/CRITIC/博弈组合)
# =====================================================================
def fig9():
    w = pd.read_csv(os.path.join(DATA, "entropy_weights_v2.csv"), encoding="utf-8-sig")
    lab = {"util":"货源利用率","fill":"订单满足率","full_surf":"订足面","price_index":"顺价指数",
           "gross_margin":"毛利率","unitval":"单箱销售额","inventory_ratio":"存销比","channel_coverage":"投放客户覆盖率"}
    w["name"] = w["feature"].map(lab).fillna(w["feature"])
    w = w.sort_values("w_fusion")
    fig, ax = plt.subplots(figsize=(9, 5))
    ypos = np.arange(len(w))
    ax.barh(ypos-0.24, w["w_entropy"], height=0.24, color=C_LIGHT, label="熵权法")
    ax.barh(ypos, w["w_critic"], height=0.24, color=C_GRAY, label="CRITIC法")
    cols = [C_ACCENT if i == w["w_fusion"].idxmax() else C_PRIMARY for i in range(len(w))]
    ax.barh(ypos+0.24, w["w_fusion"], height=0.24, color=cols, label="博弈组合(最终)")
    ax.set_yticks(ypos); ax.set_yticklabels(w["name"], fontsize=10)
    ax.set_xlabel("权重")
    set_style(ax)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    chart_title(ax, "状态评分三种赋权结果对比")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_weights.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig9 ok")

    trt = data[data["T"] == 1].dropna(subset=["CATE"]).copy()
    hi_code = trt.sort_values("CATE", ascending=False).iloc[0]["code"]
    lo_code = trt.sort_values("CATE", ascending=True).iloc[0]["code"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("cf", r"D:\TraeNewPaper07-1\Papers2\v16\code\02_run_causal_forest.py")
    cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
    sd, *_ = cf.build_score(panel)
    cmp = panel.merge(sd, on=["code", "ym"], how="left")
    cmp = cmp[cmp["code"].isin([hi_code, lo_code])].copy()
    cmp["dt"] = pd.to_datetime(cmp["ym"].astype(str) + "01", format="%Y%m%d")
    smin, smax = cmp["S"].min(), cmp["S"].max()
    cmp["S_plot"] = (cmp["S"] - smin) / max((smax - smin), 1e-9) * 40 + 30
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.7), sharey=True)
    for ax, code, color, ttl in zip(axes, [hi_code, lo_code], [C_PRIMARY, C_SECOND], ["高敏感代表", "低敏感代表"]):
        d = cmp[cmp["code"] == code].sort_values("dt")
        ax.plot(d["dt"], d["S_plot"], color=color, lw=2.0, marker="o", ms=4.2)
        tmark = trt[trt["code"] == code]["ym"].astype(str).tolist()
        for _, r in d[d["ym"].astype(str).isin(tmark)].iterrows():
            ax.axvspan(r["dt"] - pd.Timedelta(days=12), r["dt"] + pd.Timedelta(days=12), color=C_ACCENT, alpha=0.10, lw=0)
        max_idx = d["S_plot"].idxmax()
        min_idx = d["S_plot"].idxmin()
        ax.scatter(d.loc[max_idx, "dt"], d.loc[max_idx, "S_plot"], color=C_ACCENT, s=34, zorder=4)
        ax.scatter(d.loc[min_idx, "dt"], d.loc[min_idx, "S_plot"], color=C_LIGHT, s=30, zorder=4)
        ax.text(d.loc[max_idx, "dt"], d.loc[max_idx, "S_plot"] + 1.8, f"{d.loc[max_idx, 'S_plot']:.1f}", fontsize=7.6, color=C_ACCENT, ha="center")
        ax.text(d.loc[min_idx, "dt"], d.loc[min_idx, "S_plot"] - 2.8, f"{d.loc[min_idx, 'S_plot']:.1f}", fontsize=7.6, color=C_LIGHT, ha="center")
        ax.set_title(f"{ttl}：{str(d['name'].iloc[0])[:16]}", fontsize=9.6, color=C_DARK, pad=7)
        ax.grid(axis="y", ls="--", lw=0.55, alpha=0.28, color="#B0B0B0")
        ax.grid(axis="x", ls="--", lw=0.45, alpha=0.18, color="#B0B0B0")
        ax.tick_params(axis="x", rotation=45, labelsize=7.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("综合评分")
    for ax in axes:
        ax.set_xlabel("月份")
    fig.suptitle("高敏感与低敏感代表品规状态轨迹对照", fontsize=11.2, color=C_DARK, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(FIG, "fig9_case_compare.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig9_case ok")

# =====================================================================
# 图10 高敏感代表品规月度状态轨迹 (折线+标注)
# =====================================================================
def fig10():
    # 挑选 CATE 最高且处理组内的代表品规
    trt = data[data["T"] == 1]
    hi = trt.sort_values("CATE", ascending=False)
    code = hi.iloc[0]["code"]
    sub = panel[panel["code"] == code].sort_values("ym")
    if len(sub) < 6:
        code = data["code"].value_counts().index[0]
        sub = panel[panel["code"] == code].sort_values("ym")
    sdp = sub[["ym", "code"]].copy()
    sdp = sdp.merge(panel[["code", "ym", "S"]].drop_duplicates(["code", "ym"]), on=["code", "ym"])
    treat_map = trt[trt["code"] == code][["ym", "T", "CATE"]].drop_duplicates("ym")
    sdp = sdp.merge(treat_map, on="ym", how="left")
    sdp["T"] = sdp["T"].fillna(0)
    sdp["CATE"] = sdp["CATE"].fillna(0)
    sdp["S"] = (sdp["S"] - sdp["S"].min()) / max((sdp["S"].max()-sdp["S"].min()),1e-6) * 40 + 30
    sdp["ymlbl"] = sdp["ym"].astype(str)
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    q1, q2 = sdp["S"].quantile([0.33, 0.67]).values
    ax.axhspan(sdp["S"].min()-1, q1, color="#EEF3F8", alpha=0.65, lw=0)
    ax.axhspan(q1, q2, color="#F8FAFC", alpha=0.80, lw=0)
    ax.axhspan(q2, sdp["S"].max()+1, color="#F2F6FB", alpha=0.55, lw=0)
    ax.plot(range(len(sdp)), sdp["S"], color=C_PRIMARY, lw=2.2, marker="o", ms=5, label="市场状态评分S")
    treat_months = set(sdp.loc[sdp["T"] == 1, "ymlbl"].tolist())
    for i, lab in enumerate(sdp["ymlbl"]):
        if lab in treat_months:
            ax.axvspan(i-0.23, i+0.23, color=C_ACCENT, alpha=0.11, lw=0)
            ax.text(i, sdp["S"].max()+1.2, "缩", ha="center", va="bottom", fontsize=7.8, color=C_ACCENT)
    best = sdp["S"].idxmax()
    worst = sdp["S"].idxmin()
    ax.plot(best, sdp.loc[best, "S"], "o", color=C_ACCENT, ms=9, zorder=5)
    ax.plot(worst, sdp.loc[worst, "S"], "o", color=C_LIGHT, ms=7, zorder=5)
    ax.annotate("状态改善峰值\n+%.1f分" % (sdp.loc[best,"S"]-sdp["S"].min()),
                xy=(best, sdp.loc[best,"S"]), xytext=(best+1.5, sdp["S"].max()*0.9),
                arrowprops=dict(arrowstyle="->", color=C_ACCENT), fontsize=9, color=C_ACCENT)
    ax.annotate("阶段低点\n%.1f分" % sdp.loc[worst, "S"],
                xy=(worst, sdp.loc[worst, "S"]), xytext=(max(worst-1.2,0), sdp.loc[worst, "S"]-6.5),
                arrowprops=dict(arrowstyle="->", color=C_LIGHT), fontsize=8.3, color=C_LIGHT)
    for idx in sdp.index[sdp["T"] == 1].tolist()[:2]:
        ax.text(idx, sdp.loc[idx, "S"] + 2.0, f"CATE={sdp.loc[idx, 'CATE']:.1f}", fontsize=7.6, color=C_ACCENT, ha="center")
    ax.set_xticks(range(len(sdp))); ax.set_xticklabels(sdp["ymlbl"], rotation=45, fontsize=9)
    ax.set_xlabel("月份")
    ax.set_ylabel("市场状态评分（归一化到30-70区间）")
    set_style(ax)
    ax.legend(frameon=False)
    chart_title(ax, "高敏感代表品规月度状态轨迹")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_trajectory.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig10 ok")

# =====================================================================
# 图11 处理/对照协变量平衡SMD (辅色/强调色)
# =====================================================================
def fig11():
    from scipy.stats import mannwhitneyu
    trt = data[data["T"] == 1]; ctl = data[data["T"] == 0]
    covs = M["covs"]
    keep = []
    for c in covs:
        a = trt[c]; b = ctl[c]
        if a.nunique() <= 1: continue
        sd_ = np.sqrt((np.nanstd(a)**2 + np.nanstd(b)**2)/2)
        if sd_ < 1e-9: continue
        keep.append((c, (np.nanmean(a)-np.nanmean(b))/sd_))
    keep.sort(key=lambda x: -abs(x[1]))
    keep = keep[:12]
    names = {"util":"货源利用率","fill":"订单满足率","full_surf":"订足面","ord_success":"订货成功率",
             "price_index":"顺价指数","gross_margin":"毛利率","unitval":"单箱销售额",
             "inventory_ratio":"存销比","channel_coverage":"投放客户覆盖率","demand_gap":"需求缺口率",
             "amt_per_cust":"户均订货金额","new_cust":"新进货户数","S":"市场状态评分"}
    names = {**names, **{"cat_一类烟":"一类烟","cat_二类烟":"二类烟","cat_三类烟":"三类烟",
                         "cat_四类烟":"四类烟","band_高档":"高档","band_中高档":"中高档",
                         "band_中档":"中档","band_中低档":"中低档"}}
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.8, 5.2), gridspec_kw={"width_ratios":[1.2, 0.8]})
    ypos = np.arange(len(keep))
    vals = [k[1] for k in keep]
    cols = [C_ACCENT if abs(v) > 0.5 else C_PRIMARY for v in vals]
    ax.barh(ypos, vals, color=cols, height=0.6, edgecolor="#FFFFFF")
    ax.axvline(0, color="#555555", lw=1)
    ax.axvline(-0.2, color=C_LIGHT, ls=":", lw=1.2); ax.axvline(0.2, color=C_LIGHT, ls=":", lw=1.2)
    ax.set_yticks(ypos); ax.set_yticklabels([names.get(f, f) for f, _ in keep], fontsize=9.5)
    ax.set_xlabel("标准化差异 SMD（|SMD|<0.2 视为平衡）")
    set_style(ax)
    chart_title(ax, "处理组与对照组协变量标准化差异")
    abs_df = pd.DataFrame({"变量":[names.get(f, f) for f, _ in keep], "abs_smd":np.abs(vals)}).sort_values("abs_smd", ascending=False).head(6)
    xpos = np.arange(len(abs_df))
    cols2 = [C_ACCENT if i < 2 else C_PRIMARY for i in range(len(abs_df))]
    ax2.bar(xpos, abs_df["abs_smd"], width=0.42, color=cols2, edgecolor="#FFFFFF")
    ax2.axhline(0.2, color=C_LIGHT, ls="--", lw=1.0)
    ax2.set_xticks(xpos)
    ax2.set_xticklabels([s[:4] for s in abs_df["变量"]], rotation=35, ha="right", fontsize=8.3)
    ax2.set_ylabel("|SMD|")
    set_style(ax2)
    ax2.grid(axis="x", visible=False)
    ax2.set_title("失衡变量排序", fontsize=10.1, pad=8, color=C_DARK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11_smd.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig11 ok")

# =====================================================================
# 图12 六个代表性品规月度轨迹面板图
# =====================================================================
def fig12():
    pan = panel.copy()
    cf_panel = data[["code", "ym", "CATE", "T", "sensitivity"]].copy()
    cf_panel["ym"] = cf_panel["ym"].astype(str)
    pan["ym"] = pan["ym"].astype(str)
    pan = pan.merge(cf_panel, on=["code", "ym"], how="left")
    treated = pan[pan["T"] == 1].copy()
    name_rank = (
        treated.groupby("name", as_index=False)
        .agg(mean_cate=("CATE", "mean"), treat_cnt=("T", "sum"))
        .sort_values(["mean_cate", "treat_cnt"], ascending=[False, False])
    )
    hi_names = name_rank["name"].dropna().drop_duplicates().head(5).tolist()
    lo_names = name_rank.sort_values(["mean_cate", "treat_cnt"], ascending=[True, False])["name"].dropna().drop_duplicates().head(5).tolist()
    names_pick = hi_names + lo_names
    sub = pan[pan["name"].isin(names_pick)].copy()
    sub["dt"] = pd.to_datetime(sub["ym"] + "01", format="%Y%m%d")
    s_min = sub["S"].min()
    s_max = sub["S"].max()
    sub["S_plot"] = (sub["S"] - s_min) / max((s_max - s_min), 1e-9) * 100
    fig, axes = plt.subplots(5, 2, figsize=(11.6, 16.5), sharex=False, sharey=True)
    axes = axes.ravel()
    hi_set = set(hi_names)
    for ax, name in zip(axes, names_pick):
        d = sub[sub["name"] == name].sort_values("dt").copy()
        if d.empty:
            ax.axis("off")
            continue
        mean_cate = d["CATE"].fillna(0).mean()
        is_hi = name in hi_set
        main_color = C_PRIMARY if is_hi else C_SECOND
        ax.set_facecolor("#FCFDFE")
        local_q1, local_q2 = d["S_plot"].quantile([0.33, 0.67]).values
        ax.axhspan(0, local_q1, color="#F3F7FB", alpha=0.55, lw=0)
        ax.axhspan(local_q1, local_q2, color="#FAFBFD", alpha=0.72, lw=0)
        for _, r in d.iterrows():
            x0 = r["dt"] - pd.Timedelta(days=14)
            x1 = r["dt"] + pd.Timedelta(days=14)
            bg = C_ACCENT if float(r.get("T", 0) or 0) == 1 else C_LIGHT
            ax.axvspan(x0, x1, color=bg, alpha=0.10 if bg == C_ACCENT else 0.08, lw=0)
        ax.plot(d["dt"], d["S_plot"], color=main_color, lw=1.8, marker="o", ms=2.8, zorder=3)
        tmask = d["T"].fillna(0) == 1
        ax.scatter(d.loc[tmask, "dt"], d.loc[tmask, "S_plot"], color=C_ACCENT, s=24, zorder=4)
        for _, r in d.loc[tmask].head(3).iterrows():
            ax.annotate("缩", (r["dt"], r["S_plot"]), xytext=(0, 7), textcoords="offset points",
                        ha="center", fontsize=7.2, color=C_ACCENT)
        max_idx = d["S_plot"].idxmax()
        min_idx = d["S_plot"].idxmin()
        end_idx = d.index[-1]
        ax.text(d.loc[max_idx, "dt"], d.loc[max_idx, "S_plot"] + 4, f"{d.loc[max_idx, 'S_plot']:.1f}",
                fontsize=6.8, color=C_ACCENT if is_hi else C_PRIMARY, ha="center")
        ax.text(d.loc[min_idx, "dt"], d.loc[min_idx, "S_plot"] - 6, f"{d.loc[min_idx, 'S_plot']:.1f}",
                fontsize=6.8, color=C_LIGHT, ha="center")
        ax.text(d.loc[end_idx, "dt"], d.loc[end_idx, "S_plot"] + 2.2, f"{d.loc[end_idx, 'S_plot']:.1f}",
                fontsize=6.8, color=main_color, ha="left")
        cat = str(d["cat"].dropna().iloc[0]) if d["cat"].notna().any() else "-"
        sens = "高敏感代表" if is_hi else "低敏感代表"
        ax.set_title(f"{name}（{cat}，{sens}）", fontsize=8.9, color=C_DARK, pad=4)
        ax.grid(axis="y", ls="--", lw=0.55, alpha=0.28, color="#B0B0B0")
        ax.grid(axis="x", ls="--", lw=0.45, alpha=0.18, color="#B0B0B0")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", rotation=45, labelsize=7.1)
        ax.tick_params(axis="y", labelsize=7.6)
        ax.set_ylim(0, 110)
    for ax in axes[::2]:
        ax.set_ylabel("综合评分", fontsize=8.8)
    for ax in axes[-2:]:
        ax.set_xlabel("月份", fontsize=9)
    for ax in axes[len(names_pick):]:
        ax.axis("off")
    fig.text(0.5, 0.968, "高敏感代表样本", ha="center", va="top", fontsize=10.4, color=C_PRIMARY, weight="bold")
    fig.text(0.5, 0.505, "低敏感代表样本", ha="center", va="center", fontsize=10.4, color=C_SECOND, weight="bold")
    fig.lines.append(plt.Line2D([0.08, 0.92], [0.495, 0.495], transform=fig.transFigure, color="#C9D4E3", lw=1.0))
    fig.suptitle("10个代表性品规月度综合评分轨迹与缩投事件对照", fontsize=11.6, color=C_DARK, y=0.995, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(os.path.join(FIG, "fig12_product_panel.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig12 ok")

# =====================================================================
# 图13 根节点分裂变量频率图
# =====================================================================
def fig13():
    root = pd.DataFrame([
        ("顺价指数", 19.3),
        ("存销比", 10.3),
        ("投放客户覆盖率", 10.3),
        ("订足面", 10.0),
        ("订单满足率", 10.0),
    ], columns=["feature", "freq"])
    thr_price = 1.16
    thr_inv = 1034.77
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.9), gridspec_kw={"width_ratios":[0.95, 1.05]})
    ypos = np.arange(len(root))
    cols = [C_ACCENT, C_PRIMARY, C_SECOND, C_PRIMARY, "#8EA4BF"]
    ax1.barh(ypos, root["freq"], color=cols, height=0.42, edgecolor="#FFFFFF")
    ax1.plot(root["freq"], ypos, color="#7F8EA3", lw=0.9, alpha=0.7)
    ax1.set_yticks(ypos)
    ax1.set_yticklabels(root["feature"], fontsize=10)
    ax1.invert_yaxis()
    for i, v in enumerate(root["freq"]):
        ax1.text(v + 0.35, i, f"{v:.1f}%", va="center", fontsize=9.4, color=cols[i])
    ax1.set_xlabel("根节点分裂频率/%")
    set_style(ax1)
    chart_title(ax1, "首层分裂变量频率")

    case_df = data[["code", "ym", "CATE", "T"]].merge(
        panel[["code", "ym", "name", "price_index", "inventory_ratio"]], on=["code", "ym"], how="left"
    )
    trt = case_df[case_df["T"] == 1].dropna(subset=["price_index", "inventory_ratio", "CATE"]).copy()
    hi = trt.sort_values("CATE", ascending=False).drop_duplicates("name").head(5)
    lo = trt.sort_values("CATE", ascending=True).drop_duplicates("name").head(5)
    ax2.scatter(trt["price_index"], trt["inventory_ratio"], s=9, color="#D4DCE7", alpha=0.60, edgecolors="none")
    ax2.scatter(hi["price_index"], hi["inventory_ratio"], s=34, color=C_PRIMARY, label="高敏感代表")
    ax2.scatter(lo["price_index"], lo["inventory_ratio"], s=34, color=C_SECOND, label="低敏感代表")
    ax2.axvline(thr_price, color=C_ACCENT, lw=1.3, ls="--")
    ax2.axhline(thr_inv, color=C_ACCENT, lw=1.3, ls="--")
    for _, r in pd.concat([hi.head(3), lo.head(3)]).iterrows():
        ax2.text(r["price_index"] + 0.003, r["inventory_ratio"] + 18, str(r["name"])[:8], fontsize=7.4, color=C_DARK)
    ax2.text(thr_price + 0.005, ax2.get_ylim()[1] * 0.92, "顺价阈值 1.16", fontsize=8.0, color=C_ACCENT)
    ax2.text(ax2.get_xlim()[0] + 0.01, thr_inv + 35, "存销比阈值 1034.77", fontsize=8.0, color=C_ACCENT)
    ax2.fill_betweenx(ax2.get_ylim(), ax2.get_xlim()[0], thr_price, color=C_LIGHT, alpha=0.06)
    ax2.fill_between([thr_price, ax2.get_xlim()[1]], thr_inv, ax2.get_ylim()[1], color=C_ACCENT, alpha=0.05)
    ax2.set_xlabel("顺价指数")
    ax2.set_ylabel("存销比")
    set_style(ax2)
    ax2.grid(axis="x", ls="--", lw=0.5, alpha=0.25, color="#B0B0B0")
    ax2.legend(frameon=False, fontsize=8.6, loc="upper right")
    ax2.set_title("关键阈值与代表样本落点", fontsize=10.2, pad=8, color=C_DARK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig13_root_split_freq.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig13 ok")

def fig_density_advanced():
    """复刻母版分组密度图；边界效应采用直方密度平滑，避免KDE越界。"""
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    colors = {"低敏感": C_LIGHT, "中敏感": C_SECOND, "高敏感": C_ACCENT, "总体": "#B4555B"}
    lo, hi = float(data.CATE.min()), float(data.CATE.max())
    bins = np.linspace(lo, hi, 34); centers = (bins[:-1] + bins[1:]) / 2
    for g in GROUP_ORDER:
        vals = data.loc[data.sensitivity == g, "CATE"].to_numpy(float)
        hist, _ = np.histogram(vals, bins=bins, density=True)
        smooth = np.convolve(hist, np.ones(3) / 3, mode="same")
        ax.fill_between(centers, 0, smooth, step="mid", color=colors[g], alpha=.16)
        ax.plot(centers, smooth, color=colors[g], lw=1.8, label=g)
        ax.axvline(np.median(vals), color=colors[g], lw=.8, alpha=.75)
    vals = data.CATE.to_numpy(float)
    hist, _ = np.histogram(vals, bins=bins, density=True)
    smooth = np.convolve(hist, np.ones(3) / 3, mode="same")
    ax.plot(centers, smooth, color=colors["总体"], lw=1.7, label="总体")
    ax.fill_between(centers, 0, smooth, step="mid", color=colors["总体"], alpha=.10)
    ax.axvline(0, color="#666", ls="--", lw=1.1)
    ax.set_xlabel("处理效应 / CATE"); ax.set_ylabel("密度 / Density"); set_style(ax)
    ax.legend(frameon=False, fontsize=9); chart_title(ax, "不同敏感组处理效应密度分布")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig3_cate_density_groups.png"), bbox_inches="tight"); plt.close(fig)

def fig_absorption_advanced():
    from sklearn.preprocessing import StandardScaler
    work = data.copy()
    xcols = ["price_index", "ord_success", "channel_coverage", "util"]
    ycols = ["price_index", "gross_margin", "inventory_ratio", "sell_rate"]
    xx = work[xcols].apply(lambda s: s.fillna(s.median()))
    yy = work[ycols].apply(lambda s: s.fillna(s.median())); yy["inventory_ratio"] *= -1
    work["连接嵌入"] = StandardScaler().fit_transform(xx).mean(axis=1)
    work["状态吸收"] = StandardScaler().fit_transform(yy).mean(axis=1)
    fig, ax = plt.subplots(figsize=(7.6, 5.8))
    sc = ax.scatter(work["连接嵌入"], work["状态吸收"], c=work.CATE, cmap="RdYlBu_r", s=15, alpha=.72, edgecolors="none")
    ax.axhline(0, color="#666", ls="--", lw=1); ax.axvline(0, color="#666", ls="--", lw=1)
    for _, r in work.sort_values("CATE", ascending=False).drop_duplicates("name").head(4).iterrows():
        ax.text(r["连接嵌入"]+.04, r["状态吸收"]+.04, str(r["name"])[:9], fontsize=7, color=C_DARK)
    ax.text(.02,.96,"高承接-高吸收\n优先人工复核区",transform=ax.transAxes,fontsize=8.5,color=C_PRIMARY,va="top")
    ax.text(.67,.08,"弱吸收区\n转向动销/去库存",transform=ax.transAxes,fontsize=8.5,color=C_SECOND,va="bottom")
    ax.set_xlabel("市场连接与供给嵌入能力 / Market linkage (standardized)"); ax.set_ylabel("资源调度与状态吸收能力 / Absorption capacity (standardized)")
    set_style(ax); cb=fig.colorbar(sc,ax=ax,fraction=.046,pad=.03); cb.set_label("品规层面CATE")
    chart_title(ax,"政策收益吸收地图"); fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig4_effect_absorption_map.png"),bbox_inches="tight"); plt.close(fig)

def fig_subgroup_forest_advanced():
    work=data.copy(); work["时令"]=np.where(work["month"].isin([1,2]),"元春","常规")
    rows=[]
    for dim,col in [("价位段","price_band_cat"),("品类","cat"),("时令","时令")]:
        for name,g in work.groupby(col):
            vals=g.CATE.to_numpy(float); se=np.std(vals,ddof=1)/np.sqrt(len(vals)) if len(vals)>1 else 0
            rows.append((dim,str(name),len(vals),np.mean(vals),np.mean(vals)-1.96*se,np.mean(vals)+1.96*se))
    z=pd.DataFrame(rows,columns=["维度","子组","n","均值","下限","上限"]).tail(14)
    y=np.arange(len(z)); fig,ax=plt.subplots(figsize=(7.8,5.8))
    ax.errorbar(z["均值"],y,xerr=[z["均值"]-z["下限"],z["上限"]-z["均值"]],fmt="o",color=C_PRIMARY,ecolor=C_LIGHT,elinewidth=1.3,capsize=3,ms=4.5)
    ax.axvline(0,color="#666",ls="--",lw=1); ax.set_yticks(y); ax.set_yticklabels(z["维度"]+"-"+z["子组"]+" (n="+z["n"].astype(str)+")",fontsize=8.3)
    ax.set_xlabel("平均CATE及95%置信区间 / Mean CATE and 95% CI"); set_style(ax); ax.grid(axis="x",ls="--",lw=.55,alpha=.25); chart_title(ax,"价位段、品类与时令异质性森林图")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig6_subgroup_forest.png"),bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    fig1_revised(); fig2(); fig_density_advanced(); fig_absorption_advanced(); fig8(); fig_subgroup_forest_advanced(); fig10(); fig12()
    os.replace(os.path.join(FIG,"fig8_radar.png"), os.path.join(FIG,"fig5_priceband_heatmap.png"))
    os.replace(os.path.join(FIG,"fig10_trajectory.png"), os.path.join(FIG,"fig7_trajectory.png"))
    os.replace(os.path.join(FIG,"fig12_product_panel.png"), os.path.join(FIG,"fig8_product_panel.png"))
    print("\n全部图表生成完成 →", FIG)

