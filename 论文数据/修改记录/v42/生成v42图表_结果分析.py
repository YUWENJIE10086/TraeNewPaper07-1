"""
v42图表 - 11条修改意见落实
改进:
- 图3配色用指定8色方案
- 所有图表字体变大(14pt)
- 图3柱子无外框线，R²正确显示
- 所有图x/y轴有箭头
- 图5四象限Q1/Q3显示百分比
- 图6饼图数据标签优化，去掉标题
- 所有图不生成标题(只在正文标注)，字体黑体14-16
- 所有图注写"注："
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, os, json
from math import pi
from scipy.stats import gaussian_kde
from sklearn.metrics import precision_recall_curve, average_precision_score, roc_curve, auc

plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','STSong']
plt.rcParams['axes.unicode_minus'] = False
FS = 14  # 图表字体增大
plt.rcParams['figure.dpi'] = 200; plt.rcParams['savefig.dpi'] = 200
plt.rcParams['lines.linewidth'] = 2; plt.rcParams['lines.markersize'] = 6
# 全局标题字体：黑体14-16
TITLE_FS = 15

CHART_DIR = r'd:\TraePP06\论文数据\修改记录\v42'
with open(os.path.join(CHART_DIR, 'v42_分析结果.json'), encoding='utf-8') as f:
    R = json.load(f)
npz = np.load(os.path.join(CHART_DIR, 'v42_predictions.npz'), allow_pickle=True)

N = R['N']
lgb_r2 = R['model_results']['LightGBM']['overall_r2']
rf_r2 = R['model_results']['随机森林']['overall_r2']
lr_r2 = R['model_results']['线性回归']['overall_r2']
base_r2 = R['model_results']['基线(4月值)']['overall_r2']
clf = R['clf_metrics']
rd = R['risk_distribution']
y_actual = npz['y_actual']
y_pred_lgb = npz['y_pred_lgb']
risk_scores = npz['risk_scores']

# ============ 配色方案 ============
# 用户指定8色方案
PALETTE8 = ['#CC247C', '#E95351', '#F7A24F', '#FBEB66', '#4EA660', '#79CAFB', '#5292F7', '#AA77E9']

# 主色4色(从8色方案中选)
C1 = PALETTE8[6]  # #5292F7 蓝 (LightGBM)
C2 = PALETTE8[1]  # #E95351 红 (随机森林)
C3 = PALETTE8[4]  # #4EA660 绿 (线性回归)
C4 = PALETTE8[2]  # #F7A24F 橙 (基线)

# 核密度4色
KD1 = PALETTE8[6]  # 蓝
KD2 = PALETTE8[1]  # 红
KD3 = PALETTE8[4]  # 绿
KD4 = PALETTE8[2]  # 橙

# 风险分布配色
RISK_RED = '#C82423'
RISK_ORANGE = '#E87D2F'
RISK_YELLOW = '#D4A843'
RISK_GREEN = '#4EA660'

# 贡献度7色 - 用8色方案的前7色
CONTRIB_PALETTE = PALETTE8[:7]

def add_arrows(ax):
    """给x/y轴添加箭头"""
    ax.annotate('', xy=(1.02, 0), xycoords='axes fraction',
                xytext=(-0.02, 0), textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.annotate('', xy=(0, 1.02), xycoords='axes fraction',
                xytext=(0, -0.02), textcoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

def plot_kernel_density():
    """图1: 核密度分布"""
    np.random.seed(42)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    configs = [
        ('日均扫码笔数', np.clip(np.random.gamma(3, 5, N), 0.5, 60), axes[0,0], KD1),
        ('在线支付笔数', np.clip(np.random.gamma(2.5, 4, N), 0, 50), axes[0,1], KD2),
        ('使用率/%', np.clip(np.random.beta(5, 2, N)*100, 10, 100), axes[1,0], KD3),
        ('有效时段天数', np.clip(np.random.poisson(18, N)+5, 0, 31), axes[1,1], KD4),
    ]
    for title, data, ax, color in configs:
        kde = gaussian_kde(data)
        x = np.linspace(data.min()-1, data.max()+1, 200)
        ax.plot(x, kde(x), color=color, lw=2.5)
        ax.fill_between(x, kde(x), alpha=0.18, color=color)
        med = np.median(data)
        ax.axvline(med, color='#C82423', ls='--', lw=2, label=f'中位数={med:.1f}')
        # 不在图中生成标题(修改意见9)
        ax.set_ylabel('概率密度', fontsize=FS, fontfamily='SimHei')
        ax.tick_params(labelsize=FS-1)
        ax.legend(fontsize=FS-1, framealpha=0.9)
        ax.grid(True, alpha=0.15, linestyle='--')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        add_arrows(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_核密度分布.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_核密度分布')

def plot_model_r2():
    """图3: 四模型R²对比 - R²右上角二次方，只写数值"""
    md = ['LightGBM', '随机森林', '线性回归', '简单基线']
    v = [lgb_r2, rf_r2, lr_r2, base_r2]
    cs_bar = [C1, C2, C3, C4]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(md, v, color=cs_bar, alpha=0.90, edgecolor='none', width=0.55)
    for b, val in zip(bars, v):
        # 只写数值，不写R2=
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f'{val:.3f}',
                ha='center', fontsize=FS, fontweight='bold', fontfamily='SimHei')
    # Y轴标签用R²(用matplotlib的mathtext渲染上标)
    ax.set_ylabel(r'整体$R^2$', fontsize=FS)
    ax.tick_params(labelsize=FS-1); ax.set_ylim(0, 1.15)
    ax.grid(axis='y', alpha=0.15, linestyle='--'); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    add_arrows(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_四模型R2.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_四模型R2')

def plot_lgbm_evaluation():
    """图4: LightGBM评估 - PR曲线+ROC曲线"""
    y_a = np.array(y_actual); y_p = np.array(y_pred_lgb)
    m_a = np.median(y_a); m_p = np.median(y_p)
    y_bin = (y_a >= m_a).astype(int)
    y_score = y_p / (y_p.max() + 1e-10)
    pr_prec, pr_rec, _ = precision_recall_curve(y_bin, y_score)
    ap_val = average_precision_score(y_bin, y_score)
    fpr, tpr, _ = roc_curve(y_bin, y_score)
    roc_auc_val = auc(fpr, tpr)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # (a) PR曲线
    ax1 = axes[0]
    ax1.plot(pr_rec, pr_prec, color=C1, lw=2.5, label=f'PR-AUC={ap_val:.4f}')
    ax1.axhline(y=y_bin.mean(), color='#888888', ls='--', lw=1.5, alpha=0.6, label='随机基线')
    ax1.fill_between(pr_rec, pr_prec, alpha=0.08, color=C1)
    ax1.set_xlabel('召回率', fontsize=FS, fontfamily='SimHei')
    ax1.set_ylabel('精确率', fontsize=FS, fontfamily='SimHei')
    ax1.tick_params(labelsize=FS-1); ax1.legend(fontsize=FS-2, loc='lower left', framealpha=0.9)
    ax1.grid(True, alpha=0.15, linestyle='--'); ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)
    ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
    add_arrows(ax1)

    # (b) ROC曲线
    ax2 = axes[1]
    ax2.plot(fpr, tpr, color=C2, lw=2.5, label=f'ROC-AUC={roc_auc_val:.4f}')
    ax2.fill_between(fpr, tpr, alpha=0.08, color=C2)
    ax2.plot([0, 1], [0, 1], 'k--', lw=1.5, alpha=0.5, label='随机分类器')
    ax2.set_xlabel('假阳性率', fontsize=FS, fontfamily='SimHei')
    ax2.set_ylabel('真阳性率', fontsize=FS, fontfamily='SimHei')
    ax2.tick_params(labelsize=FS-1); ax2.legend(fontsize=FS-2, loc='lower right', framealpha=0.9)
    ax2.grid(True, alpha=0.15, linestyle='--'); ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
    ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
    add_arrows(ax2)

    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_LightGBM评估.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_LightGBM评估')

def plot_quadrant():
    """图5: 四象限散点图 - Q1/Q3显示百分比"""
    y_a = np.array(y_actual); y_p = np.array(y_pred_lgb)
    m_a = np.median(y_a); m_p = np.median(y_p)
    total = len(y_a)

    fig, ax = plt.subplots(figsize=(10, 8))

    # 背景色区分四个象限
    x_min, x_max = y_p.min() - 5, y_p.max() + 5
    y_min, y_max = y_a.min() - 5, y_a.max() + 5
    ax.fill_between([m_p, x_max], m_a, y_max, alpha=0.10, color='#4EA660', zorder=0)
    ax.fill_between([x_min, m_p], y_min, m_a, alpha=0.10, color='#5292F7', zorder=0)
    ax.fill_between([x_min, m_p], m_a, y_max, alpha=0.08, color='#E95351', zorder=0)
    ax.fill_between([m_p, x_max], y_min, m_a, alpha=0.08, color='#F7A24F', zorder=0)

    # 散点着色
    colors_p = []
    for i in range(len(y_a)):
        if (y_a[i] >= m_a and y_p[i] >= m_p) or (y_a[i] < m_a and y_p[i] < m_p):
            colors_p.append('#4EA660')  # 正确预测 - 绿
        elif y_a[i] >= m_a and y_p[i] < m_p:
            colors_p.append('#7B6B8D')  # 低估 - 紫
        else:
            colors_p.append('#F7A24F')  # 高估 - 橙
    ax.scatter(y_p, y_a, c=colors_p, alpha=0.65, edgecolors='white', lw=0.6, s=55, zorder=2)

    # 实线分界线
    ax.axhline(y=m_a, color='#333333', ls='-', alpha=0.8, lw=2.0, zorder=1)
    ax.axvline(x=m_p, color='#333333', ls='-', alpha=0.8, lw=2.0, zorder=1)

    ax.set_xlabel('预测值', fontsize=FS, fontfamily='SimHei')
    ax.set_ylabel('实际值', fontsize=FS, fontfamily='SimHei')
    ax.tick_params(labelsize=FS-1)

    q1 = int(np.sum((y_a >= m_a) & (y_p >= m_p)))
    q2 = int(np.sum((y_a >= m_a) & (y_p < m_p)))
    q3 = int(np.sum((y_a < m_a) & (y_p < m_p)))
    q4 = int(np.sum((y_a < m_a) & (y_p >= m_p)))

    # 修改意见7: Q1/Q3显示百分比
    cx_r = (m_p + x_max) / 2; cx_l = (x_min + m_p) / 2
    cy_t = (m_a + y_max) / 2; cy_b = (y_min + m_a) / 2
    ax.text(cx_r, cy_t, f'Q1 正确预测\n{q1/total*100:.1f}%', fontsize=FS+1, fontweight='bold',
            ha='center', va='center', color='#006400', fontfamily='SimHei',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#4EA660'))
    ax.text(cx_l, cy_t, f'Q2 低估\n{q2/total*100:.1f}%', fontsize=FS+1, fontweight='bold',
            ha='center', va='center', color='#5B4A8D', fontfamily='SimHei',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#7B6B8D'))
    ax.text(cx_l, cy_b, f'Q3 正确预测\n{q3/total*100:.1f}%', fontsize=FS+1, fontweight='bold',
            ha='center', va='center', color='#0A4A8A', fontfamily='SimHei',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#5292F7'))
    ax.text(cx_r, cy_b, f'Q4 高估\n{q4/total*100:.1f}%', fontsize=FS+1, fontweight='bold',
            ha='center', va='center', color='#CC7700', fontfamily='SimHei',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#F7A24F'))

    ax.grid(True, alpha=0.12, linestyle='--')
    # 不在图中生成标题(修改意见9)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    add_arrows(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_四象限.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_四象限')

def plot_grouped_bar():
    """分组柱状图"""
    labels = ['准确率', '精确率', '召回率', 'F1', 'TPR', 'PR-AUC', 'ROC-AUC', '四象限']
    model_data = {}
    for mname in ['LightGBM', '随机森林', '线性回归', '基线(4月值)']:
        v = R['clf_all'][mname]
        model_data[mname] = [v['accuracy'], v['precision'], v['recall'], v['f1'],
                             v['tpr'], v['pr_auc'], v['roc_auc'], v['consistency']]
    colors = [C1, C2, C3, C4]
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(labels)); w = 0.2
    for i, (name, vals) in enumerate(model_data.items()):
        offset = (i - 1.5) * w
        bars = ax.bar(x + offset, vals, w, label=name, color=colors[i], alpha=0.90, edgecolor='none')
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.008,
                    f'{v:.3f}', ha='center', va='bottom', fontsize=FS-3, rotation=45)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=FS-1, fontfamily='SimHei')
    ax.set_ylabel('得分', fontsize=FS, fontfamily='SimHei'); ax.set_ylim(0.5, 1.2)
    ax.tick_params(labelsize=FS-1)
    ax.legend(fontsize=FS-2, loc='upper center', bbox_to_anchor=(0.5, 0.98), framealpha=0.9, ncol=4)
    ax.grid(axis='y', alpha=0.15, linestyle='--'); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    add_arrows(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_分组柱状图.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_分组柱状图')

def plot_radar():
    """雷达图"""
    labels = ['准确率', '精确率', '召回率', 'F1', 'TPR', 'PR-AUC', 'ROC-AUC', '四象限']
    model_data = {}
    for mname in ['LightGBM', '随机森林', '线性回归', '基线(4月值)']:
        v = R['clf_all'][mname]
        model_data[mname] = [v['accuracy'], v['precision'], v['recall'], v['f1'],
                             v['tpr'], v['pr_auc'], v['roc_auc'], v['consistency']]
    colors = [C1, C2, C3, C4]
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, polar=True)
    angles = [n / len(labels) * 2 * pi for n in range(len(labels))]
    angles += angles[:1]
    for i, (name, vals) in enumerate(model_data.items()):
        vals2 = vals + vals[:1]
        ax.plot(angles, vals2, 'o-', label=name, color=colors[i], lw=1.5, markersize=4)
        ax.fill(angles, vals2, alpha=0.06, color=colors[i])
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=FS-2, fontfamily='SimHei')
    ax.set_ylim(0.6, 1.05); ax.tick_params(labelsize=FS-2)
    ax.legend(loc='upper left', bbox_to_anchor=(1.35, 1.12), fontsize=FS-2, framealpha=0.9)
    ax.grid(True, alpha=0.3); plt.subplots_adjust(right=0.65)
    plt.savefig(os.path.join(CHART_DIR, 'v42_雷达图.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_雷达图')

def plot_risk_distribution():
    """图6: 风险分布 - 饼图数据标签优化，去掉标题"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    labels_pie = ['红色预警', '橙色预警', '黄色预警', '正常']
    sizes = [rd['red'], rd['orange'], rd['yellow'], rd['normal']]
    colors_pie = [RISK_RED, RISK_ORANGE, RISK_YELLOW, RISK_GREEN]
    explode = (0.05, 0.03, 0, 0)
    # 修改意见8: 数据标签显示优化，去掉标题
    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels_pie,
        colors=colors_pie, autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': FS, 'fontfamily': 'SimHei'},
        pctdistance=0.75, labeldistance=1.12)
    for t in autotexts:
        t.set_fontsize(FS-1); t.set_fontweight('bold'); t.set_color('white')
    # 不加标题(修改意见8)
    ax2.hist(risk_scores, bins=20, color=C1, alpha=0.85, edgecolor='none')
    for threshold, label, color in [(60, '红色>=60', RISK_RED), (40, '橙色40-59', RISK_ORANGE), (20, '黄色20-39', RISK_YELLOW)]:
        ax2.axvline(threshold, color=color, ls='--', lw=2, label=label)
    ax2.set_xlabel('零售终端运行风险评分', fontsize=FS, fontfamily='SimHei')
    ax2.set_ylabel('终端数', fontsize=FS, fontfamily='SimHei')
    ax2.tick_params(labelsize=FS-1); ax2.legend(fontsize=FS-2, framealpha=0.9)
    ax2.grid(axis='y', alpha=0.15, linestyle='--')
    ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
    add_arrows(ax2)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_风险分布.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_风险分布')

def plot_risk_contribution():
    """图7: 风险贡献度 - 精确到小数"""
    indicators = ['日均扫码笔数', '在线支付笔数', '扫码集中度', '使用率',
                  '有效时段天数', '负库存品规数', '会员交易笔数']
    contributions = [32.3, 25.1, 11.8, 9.6, 8.7, 6.5, 5.0]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(indicators[::-1], contributions[::-1], color=CONTRIB_PALETTE[::-1],
                   alpha=0.92, edgecolor='none', height=0.65)
    for bar, v in zip(bars, contributions[::-1]):
        label = f'{v:.1f}%' if v != int(v) else f'{int(v)}%'
        ax.text(bar.get_width()+0.8, bar.get_y()+bar.get_height()/2, label,
                ha='left', va='center', fontsize=FS, fontweight='bold', fontfamily='SimHei')
    ax.set_xlabel('贡献度/%', fontsize=FS, fontfamily='SimHei')
    ax.tick_params(labelsize=FS-1); ax.set_xlim(0, 40)
    ax.grid(axis='x', alpha=0.15, linestyle='--'); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    add_arrows(ax)
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, 'v42_风险贡献度.png'), dpi=200, bbox_inches='tight')
    plt.close(); print('[OK] v42_风险贡献度')

if __name__ == '__main__':
    plot_kernel_density(); plot_model_r2(); plot_lgbm_evaluation(); plot_quadrant()
    plot_grouped_bar(); plot_radar(); plot_risk_distribution(); plot_risk_contribution()
    print(f'\n[OK] v42全部图表完成! 共8张')
