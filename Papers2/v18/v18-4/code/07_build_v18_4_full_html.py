# -*- coding: utf-8 -*-
"""以 v18-2 为唯一版式母版，保留 8 图 21 表并写入严格重算结果。"""
from pathlib import Path
import json, re
import numpy as np
import pandas as pd
from lxml import html, etree

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parent / "v18-2" / "论文v18-2.html"
OUT = HERE / "论文v18-4.html"
DATA = HERE / "data"
d = pd.read_csv(DATA / "causal_forest_panel.csv", encoding="utf-8-sig")
m = json.load(open(DATA / "metrics.json", encoding="utf-8"))
imp = pd.read_csv(DATA / "feature_importance.csv", encoding="utf-8-sig")
smd = pd.read_csv(DATA / "psm_smd.csv", encoding="utf-8-sig")
doc = html.parse(str(SRC)); root = doc.getroot(); tables = root.xpath("//table")

NAMES={"util_pre":"货源利用率","fill_pre":"订单满足率","full_surf_pre":"订足面","ord_success_pre":"订货成功率",
"price_index_pre":"顺价指数","gross_margin_pre":"毛利率","unitval_pre":"单箱销售额","inventory_ratio_pre":"存销比",
"channel_coverage_pre":"投放客户覆盖率","demand_gap_pre":"需求缺口率","amt_per_cust_pre":"户均订货金额",
"new_cust_pre":"新进货户数","S_pre":"缩投前状态评分"}

def set_table(i, rows):
    t=tables[i-1]
    for child in list(t): t.remove(child)
    tbody=etree.SubElement(t,"tbody")
    for ri,row in enumerate(rows):
        tr=etree.SubElement(tbody,"tr")
        for val in row:
            cell=etree.SubElement(tr,"th" if ri==0 else "td"); cell.text=str(val)

def set_caption(i, zh, en):
    t=tables[i-1]; n=t.getnext()
    while n is not None and "caption" not in (n.get("class") or ""): n=n.getnext()
    if n is not None:
        n.clear(); n.set("class","caption"); n.text=zh; etree.SubElement(n,"br").tail=en

order=["高敏感","中敏感","低敏感"]
rows=[["敏感组","样本量","CATE均值","标准差","1%分位","5%分位","25%分位","中位数","75%分位","95%分位","99%分位","正效应比例/%"]]
for g in order:
    x=d.loc[d.sensitivity==g,"CATE"]
    rows.append([g,len(x),f"{x.mean():.3f}",f"{x.std():.3f}",*[f"{x.quantile(q):.3f}" for q in [.01,.05,.25,.5,.75,.95,.99]],f"{(x>0).mean()*100:.1f}"])
set_table(3,rows)

set_table(4,[["检验环节","设定","结果","审慎解释"],
 ["分组交叉拟合","按品规分组5折","同一品规不跨训练折与验证折","降低同品规跨月信息泄漏"],
 ["诚实分样本","分裂样本45%，估计样本55%","600棵树，叶节点最少20条","分裂与叶效应估计相互独立"],
 ["总体推断","ATE及森林置信区间",f"{m['ate']:.3f}（{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}）","总体效应显著为正，但不替代分层判断"]])
set_caption(4,"表4　诚实因果森林识别与防泄漏设置","Tab. 4 Identification and leakage-control settings of the honest causal forest")

profile=[["敏感组","缩投前状态评分S","货源利用率/%","顺价指数","存销比","订单满足率/%","订货成功率/%"]]
for g in order:
    z=d[d.sensitivity==g]
    profile.append([g,*[f"{z[c].mean():.2f}" for c in ["S_pre","util_pre","price_index_pre","inventory_ratio_pre","fill_pre","ord_success_pre"]]])
set_table(5,profile)

q=d.price_index_pre.quantile([.25,.5,.75]).to_list(); bins=[-np.inf,*q,np.inf]
d["price_bin"]=pd.cut(d.price_index_pre,bins,duplicates="drop")
r=[["顺价指数区间","样本量","平均顺价指数","平均CATE","标准误"]]
for k,g in d.groupby("price_bin",observed=True): r.append([str(k),len(g),f"{g.price_index_pre.mean():.4f}",f"{g.CATE.mean():.3f}",f"{g.CATE.sem():.3f}"])
set_table(6,r)

r=[["变量","因果森林重要性","业务解释"]]
for _,x in imp.head(8).iterrows():
    nm=NAMES.get(x.feature,x.feature.replace("cat_","品类：").replace("band_","价位段："))
    r.append([nm,f"{x.importance:.4f}","用于解释异质性分裂贡献，不作单变量因果结论"])
set_table(7,r); set_caption(7,"表7　因果森林异质性变量重要性排序","Tab. 7 Feature-importance ranking for treatment-effect heterogeneity")

set_table(8,[["层级","复核变量","参考分位区间","用途","解释边界"],
 ["第一层","顺价指数",f"P50={d.price_index_pre.median():.3f}","价格修复空间复核","描述性分箱，不是充分条件"],
 ["第二层","存销比",f"P50={d.inventory_ratio_pre.median():.2f}","库存承压复核","须与CATE及承接能力联合判断"],
 ["第二层","订货成功率",f"P50={d.ord_success_pre.median():.2f}%","终端承接复核","不得直接推导缩投幅度"],
 ["第二层","订单满足率",f"P50={d.fill_pre.median():.2f}%","供需约束复核","仅用于业务二次审核"]])
set_caption(8,"表8　关键经营变量的业务复核参考分箱","Tab. 8 Reference bins of key operating variables for business review")

r=[["变量","重要性占比/%","排序","解释"]]
for j,x in imp.head(5).reset_index(drop=True).iterrows(): r.append([NAMES.get(x.feature,x.feature),f"{x.importance/imp.importance.sum()*100:.2f}",j+1,"森林整体分裂贡献"])
set_table(9,r); set_caption(9,"表9　因果森林主要变量重要性占比","Tab. 9 Importance shares of leading causal-forest variables")

def pivot_table(col, labels):
    r=[[labels,*order]]
    for k,g in d.groupby(col):
        row=[k]
        for s in order:
            z=g[g.sensitivity==s].CATE; row.append(f"{z.mean():.2f}（n={len(z)}）" if len(z) else "—")
        r.append(row)
    return r
set_table(10,pivot_table("price_band_cat","价位段")); set_table(11,pivot_table("cat","品类"))

d["时令"]=np.where(d.month.isin([1,2]),"元春","常规")
r=[["维度","子组","样本量","平均CATE","95%CI"]]
for dim,col in [("价位段","price_band_cat"),("品类","cat"),("时令","时令")]:
    for k,g in d.groupby(col):
        se=g.CATE.sem(); r.append([dim,k,len(g),f"{g.CATE.mean():.3f}",f"{g.CATE.mean()-1.96*se:.3f}～{g.CATE.mean()+1.96*se:.3f}"])
set_table(12,r)

b=m["backtest"]
set_table(13,[["调控对象","样本量","状态改善均值","改善率/%","基线提示"],
 ["处理样本中CATE上三分之一",b["high_n"],f"{b['high_mean_change']:.3f}",f"{b['high_improvement']*100:.1f}",f"缩投前SMD={b['baseline_smd']:.3f}"],
 ["其余处理样本",b["other_n"],f"{b['other_mean_change']:.3f}",f"{b['other_improvement']*100:.1f}",f"P={b['baseline_p']:.3g}；仅作回溯排序验证"]])

set_table(14,[["方法","样本/配对","效应估计","区间或平衡性","功能定位"],
 ["诚实因果森林",m["n"],f"ATE={m['ate']:.3f}",f"95%CI {m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}","主识别：估计CATE异质性"],
 ["1:1倾向得分匹配",m["psm"]["pairs"],f"匹配效应={m['psm']['effect']:.3f}",f"平均|SMD| {m['psm']['mean_abs_smd_before']:.3f}→{m['psm']['mean_abs_smd_after']:.3f}","稳健性辅助，不替代主模型"],
 ["处理组内回溯",m["treated"],f"改善率 {b['high_improvement']*100:.1f}% vs {b['other_improvement']*100:.1f}%",f"基线SMD={b['baseline_smd']:.3f}","检验排序应用性，不作部署增益"]])
set_caption(14,"表14　主模型与补充识别结果对照","Tab. 14 Comparison of the main model and supplementary identification results")

r=[["协变量","匹配前SMD","匹配后SMD"]]
for _,x in smd.assign(a=smd.before.abs()).sort_values("a",ascending=False).head(8).iterrows(): r.append([NAMES.get(x.feature,x.feature),f"{x.before:.3f}",f"{x.after:.3f}"])
set_table(15,r)
set_table(16,[["检验","指标","取值","结论"],
 ["PSM匹配","匹配效应",f"{m['psm']['effect']:.3f}","与主模型方向一致"],
 ["PSM匹配","平均|SMD|",f"{m['psm']['mean_abs_smd_before']:.3f}→{m['psm']['mean_abs_smd_after']:.3f}","匹配后总体平衡明显改善"],
 ["回溯基线检验","缩投前状态评分",f"SMD={b['baseline_smd']:.3f}，P={b['baseline_p']:.3g}","存在基线差异，改善率差异不得解释为纯因果增益"]])
set_caption(16,"表16　PSM与回溯基线稳健性检验汇总","Tab. 16 Summary of PSM and retrospective baseline robustness checks")

set_table(17,[["处理变量定义","处理组样本量","ATE","95%CI","结论"],
 ["订单满足率≤同月35%分位且较上月下降>2个百分点",m["treated"],f"{m['ate']:.3f}",f"{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}","论文主定义；其他阈值未在本轮重复估计，不虚报"]])

tr=d[d["T"]==1].copy()
cols=["ym","name","cat","CATE","Y","price_index_pre","inventory_ratio_pre","ord_success_pre","fill_pre"]
def cases(z, high=True):
    z=z.sort_values(["CATE","Y"],ascending=[not high,not high]).drop_duplicates("name").head(5)
    r=[["月份","品规","类别","CATE","下期变化Y","顺价指数","存销比","订货成功率/%","订单满足率/%","复核说明"]]
    for _,x in z[cols].iterrows(): r.append([x.ym,x["name"],x["cat"],f"{x.CATE:.3f}",f"{x.Y:.3f}",f"{x.price_index_pre:.3f}",f"{x.inventory_ratio_pre:.2f}",f"{x.ord_success_pre:.2f}",f"{x.fill_pre:.2f}","优先复核" if high else "暂缓缩投并复核动销/库存"])
    return r,z
rh,zh=cases(tr,True); rl,zl=cases(tr,False); set_table(18,rh); set_table(19,rl)

r=[["月份","品规","类别","CATE","顺价指数","存销比","建议动作","建议幅度","复核说明"]]
for _,x in pd.concat([zh.head(3),zl.head(3)]).iterrows():
    good=x.CATE>=tr.CATE.quantile(2/3); r.append([x.ym,x["name"],x["cat"],f"{x.CATE:.3f}",f"{x.price_index_pre:.3f}",f"{x.inventory_ratio_pre:.2f}","进入优先缩投复核" if good else "暂缓缩投", "不由二元处理模型估计", "结合价盘、库存和品牌策略人工确定"])
set_table(20,r)

# 替换正文中会误导的旧数值与过度结论，保留章节、公式、图片位置和版式。
for p in root.xpath("//p"):
    txt="".join(p.itertext())
    if any(k in txt for k in ["7.647","14.275","84.4%","46.1%","270个","2857个","323个"]):
        if "平均处理效应" in txt:
            p.text=f"诚实因果森林估计的平均处理效应ATE为{m['ate']:.3f}，95%置信区间为{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}；品规级CATE标准差为{m['cate_sd']:.3f}。总体效应显著为正，但异质性仍是形成差异化复核清单的主要依据。"
        elif "回溯" in txt or "改善率" in txt:
            p.text=f"回溯验证纳入{m['treated']}个实际缩投样本。CATE上三分之一的{b['high_n']}个样本改善率为{b['high_improvement']*100:.1f}%，其余{b['other_n']}个样本为{b['other_improvement']*100:.1f}%。但两组缩投前状态存在差异（SMD={b['baseline_smd']:.3f}，P={b['baseline_p']:.3g}），因此该结果只支持排序复核价值，不解释为完全排除混杂后的部署增益。"
        else:
            p.text=f"图表基于{m['n']}条品规—月份完整样本、{m['products']}个品规和{m['treated']}次供给收缩事件重算。CATE按样本三分位分层，用于比较相对敏感程度，不把单一阈值解释为普适决策规则。"
        for c in list(p): p.remove(c)

revisions = {
"采用R-learner正交化残差和诚实因果森林估计": f"【方法】以某市203个品规19个月的品规—月份面板为样本，按式（1）构造市场状态评分，以式（2）定义下一期状态变化；以订单满足率不高于同月35%分位且较上月下降超过2个百分点识别供给收缩。模型使用23维t−1期经营画像、按品规分组的5折交叉拟合和600棵诚实因果树估计CATE，并以森林变量重要性、业务参考分箱、处理组内回溯和1∶1倾向得分匹配进行解释与复核。",
"清洗后进入估计的有效样本": f"清洗后进入估计的有效样本为{m['products']}个品规、{m['n']}条品规—月份观测，其中处理组{m['treated']}条、对照组{m['n']-m['treated']}条。供给收缩不是随机发生，且处理组占比较低，因此本文采用按品规分组交叉拟合的诚实因果森林，并在解释结果时同步报告匹配平衡和回溯基线差异。",
"SHAP与根节点规则负责解释": "图1给出研究框架：由原始月报构建品规—月份面板，按既定公式形成状态评分S、处理T和结果Y；主识别层使用正交化诚实因果森林估计CATE；结果层以森林变量重要性、经营画像分箱、子组比较和历史案例将模型输出转化为月度复核清单。PSM用于辅助检验处理组与对照组可比性，所有阈值仅作为业务复核入口。",
"以中华(双中支)2025年2月样本为例": "式（7）和式（8）表示先从结果与处理变量中剥离缩投前画像可解释部分，再在正交残差上学习局部处理效应。本文不再以单一样本手工代入未经保存的中间预测值，而直接报告可由结果文件复核的样本级CATE、区间估计和经营画像，避免把示意计算误写成实证结果。",
"树数通过300、600、900棵的稳定性比较确定": f"主模型设置600棵树、最小叶节点20条，单棵树将45%的抽样数据用于寻找分裂，其余55%用于叶节点效应估计；5折交叉拟合按品规分组。CATE按样本三分位划分为高、中、低敏感组，分组仅服务相对排序与复核，不把分位点解释为结构性因果阈值。",
"本文用SHAP": "为提高可解释性，本文直接报告诚实因果森林的异质性变量重要性，并结合关键经营指标的分位分箱、二维政策收益吸收地图和真实品规轨迹进行复核。变量重要性反映变量参与处理效应异质性分裂的相对贡献，不等同于单变量因果效应，也不直接生成缩投规则。",
"先计算各品规CATE并按三分位排序": "实际操作先计算各品规—月份CATE并按三分位排序，再回看缩投前顺价指数、订单满足率、存销比和订货成功率等经营画像，最后形成优先复核、观察复核和暂缓缩投清单。二元处理模型只识别是否缩投的效应，不识别5%～12%等连续幅度，幅度须由业务人员结合总量约束另行确定。",
"为检验观测数据因果识别结果的可靠性": f"稳健性复核包括两部分：一是采用1∶1无放回最近邻倾向得分匹配，比较匹配前后23维协变量的标准化差异；二是在实际缩投样本内比较CATE上三分之一与其余样本的后续改善，同时检验两组缩投前状态评分差异。匹配后平均|SMD|由{m['psm']['mean_abs_smd_before']:.3f}降至{m['psm']['mean_abs_smd_after']:.3f}；回溯分组仍存在基线差异，因此改善率只作排序复核证据。",
"图2展示": f"图2同时展示{m['n']}条样本的CATE直方分布、平滑密度与经验累计分布。ATE为{m['ate']:.3f}，CATE三分位点为{m['q_low']:.3f}和{m['q_high']:.3f}；图中分界线用于形成相对复核层级，不表示超过某一阈值即可自动缩投。",
"表3与图3给出": "表3与图3共同表明三档CATE分布具有清晰的相对梯度，但各档内仍存在连续差异。密度曲线采用边界友好的直方密度平滑，避免普通KDE在样本支持范围外产生虚假尾部；因此图形用于比较分布形态，而不是把分组边界解释为自然断点。",
"表6显示顺价指数": "表6显示，顺价指数分箱后的平均CATE随价格秩序变化呈现梯度，但各箱结果仍混合了其他经营画像。该图表只支持顺价指数作为重要复核维度，不能据此单独设定缩投动作。",
"SHAP在本文中解释": "表7报告因果森林变量重要性。缩投前状态评分、户均订货金额、存销比、单箱销售额和顺价指数贡献居前，说明效应差异来自状态基础、需求承接、库存与价格秩序的共同作用；重要性不提供方向，也不构成单变量因果结论。",
"表9显示": "表8和表9将模型重要性与经营指标分位数转化为可核对的参考信息。分箱点是样本描述性位置，不是从单棵树抽取的稳定因果阈值；实际动作必须同时结合CATE排序、置信区间、库存和品牌策略。",
"表10和表11表明": "表10至表12及图4至图6从价位段、品类和时令三个层面展示异质性。各子组平均CATE总体为正，但不同敏感层级的梯度明显强于单纯价位段或品类差异，说明经营画像比类别标签更适合用于月度对象排序。吸收地图以缩投前连接嵌入能力和状态吸收能力构成二维坐标，颜色表示CATE，用于识别应优先复核与应先处理库存、动销问题的区域。",
"基于上述分层、阈值与案例结果": "基于分层与案例结果，月度投放复核采用三档管理：高敏感对象进入优先缩投复核，中敏感对象进入观察清单，低敏感对象原则上暂缓缩投并优先检查库存、动销和渠道覆盖。模型为二元处理效应模型，不直接给出缩投百分比；具体幅度由业务审批结合总量约束确定。",
"表20将模型结果压缩": "表20把模型结果压缩为可执行的复核动作，同时将建议幅度明确标注为不由本模型估计，避免把是否缩投的因果效应错误外推为连续剂量建议。"
,"正向改善识别率定义": "表14并列报告主模型、倾向得分匹配和处理组内回溯结果。三者回答的问题不同：诚实因果森林用于识别异质性处理效应，PSM用于检查可比样本上的平均方向，回溯比较用于检验排序清单与历史结果是否一致；不再混入与因果识别目标不同的普通预测模型指标。"
,"稳健性检验综合支持主结论": f"PSM匹配后平均|SMD|由{m['psm']['mean_abs_smd_before']:.3f}降至{m['psm']['mean_abs_smd_after']:.3f}，匹配效应为{m['psm']['effect']:.3f}，与主模型方向一致。与此同时，处理组内回溯分层的缩投前状态存在显著差异（SMD={b['baseline_smd']:.3f}，P={b['baseline_p']:.3g}），因此本文仅将改善率差异解释为模型排序的历史关联证据，不声称其为无偏部署增益。"
,"SHAP在本文中的作用": "（3）森林变量重要性与经营指标分位数共同提供解释入口。缩投前状态、需求承接、库存与价格秩序需联合判断，任何单一分箱点都不能直接生成策略；最终动作仍由CATE排序、置信区间与业务复核共同确定。"
,"表5从状态评分": "表5以严格模型实际使用的t−1期经营画像比较三档对象。高敏感组的缩投前状态评分、货源利用率和库存结构与其他组存在系统差异，说明CATE分层是多维经营基础共同作用的结果；任何单一指标都不应被视为自动缩投条件。"
,"表18显示": "表18列出真实缩投样本中CATE较高的代表品规。案例表同时保留下一期状态变化与缩投前经营画像，用于核对模型排序是否符合业务情境；个案不能替代总体因果估计，也不据此直接确定缩投幅度。"
,"与表18相对": "与表18相对，表19列出CATE较低的真实缩投样本。图7和图8分别展示代表品规的完整月度状态轨迹与缩投事件，强调同一动作在不同经营基础上可能产生不同结果；低敏感对象应优先复核库存、动销和渠道承接，不宜机械继续缩投。"
}
for p in root.xpath("//p"):
    txt="".join(p.itertext())
    for marker,new in revisions.items():
        if marker in txt:
            for c in list(p): p.remove(c)
            p.text=new; break
for h in root.xpath("//h2"):
    if "SHAP解释" in (h.text or ""): h.text="3.4　因果森林变量重要性：缩投敏感度的差异来源"
abstracts=root.xpath("//section[contains(@class,'abstract')]")
if len(abstracts)>=2:
    zp=abstracts[0].xpath("./p"); ep=abstracts[1].xpath("./p")
    if len(zp)>3: zp[3].text=f"【结果】ATE为{m['ate']:.3f}（95%CI：{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}），CATE标准差为{m['cate_sd']:.3f}。在实际缩投样本中，CATE上三分之一与其余样本的改善率分别为{b['high_improvement']*100:.1f}%和{b['other_improvement']*100:.1f}%；但缩投前状态仍有差异，故该比较仅支持排序复核价值。PSM后平均|SMD|降至{m['psm']['mean_abs_smd_after']:.3f}。"
    if len(ep)>3: ep[3].text=f"[Results] The ATE was {m['ate']:.3f} (95% CI: {m['ate_ci'][0]:.3f} to {m['ate_ci'][1]:.3f}), and the standard deviation of CATE was {m['cate_sd']:.3f}. The retrospective improvement rates were {b['high_improvement']*100:.1f}% and {b['other_improvement']*100:.1f}%, respectively; baseline imbalance limits this comparison to ranking validation. After propensity-score matching, the mean absolute SMD decreased to {m['psm']['mean_abs_smd_after']:.3f}."
for f in root.xpath("//div[contains(@class,'formula')]"):
    if "φ" in "".join(f.itertext()):
        f.clear(); f.set("class","formula"); f.text="RI_j=I_j/Σ_{k=1}^{p}I_k，　Σ_{j=1}^{p}RI_j=1 （10）"

# 摘要中的核心结果统一更新。
for e in root.xpath("//*[contains(@class,'abstract') or contains(@class,'zhaiyao')]//text()"):
    pass
raw=etree.tostring(root,encoding="unicode",method="html",doctype="<!DOCTYPE html>")
raw=raw.replace("2857","2687").replace("323个品规","203个品规").replace("270个","258个")
raw=raw.replace("7.647","4.126").replace("14.275","1.625").replace("84.4%","83.7%").replace("46.1%","52.9%")
raw=raw.replace("90个","86个").replace("180个","172个").replace("10.077","10.020").replace("-0.105","1.052")
raw=raw.replace("其中处理组270条、对照组2587条","其中处理组258条、对照组2429条")
raw=raw.replace("处理组仅270条","处理组为258条")
raw=raw.replace("缩投5%~12%","缩投幅度由业务复核确定").replace("5%～12%","幅度由业务复核确定").replace("8%～12%","幅度由业务复核确定")
OUT.write_text(raw,encoding="utf-8")
print({"output":str(OUT),"tables":len(root.xpath('//table')),"images":len(root.xpath('//img'))})
