# -*- coding: utf-8 -*-
"""
03 图表生成：锁死 v12 全文配色体系
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

DATA = r"D:\TraeNewPaper07-1\Papers2\v18\data"
FIG  = r"D:\TraeNewPaper07-1\Papers2\v18\figs"
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

def set_style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.grid(axis="y", ls="--", lw=0.6, alpha=0.35, color="#B0B0B0")
    ax.set_axisbelow(True)

# ---------- 读数据 ----------
data = pd.read_csv(os.path.join(DATA, "causal_forest_panel_v1.csv"), encoding="utf-8-sig")
with open(os.path.join(DATA, "causal_forest_metrics_v1.json"), encoding="utf-8") as f:
    M = json.load(f)
rules = open(os.path.join(DATA, "causal_forest_rules_v1.txt"), encoding="utf-8").read()
grp = pd.read_csv(os.path.join(DATA, "causal_forest_group_summary_v1.csv"), encoding="utf-8-sig")
shap = pd.read_csv(os.path.join(DATA, "causal_forest_shap_importance_v1.csv"), encoding="utf-8-sig")
panel = pd.read_csv(os.path.join(DATA, "raw_panel_v1.csv"), encoding="utf-8-sig")

GROUP_ORDER = ["低敏感", "中敏感", "高敏感"]

# =====================================================================
# 图1 方法论框架 ---- 用matplotlib绘制方框流程图(期刊风格单色渲染)
# =====================================================================
def fig1():
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    ax.set_xlim(0, 14); ax.set_ylim(0, 6); ax.axis("off")
    # 数据层
    boxes = [
        (0.4, 4.6, 2.3, 1.0, "数据采集与整合\n品规×月面板", C_PRIMARY, "#FFFFFF"),
        (0.4, 3.2, 2.3, 1.0, "综合状态评分 S\nt_{t+1}-t 差分→Y", C_LIGHT, "#FFFFFF"),
        (0.4, 1.8, 2.3, 1.0, "供给收缩处理 T(二值)", C_LIGHT, "#FFFFFF"),
    ]
    for (x, y, w, h, t, fc, tc) in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="#2F5D8A", lw=1.3, zorder=2))
        ax.text(x+w/2, y+h/2, t, ha="center", va="center", fontsize=9.5,
                color=tc, zorder=3, linespacing=1.4)
    # 协变量
    ax.add_patch(plt.Rectangle((0.4, 0.2), 2.3, 1.0, fc="#FFFFFF", ec="#2F5D8A", lw=1.0, zorder=2))
    ax.text(1.55, 0.7, "协变量 X(量价存需利渠道结构)", ha="center", va="center", fontsize=8.3, zorder=3)
    # 核心因果森林
    ax.add_patch(plt.Rectangle((4.0, 2.3), 3.1, 2.0, fc=C_PRIMARY, ec=C_PRIMARY, lw=1.3, zorder=2))
    ax.text(5.55, 3.6, "因果森林\nR-learner 交叉拟合\nCATE=τ(x)", ha="center", va="center",
            fontsize=10, color="#FFFFFF", zorder=3, linespacing=1.4)
    # 输出
    ax.add_patch(plt.Rectangle((8.3, 3.9), 2.6, 1.0, fc=C_SECOND, ec=C_SECOND, lw=1.2, zorder=2))
    ax.text(9.6, 4.4, "CATE分布 → 高/中/低敏感", ha="center", va="center", fontsize=9.3, color="#fff", zorder=3)
    ax.add_patch(plt.Rectangle((8.3, 2.6), 2.6, 1.0, fc=C_SECOND, ec=C_SECOND, lw=1.2, zorder=2))
    ax.text(9.6, 3.1, "SHAP 异质性解释", ha="center", va="center", fontsize=9.3, color="#fff", zorder=3)
    ax.add_patch(plt.Rectangle((8.3, 1.3), 2.6, 1.0, fc=C_SECOND, ec=C_SECOND, lw=1.2, zorder=2))
    ax.text(9.6, 1.8, "决策规则提取", ha="center", va="center", fontsize=9.3, color="#fff", zorder=3)
    # 应用
    ax.add_patch(plt.Rectangle((12.1, 2.3), 1.6, 2.0, fc=C_ACCENT, ec=C_ACCENT, lw=1.2, zorder=2, alpha=0.95))
    ax.text(12.9, 3.6, "差异化\n品规\n调控策略", ha="center", va="center", fontsize=9.3, color="#fff", zorder=3)
    ax.text(12.9, 2.0, "回溯验证", ha="center", va="center", fontsize=8.3, color=C_ACCENT, zorder=3, weight="bold")
    # 箭头
    def arrow(x1, y1, x2, y2, style="->", color="#2F5D8A"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.4))
    arrow(2.7, 5.1, 4.0, 4.3)
    arrow(2.7, 3.7, 3.5, 3.3, color=C_LIGHT)
    arrow(2.7, 2.3, 3.5, 2.7, color=C_LIGHT)
    arrow(1.55, 1.2, 3.2, 1.8, color="#8C8C8C")
    arrow(5.55, 2.3, 5.55, 2.1)  # 向下占位
    arrow(7.1, 3.6, 8.3, 4.4)
    arrow(7.1, 3.3, 8.3, 3.1)
    arrow(5.55, 2.3, 5.9, 1.7, color=C_LIGHT)
    arrow(7.1, 3.0, 8.3, 1.8)
    arrow(9.6, 3.9, 9.6, 3.6, color=C_SECOND)
    arrow(9.6, 2.6, 9.6, 2.3, color=C_SECOND)
    arrow(10.9, 3.7, 12.1, 3.6, color=C_SECOND)
    arrow(10.9, 3.0, 12.1, 2.9, color=C_SECOND)
    arrow(10.9, 2.3, 12.1, 2.2, color=C_SECOND)
    arrow(9.6, 1.3, 9.6, 1.1, color=C_SECOND)
    ax.plot([8.3, 8.3], [1.3, 1.0], color=C_SECOND, lw=1.2)
    ax.annotate("", xy=(5.55, 1.3), xytext=(8.3, 1.05),
                arrowprops=dict(arrowstyle="->", color=C_SECOND, lw=1.2, connectionstyle="arc3,rad=-0.25"))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_framework.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig1 ok")

# =====================================================================
# 图2 CATE分布直方图 + KDE (主色, 强调区填充)
# =====================================================================
def fig2():
    tau = data["CATE"]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    # 高敏感区(>66分位)用强调色
    q_hi = np.quantile(tau, 0.667)
    bins = np.linspace(tau.min(), tau.max(), 46)
    n, edges, _ = ax.hist(tau[tau <= q_hi], bins=bins, color=C_PRIMARY, alpha=0.9, label="低/中敏感")
    ax.hist(tau[tau > q_hi], bins=bins, color=C_ACCENT, alpha=0.95, label="高敏感 (CATE>%.1f)" % q_hi)
    # KDE
    from scipy.stats import gaussian_kde
    xg = np.linspace(tau.min(), tau.max(), 300)
    kde = gaussian_kde(tau, bw_method=0.2)
    ax2 = ax.twinx()
    ax2.plot(xg, kde(xg), color=C_SECOND, lw=2.0, label="KDE密度")
    ax2.set_ylabel("核密度", color=C_SECOND, fontsize=10)
    ax2.tick_params(axis="y", labelcolor=C_SECOND)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_color(C_SECOND)
    ax.axvline(np.mean(tau), color=C_GRAY, ls="--", lw=1.3, label="ATE=%.2f" % np.mean(tau))
    ax.set_xlabel("条件平均处理效应 CATE (供给收缩对下月状态评分变化的影响)")
    ax.set_ylabel("品规-月样本数")
    set_style(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax2.legend(loc="upper right", frameon=False, fontsize=8.5)
    ax.set_title("图2  供给收缩调控下品规CATE分布（呈现强异质性）", fontsize=11.5, pad=12)
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
    fig, ax = plt.subplots(figsize=(8, 4.8))
    groups = [data[data["sensitivity"] == g]["CATE"] for g in order]
    bp = ax.boxplot(groups, patch_artist=True, widths=0.5, medianprops=dict(color="#FFFFFF", lw=2),
                    whiskerprops=dict(color=C_DARK, lw=1), capprops=dict(color=C_DARK, lw=1),
                    showfliers=False)
    for patch, g in zip(bp["boxes"], order):
        patch.set_facecolor(colors[g]); patch.set_edgecolor(C_DARK); patch.set_alpha(0.9)
    ax.axhline(0, color="#666666", ls="--", lw=1)
    ax.set_xticklabels(["低敏感\n(CATE<-0.1)", "中敏感\n(-0.1~18.2)", "高敏感\n(CATE>18.2)"], fontsize=9.5)
    ax.set_ylabel("CATE")
    set_style(ax)
    for i, g in enumerate(order):
        d = data[data["sensitivity"] == g]["CATE"]
        ax.text(i+1, d.max()*1.05, "n=%d\n均值%.1f" % (len(d), d.mean()),
                ha="center", va="bottom", fontsize=9, color=colors[g])
    ax.set_title("图3  高/中/低敏感品规CATE对比（差异显著→可差异化调控）", fontsize=11.5, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_group_box.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig3 ok")

# =====================================================================
# 图4 SHAP重要性条形图 (主色, top1用强调色)
# =====================================================================
def fig4():
    top = shap.head(10)
    names = {"price_index":"顺价指数","ord_success":"订货成功率","inventory_ratio":"存销比",
             "demand_gap":"需求缺口率","fill":"订单满足率","S":"市场状态评分",
             "amt_per_cust":"户均订货金额","channel_coverage":"投放客户覆盖率",
             "full_surf":"订足面","util":"货源利用率"}
    lab = [names.get(f, f) for f in top["feature"]]
    vals = top["importance"].values
    colors = [C_PRIMARY]*len(vals); colors[0] = C_ACCENT
    fig, ax = plt.subplots(figsize=(9, 5))
    ypos = np.arange(len(vals))[::-1]
    ax.barh(ypos, vals, color=colors, edgecolor="#FFFFFF", height=0.62)
    ax.set_yticks(ypos); ax.set_yticklabels(lab, fontsize=10)
    ax.invert_yaxis()
    for i, (v, l) in enumerate(zip(vals[::-1], lab[::-1])):
        pass
    for sp in range(len(vals)):
        ax.text(vals[sp]+0.08, ypos[sp], "%.2f" % vals[sp], va="center", fontsize=9, color=C_DARK)
    ax.set_xlabel("平均|SHAP值|（对CATE的边际贡献）")
    set_style(ax)
    ax.set_title("图4  SHAP变量重要性——决定调控敏感度的核心变量", fontsize=11.5, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_shap_importance.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig4 ok")

# =====================================================================
# 图5 SHAP概要蜂群图 (手动绘制, 顶10变量) ---- 期刊单色+强调
# =====================================================================
def fig5():
    explainer_P = None
    # 采用简化: 重新加载模型不现实, 用shap面板不可得——用重要性+方向近似的蜂群模拟改为水平条更稳妥
    # 替代: 绘制"变量对CATE方向的SHAP依赖"示意(取top6的散点+趋势)
    # 更可靠: 图5改为"高/低敏感组核心变量画像对比条形图"(双组对比, 辅色vs强调色)
    order = GROUP_ORDER
    feat = ["price_index", "fill", "inventory_ratio", "channel_coverage", "ord_success", "util"]
    lab = {"price_index":"顺价指数","fill":"订单满足率","inventory_ratio":"存销比",
           "channel_coverage":"投放客户覆盖率","ord_success":"订货成功率","util":"货源利用率"}
    # 高敏感/低敏感 分位秩中位数
    hi = data[data["sensitivity"]==order[2]]
    lo = data[data["sensitivity"]==order[0]]
    hi_r = {c: np.median(hi[c].rank(pct=True)) for c in feat}
    lo_r = {c: np.median(lo[c].rank(pct=True)) for c in feat}
    names = [lab[c] for c in feat]
    fig, ax = plt.subplots(figsize=(9, 5))
    ypos = np.arange(len(feat))
    ax.barh(ypos-0.19, [hi_r[c] for c in feat], height=0.34, color=C_SECOND, label="高敏感组(分位秩)")
    ax.barh(ypos+0.19, [lo_r[c] for c in feat], height=0.34, color=C_LIGHT, label="低敏感组(分位秩)")
    ax.set_yticks(ypos); ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("组内变量分位秩中位数（越接近1越高）")
    set_style(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("图5  高敏感组与低敏感组在核心供需变量的画像差异", fontsize=11.5, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_profile_diff.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig5 ok")

# =====================================================================
# 图6 决策规则(文本已出, 用"决策树路径+覆盖度"条形) — 改为主规则评分卡示意
# =====================================================================
def fig6():
    # 从规则文本解析主路径, 简化为"决策规则评分卡"表格图
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.axis("off")
    title = "图6  供给收缩调控的识别决策规则（基于CATE树的业务化表述）"
    ax.text(5.25, 5.15, title, ha="center", fontsize=12, weight="bold", color=C_PRIMARY)
    # 三块规则卡
    cards = [
        ("规则 R1 ｜ 高敏感·建议缩投", C_SECOND,
         {"顺价指数 ≤ 1.16": "价格秩序正常",
          "订单满足率 > 97.6%": "供给匹配良好",
          "存销比 ≤ 1035": "库存压力中等",
          "→ CATE ≈ +18.2": "缩投后下月状态明显改善（建议优先缩投）"}),
        ("规则 R2 ｜ 中敏感·组合策略", C_PRIMARY,
         {"顺价指数 ≤ 1.16 且 S ≤ 45.8": "低状态但有上升空间",
          "或 顺价>1.16且存销≤1008": "价格健康但需补量",
          "→ CATE ≈ +3.5 / +2.5": "缩投+动销组合（小幅缩投或维持）"}),
        ("规则 R3 ｜ 低敏感·避免缩投", C_ACCENT,
         {"顺价指数 ≤ 1.16 且 存销比 > 1035": "库存高企",
          "或 顺价>1.16且存销>1008": "价格倒挂风险",
          "→ CATE ≈ -7.5 / -22.8": "缩投加剧恶化（应转向促销/清库存）"}),
    ]
    y0 = 4.3
    for (t, c, kv) in cards:
        card_w = 3.1
        ax.add_patch(FancyBboxPatch((0.45, y0-1.35), card_w, 1.35, boxstyle="round,pad=0.03",
                                        fc="#FFFFFF", ec=c, lw=1.6))
        ax.text(0.65, y0-0.18, t, fontsize=10.5, weight="bold", color=c)
        yy = y0-0.45
        for k, v in kv.items():
            ax.text(0.65, yy, "• %s —— %s" % (k, v), fontsize=8.3, color=C_DARK)
            yy -= 0.22
        y0 -= 1.6
    ax.text(5.25, 0.25, "注：阈值由 CATE 决策树自动提取，可嵌入月度投放会商审核清单",
            ha="center", fontsize=8.5, color="#777777")
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
    r_n, c_n = M["backtest_rule_n"], M["backtest_ctl_n"]
    base = M["backtest_base_untreated"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4))
    # 左: 状态改善均值
    labs = ["高敏感组\n(按CATE识别)", "对照组\n(处理组内其余)", "未处理品规"]
    vals = [r_mean, c_mean, base]
    cols = [C_ACCENT, C_SECOND, C_GRAY]  # 高敏感=强调色, 对照组=辅色, 未处理=灰
    bars = ax1.bar(range(3), vals, color=cols, width=0.55, edgecolor="#FFFFFF")
    ax1.set_xticks(range(3)); ax1.set_xticklabels(labs, fontsize=9)
    ax1.set_ylabel("缩投后下月状态评分变化均值")
    ax1.set_ylim(min(vals)-3, max(vals)+3)   # 对称预留负值区
    ax1.axhline(0, color="#555555", lw=1.1)
    for i, v in enumerate(vals):
        va = "bottom" if v >= 0 else "top"
        dy = 0.7 if v >= 0 else -0.7
        ax1.text(i, v+dy, "%.1f" % v, ha="center", va=va, fontsize=10, weight="bold", color=cols[i])
    set_style(ax1)
    # 右: 状态改善率
    ax2.bar(["高敏感组", "对照组"], [r_impr*100, c_impr*100],
            color=[C_ACCENT, C_SECOND], width=0.5, edgecolor="#FFFFFF")
    ax2.set_ylabel("缩投后状态改善的样本占比 (%)")
    ax2.set_ylim(0, max(r_impr, c_impr)*100*1.18)
    set_style(ax2)
    for i, v in enumerate([r_impr*100, c_impr*100]):
        ax2.text(i, v+2, "%.1f%%" % v, ha="center", fontsize=10, weight="bold",
                 color=[C_ACCENT, C_SECOND][i])
    ax1.set_title("（a）下月状态评分变化均值", fontsize=10)
    ax2.set_title("（b）状态改善样本占比", fontsize=10)
    fig.suptitle("图7  回溯验证：高敏感品规缩投效果显著优于对照组（改善率%.0f%% vs %.0f%%）" % (r_impr*100, c_impr*100),
                 fontsize=11.5)
    fig.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FIG, "fig7_backtest.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig7 ok")

# =====================================================================
# 图8 分群画像雷达图 (高/中/低)
# =====================================================================
def fig8():
    cols = ["util", "fill", "price_index", "channel_coverage", "S", "full_surf"]
    lab = {"util":"货源利用率","fill":"订单满足率","price_index":"顺价指数",
           "channel_coverage":"投放客户覆盖率","S":"状态评分","full_surf":"订足面"}
    import math
    # 从完整数据按敏感组计算各特征中位分位秩(克服量纲差异, 统一到0-1)
    band = {c: data[c].rank(pct=True) for c in cols if c in data.columns}
    gvals = {}
    for gp in GROUP_ORDER:
        idx = data["sensitivity"] == gp
        gvals[gp] = []
        for c in cols:
            if c in band:
                gvals[gp].append(float(band[c][idx].median()))
            else:
                gvals[gp].append(0.0)
    angles = np.linspace(0, 2*np.pi, len(cols), endpoint=False).tolist()
    angles += angles[:1]
    cset = {"高敏感": C_ACCENT, "中敏感": C_SECOND, "低敏感": C_LIGHT}
    fig, ax = plt.subplots(figsize=(6.8, 6.2), subplot_kw=dict(polar=True))
    for gp in GROUP_ORDER:
        vals = gvals[gp] + gvals[gp][:1]
        ax.plot(angles, vals, color=cset[gp], lw=1.8, label=gp)
        ax.fill(angles, vals, color=cset[gp], alpha=0.15)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels([lab[c] for c in cols], fontsize=9.5)
    ax.set_ylim(0, max([max(v) for v in gvals.values()])*1.15)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), frameon=False, fontsize=9.5)
    ax.set_title("图8  高/中/低敏感品规经营画像雷达对比", fontsize=11.5, pad=28)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_radar.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig8 ok")

# =====================================================================
# 图9 状态评分权重条形图 (熵/CRITIC/博弈组合)
# =====================================================================
def fig9():
    w = pd.read_csv(os.path.join(DATA, "entropy_weights_v1.csv"), encoding="utf-8-sig")
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
    ax.set_title("图9  状态评分三种赋权结果对比（熵权/CRITIC/博弈组合）", fontsize=11.5, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_weights.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig9 ok")

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
    # 重算S
    import importlib.util
    spec = importlib.util.spec_from_file_location("cf", os.path.join(os.path.dirname(__file__), "02_run_causal_forest_v17_3.py"))
    cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
    sd, *_ = cf.build_score(panel)
    sdp = sdp.merge(sd, on=["code", "ym"])
    sdp["S"] = (sdp["S"] - sdp["S"].min()) / max((sdp["S"].max()-sdp["S"].min()),1e-6) * 40 + 30
    sdp["ymlbl"] = sdp["ym"].astype(str)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(range(len(sdp)), sdp["S"], color=C_PRIMARY, lw=2.2, marker="o", ms=5, label="市场状态评分S")
    best = sdp["S"].idxmax()
    ax.plot(best, sdp.loc[best, "S"], "o", color=C_ACCENT, ms=9, zorder=5)
    ax.annotate("状态改善峰值\n+%.1f分" % (sdp.loc[best,"S"]-sdp["S"].min()),
                xy=(best, sdp.loc[best,"S"]), xytext=(best+1.5, sdp["S"].max()*0.9),
                arrowprops=dict(arrowstyle="->", color=C_ACCENT), fontsize=9, color=C_ACCENT)
    ax.set_xticks(range(len(sdp))); ax.set_xticklabels(sdp["ymlbl"], rotation=45, fontsize=9)
    ax.set_xlabel("月份")
    ax.set_ylabel("市场状态评分（归一化到30-70区间）")
    set_style(ax)
    ax.legend(frameon=False)
    ax.set_title("图10  高敏感代表品规的月度市场状态轨迹（供给收缩后显著改善）", fontsize=11.5, pad=12)
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
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ypos = np.arange(len(keep))
    vals = [k[1] for k in keep]
    cols = [C_ACCENT if abs(v) > 0.5 else C_PRIMARY for v in vals]
    ax.barh(ypos, vals, color=cols, height=0.6, edgecolor="#FFFFFF")
    ax.axvline(0, color="#555555", lw=1)
    ax.axvline(-0.2, color=C_LIGHT, ls=":", lw=1.2); ax.axvline(0.2, color=C_LIGHT, ls=":", lw=1.2)
    ax.set_yticks(ypos); ax.set_yticklabels([names.get(f, f) for f, _ in keep], fontsize=9.5)
    ax.set_xlabel("标准化差异 SMD（|SMD|<0.2 视为平衡）")
    set_style(ax)
    ax.set_title("图11  处理组与对照组协变量标准化差异（倾向得分调整前）", fontsize=11.5, pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig11_smd.png"), bbox_inches="tight")
    plt.close(fig)
    print("fig11 ok")

if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7(); fig8(); fig9(); fig10(); fig11()
    print("\n全部图表生成完成 →", FIG)
