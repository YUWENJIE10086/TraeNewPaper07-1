# -*- coding: utf-8 -*-
"""将修订实验结果回填到 v18-3-3 母版，保留19表8图结构。"""
from pathlib import Path
import json, re
import numpy as np, pandas as pd
from lxml import html, etree

B=Path(__file__).resolve().parents[1]; D=B/"data"; P=B/"论文v18-3-3.html"
d=pd.read_csv(D/"analysis_panel.csv",encoding="utf-8-sig"); m=json.load(open(D/"metrics.json",encoding="utf-8")); imp=pd.read_csv(D/"feature_importance.csv",encoding="utf-8-sig"); bal=pd.read_csv(D/"psm_balance.csv",encoding="utf-8-sig")
doc=html.parse(str(P)); root=doc.getroot(); tables=root.xpath("//table")
NM={"S_clean_pre":"处理无关状态评分","util_pre":"货源利用率","fill_pre":"订单满足率","full_surf_pre":"订足面","ord_success_pre":"订货成功率","price_index_pre":"顺价指数","gross_margin_pre":"毛利率","unitval_pre":"单箱销售额","inventory_ratio_pre":"存销比","channel_coverage_pre":"渠道覆盖率","demand_gap_pre":"需求缺口率","amt_per_cust_pre":"户均订货金额","new_cust_pre":"新进货户数"}
def table(i,rows):
    t=tables[i-1]
    for c in list(t):t.remove(c)
    body=etree.SubElement(t,"tbody")
    for ri,row in enumerate(rows):
        tr=etree.SubElement(body,"tr")
        for v in row: c=etree.SubElement(tr,"th" if ri==0 else "td"); c.text=str(v)
def caption(i,zh,en):
    n=tables[i-1].getnext()
    while n is not None and "caption" not in (n.get("class") or ""):n=n.getnext()
    if n is not None:n.clear();n.set("class","caption");n.text=zh;etree.SubElement(n,"br").tail=en
def f(x,n=3): return f"{x:.{n}f}"

table(1,[["结果维度","指标","方向","业务含义"],["价格秩序","顺价指数","正向","反映零售价格相对批发价格的修复程度"],["终端盈利","毛利率","正向","反映终端盈利基础"],["库存消化","存销比、社会库存、可销天数","负向","反映库存压力与消化速度"],["市场动销","动销率","正向","反映终端销售承接"],["明确排除","订单满足率、需求缺口率、投放量、货源利用率","不进入结果评分","避免处理定义与结果变量机械相关"]])
caption(1,"表1　处理无关结果评分指标体系","Tab. 1 Indicator system for the treatment-independent outcome score")
table(2,[["变量角色","变量","定义口径","识别作用"],["结果变量Y","处理无关状态变化","Y=S*ᵢ,ₜ₊₁-S*ᵢ,ₜ；S*仅含价格、毛利、库存消化和动销指标","避免处理—结果循环构造"],["处理变量T","供给收缩事件","订单满足率≤同月35%分位且环比下降>2个百分点","识别可核对的缩投事件"],["异质性变量X","23维t-1期画像","供需、价格、库存、渠道及品规结构","控制缩投前差异并估计CATE"],["固定效应","品规与月份虚拟变量","双向固定效应补充模型","控制不随时间变化的品规差异和共同月份冲击"]])

groups=["高敏感","中敏感","低敏感"]; r=[["敏感组","样本量","CATE均值","标准差","最小值","25%分位","中位数","75%分位","最大值"]]
for g in groups:
 x=d[d.sensitivity==g].CATE;r.append([g,len(x),f(x.mean()),f(x.std()),f(x.min()),f(x.quantile(.25)),f(x.median()),f(x.quantile(.75)),f(x.max())])
table(3,r)
table(4,[["诊断","设定或统计量","结果","含义"],["分组交叉拟合","按品规5折","同一品规不跨训练与验证折","控制跨月信息泄漏"],["诚实分样本","600棵树；最小叶节点20","分裂与效应估计样本分离","降低自适应偏差"],["倾向得分重叠","落在[0.05,0.95]之外比例",f(m['overlap']['outside_005_095']*100,1)+"%","存在一定尾部重叠不足"],["有效样本量","倾向得分ESS",f(m['overlap']['ess'],1),"主体样本仍具有可比信息"]]);caption(4,"表4　主模型识别与重叠性诊断","Tab. 4 Identification and overlap diagnostics of the main model")
r=[["敏感组","缩投前S*","货源利用率/%","顺价指数","存销比","订单满足率/%","订货成功率/%"]]
for g in groups:
 z=d[d.sensitivity==g];r.append([g,*[f(z[c].mean(),2) for c in ["S_clean_pre","util_pre","price_index_pre","inventory_ratio_pre","fill_pre","ord_success_pre"]]])
table(5,r)
r=[["变量","森林重要性","解释边界"]]
for _,x in imp.head(9).iterrows():r.append([NM.get(x.feature,x.feature.replace("cat_","品类：").replace("band_","价位段：")),f(x.importance,4),"反映异质性分裂贡献，不表示单变量因果方向"])
table(6,r);caption(6,"表6　诚实因果森林异质性变量重要性","Tab. 6 Feature importance for heterogeneity in the honest causal forest")
table(7,[["复核变量","样本中位数","用途","限制"],["处理无关状态评分",f(d.S_clean_pre.median()),"判断初始位势","不得单独决定缩投"],["顺价指数",f(d.price_index_pre.median()),"判断价格修复空间","仅为描述性分箱"],["存销比",f(d.inventory_ratio_pre.median(),2),"判断库存压力","需结合动销"],["订货成功率/%",f(d.ord_success_pre.median(),2),"判断终端承接","不推导连续幅度"]]);caption(7,"表7　关键经营变量的业务复核参考点","Tab. 7 Reference points of key operating variables for business review")
table(8,[["证据","估计值","95%CI或P值","判断"],["诚实因果森林ATE",f(m['ate']),f(m['ate_ci'][0])+"～"+f(m['ate_ci'][1]),"区间跨0"],["双向固定效应",f(m['twfe']['coef']),"P="+f(m['twfe']['p']),"边际显著，方向为正"],["处理前负对照",f(m['negative_control']['coef']),"P="+format(m['negative_control']['p'],'.2e'),"显著，提示残余选择偏差"],["置换安慰剂",f(m['placebo']['mean']),f(m['placebo']['ci'][0])+"～"+f(m['placebo']['ci'][1]),"伪效应围绕0"]]);caption(8,"表8　主效应、固定效应与证伪检验","Tab. 8 Main effect, fixed-effects estimate and falsification tests")
def piv(col,label):
 r=[[label,*groups]]
 for k,z in d.groupby(col):
  row=[k]
  for g in groups:
   x=z[z.sensitivity==g].CATE;row.append(f(x.mean(),2)+f"（n={len(x)}）" if len(x) else "—")
  r.append(row)
 return r
table(9,piv("price_band_cat","价位段"));table(10,piv("cat","品类"))
d["时令"]=np.where(d.month.isin([1,2]),"元春","常规");r=[["维度","子组","样本量","平均CATE","95%参考区间"]]
for dim,col in [("价位段","price_band_cat"),("品类","cat"),("时令","时令")]:
 for k,z in d.groupby(col):
  se=z.CATE.sem();r.append([dim,k,len(z),f(z.CATE.mean()),f(z.CATE.mean()-1.96*se)+"～"+f(z.CATE.mean()+1.96*se)])
table(11,r)
b=m["backtest"];table(12,[["调控对象","样本量","处理无关状态变化均值","改善率/%","缩投前S*差异"],["CATE上三分之一",b["high_n"],f(b["high_mean"]),f(b["high_improve"]*100,1),"SMD="+f(b["baseline_smd"])],["其余处理对象",b["other_n"],f(b["other_mean"]),f(b["other_improve"]*100,1),"P="+format(b["baseline_p"],'.2e')]])
table(13,[["方法","效应估计","区间/平衡","定位"],["诚实因果森林",f(m['ate']),f(m['ate_ci'][0])+"～"+f(m['ate_ci'][1]),"主模型：估计CATE"],["双向固定效应",f(m['twfe']['coef']),f(m['twfe']['ci'][0])+"～"+f(m['twfe']['ci'][1]),"控制品规和月份固定效应"],["1:1倾向得分匹配",f(m['psm']['effect']),"平均|SMD| "+f(m['psm']['mean_abs_smd_before'])+"→"+f(m['psm']['mean_abs_smd_after']),"匹配样本平均差异"]])
table(14,[["检验","指标","结果","解释"],["PSM平衡","平均|SMD|",f(m['psm']['mean_abs_smd_before'])+"→"+f(m['psm']['mean_abs_smd_after']),"可观测协变量平衡改善"],["E-value","匹配后改善风险比",f(m['psm']['risk_ratio'])+"；E-value="+f(m['psm']['e_value']),"强度达到2.156的未测混杂可解释风险比"],["处理前负对照","当期T对处理前状态变化",f(m['negative_control']['coef'])+"，P="+format(m['negative_control']['p'],'.2e'),"显著，不能宣称已排除未观测混杂"],["置换安慰剂","100次伪处理效应",f(m['placebo']['mean'])+"（"+f(m['placebo']['ci'][0])+"～"+f(m['placebo']['ci'][1])+"）","随机标签效应接近0"]]);caption(14,"表14　匹配、未测混杂与证伪检验汇总","Tab. 14 Summary of matching, unmeasured-confounding and falsification checks")
r=[["处理定义","处理样本量","双向固定效应","95%CI","P值"]]
for x in m["threshold_sensitivity"]:r.append([x["definition"],x["treated"],f(x["coef"]),f(x["ci"][0])+"～"+f(x["ci"][1]),f(x["p"])])
table(15,r)
tr=d[d.T==1] if False else d[d["T"]==1]; cols=["ym","name","cat","CATE","Y_clean","S_clean_pre","price_index_pre","inventory_ratio_pre"]
def cases(high=True):
 z=tr.sort_values(["CATE","Y_clean"],ascending=[not high,not high]).drop_duplicates("name").head(5);r=[["月份","品规","类别","CATE","下期变化","缩投前S*","顺价指数","存销比","复核建议"]]
 for _,x in z[cols].iterrows():r.append([x.ym,x["name"],x["cat"],f(x.CATE),f(x.Y_clean),f(x.S_clean_pre),f(x.price_index_pre),f(x.inventory_ratio_pre,2),"进入人工复核" if high else "暂缓缩投"])
 return r,z
rh,zh=cases(True);rl,zl=cases(False);table(16,rh);table(17,rl)
r=[["品规","CATE","模型层级","建议动作","幅度","触发条件","回滚条件"]]
for _,x in pd.concat([zh.head(3),zl.head(3)]).iterrows():
 hi=x.CATE>=tr.CATE.quantile(2/3);r.append([x["name"],f(x.CATE),"高敏感" if hi else "低敏感","优先人工复核" if hi else "暂缓缩投","本研究不估计","结合价盘、库存与总量约束审批","次月价格、库存或动销恶化即回滚"])
table(18,r)

# 结构化摘要：只报告能由本轮结果支持的核心发现。
ab=root.xpath("//section[contains(@class,'abstract')]")
zh=["摘　要：","【目的】识别卷烟品规对供给收缩的差异化响应，降低平均指标用于月度投放时的对象误判。",f"【方法】基于某市203个品规19个月的{m['n']}条品规—月份样本，以顺价、毛利、库存消化和动销构建不含订单满足率、投放量及货源利用率的结果评分；采用按品规分组交叉拟合的诚实因果森林估计条件平均处理效应，并以双向固定效应、倾向得分匹配、E-value、置换与处理前负对照检验复核。",f"【结果】（1）平均处理效应为{m['ate']:.2f}，95%置信区间为{m['ate_ci'][0]:.2f}～{m['ate_ci'][1]:.2f}，未显示普遍正向效应。（2）双向固定效应为{m['twfe']['coef']:.2f}（P={m['twfe']['p']:.3f}），阈值调整后方向一致但显著性不稳。（3）匹配后平均绝对标准化差异降至{m['psm']['mean_abs_smd_after']:.3f}，但处理前负对照显著（P<0.001），表明残余选择偏差尚未排除。", "【结论】供给收缩不宜按平均效应统一执行；模型可作为品规排序和人工复核工具，但在获得真实调控幅度和前瞻试验前，不应解释为自动决策或无偏部署效果。","关键词：卷烟品规；诚实因果森林；条件平均处理效应；供给收缩；负对照；差异化调控"]
en=["Abstract:","[Objective] To identify heterogeneous responses of cigarette specifications to supply contraction and reduce target misclassification in monthly allocation.",f"[Methods] A panel of {m['n']} specification-month observations for 203 specifications over 19 months was analyzed. A treatment-independent outcome score was constructed from price order, profitability, inventory digestion and sell-through, excluding order fulfillment, allocation volume and supply utilization. Conditional average treatment effects were estimated using an honest causal forest with specification-block cross-fitting and examined using two-way fixed effects, propensity-score matching, an E-value, permutation tests and a pre-treatment negative-control outcome.",f"[Results] (1) The average treatment effect was {m['ate']:.2f} (95% CI: {m['ate_ci'][0]:.2f} to {m['ate_ci'][1]:.2f}), providing no evidence of a universally beneficial effect. (2) The two-way fixed-effects estimate was {m['twfe']['coef']:.2f} (P={m['twfe']['p']:.3f}); its direction was stable but significance varied across treatment thresholds. (3) Matching reduced the mean absolute standardized difference to {m['psm']['mean_abs_smd_after']:.3f}, whereas the pre-treatment negative control remained significant (P<0.001), indicating residual selection bias.","[Conclusion] Supply contraction should not be uniformly applied on the basis of an average effect. The model may support specification ranking and human review, but should not be interpreted as an automated or unbiased deployment rule before prospective validation.","Keywords: cigarette specification; honest causal forest; conditional average treatment effect; supply contraction; negative control; differentiated regulation"]
for sec,vals in zip(ab,[zh,en]):
 for p,v in zip(sec.xpath("./p"),vals):
  for c in list(p):p.remove(c)
  p.text=v

rev={
"综合状态评分负责构造结果变量": "图1展示修订后的识别链：处理变量仍由当月供给收缩定义，结果评分仅使用顺价、毛利、库存消化和动销指标，明确排除订单满足率、需求缺口率、投放量和货源利用率；23维协变量全部滞后一期。诚实因果森林负责估计CATE，双向固定效应、匹配、E-value、置换和处理前负对照分别检验可观测与不可观测偏差。",
"设品规": "设品规i在月份t的第j项处理无关标准化结果指标为z*ijt，权重为wj，则状态评分S*由顺价指数、毛利率、存销比、社会库存、可销天数和动销率构成。权重采用熵权与CRITIC等权融合，处理定义涉及的供给指标不参与结果评分。",
"式（2）中": "式（2）中，Y>0表示下一期价格、盈利、库存消化和动销的综合状态改善。处理T仍按订单满足率的月内位置及环比下降定义；所有用于异质性识别的经营画像均取t-1期，从时间顺序和指标集合两方面切断处理—结果机械相关。",
"为使估计结果可被业务人员理解": "本文用诚实因果森林变量重要性解释CATE异质性，并用经营指标分位数形成复核参考点。重要性仅反映变量参与异质性分裂的相对贡献，不提供单变量因果方向，也不直接生成缩投幅度。",
"为检验观测数据": "稳健性分析包括：品规和月份双向固定效应、倾向得分重叠与1:1匹配、匹配后风险比的E-value、100次月内处理标签置换、处理阈值敏感性，以及处理发生前状态变化的负对照结局。负对照用于检验反向选择与未观测混杂；若其显著，模型只能用于探索性排序。",
"诚实因果森林估计结果显示": f"剔除处理相关结果指标后，诚实因果森林ATE为{m['ate']:.3f}（95%CI：{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}），区间跨0。该结果推翻了旧稿基于循环评分得到的强效应叙述：供给收缩在总体上没有稳定的普遍改善证据，后续分析重点转为异质性结构及其识别边界。",
"图2展示2687个": f"图2展示{m['n']}个品规—月份有效样本的CATE分布。直方图、核密度与经验累计分布共同表明效应存在连续异质性；分位线仅用于形成相对排序层级，不是自动执行阈值。",
"表3和图3给出": "表3和图3展示CATE按样本三分位形成的相对层级。分组用于比较模型排序，不等同于高敏感组必然受益；是否执行缩投仍须结合区间估计、价盘、库存、品牌策略和总量约束人工审核。",
"考虑到处理组样本量": "表4报告分组交叉拟合、诚实分样本和倾向得分重叠情况。约14.8%的样本位于[0.05,0.95]之外，提示部分经营画像缺少充分可比样本，外推时应限制在共同支持域。",
"表4显示": "识别诊断表明主体样本具有可比信息，但尾部重叠不足仍然存在。因此，本文不把所有品规的CATE都视为同等可靠，月度清单优先保留置信区间较窄且处于共同支持域的对象。",
"表9与表10表明": "表9至表11和图4至图6显示，价位段、品类和时令内部仍存在CATE差异，但这些结果属于探索性异质性描述。政策收益吸收地图用于组织复核线索，不能替代负对照和固定效应诊断。",
"表12显示": f"表12显示，CATE上三分之一与其余处理样本的改善率均为{b['high_improve']*100:.1f}%，虽然平均变化分别为{b['high_mean']:.2f}和{b['other_mean']:.2f}，但缩投前状态差异极大（SMD={b['baseline_smd']:.2f}，P<0.001）。因此，旧稿60.0%对20.8%的命中率结论不能复现，本表只说明排序与连续变化幅度存在关联，不构成因果验证。",
"稳健性检验综合支持": f"表13至表15给出互相制约的证据。PSM将平均|SMD|由{m['psm']['mean_abs_smd_before']:.3f}降至{m['psm']['mean_abs_smd_after']:.3f}，置换伪效应围绕0；但处理前负对照效应为{m['negative_control']['coef']:.3f}且P<0.001，说明缩投选择仍与既有状态轨迹相关。E-value为{m['psm']['e_value']:.3f}，提示中等强度未测混杂即可改变匹配后风险比解释。综合判断应是“存在排序信号，但尚不足以作自动因果决策”。",
"针对“处理非随机、重叠与反向因果证据不足”": f"倾向得分诊断显示，{m['overlap']['outside_005_095']*100:.1f}%的样本位于[0.05,0.95]之外，并非‘极小比例’；加权有效样本量为{m['overlap']['ess']:.1f}。更关键的是，处理前负对照效应为{m['negative_control']['coef']:.3f}（P<0.001），表明缩投选择与既有状态轨迹显著相关。故时序前置本身不足以排除反向选择，本研究主动降低因果措辞。",
"图7以利群": "图7展示一项代表性处理样本的月度轨迹，并标示缩投事件。单个品规的震荡变化同时受季节、品牌活动和区域经营环境影响，不能由事前事后变化直接归因于缩投；该图仅用于说明月度复核需要连续记录、设置回滚条件。",
"本文采用600棵树构建森林": "本文采用600棵树、最小叶节点20和按品规5折交叉拟合。高、中、低3组按样本CATE三分位形成，只服务于相对排序与业务复核；分位点不是结构性因果阈值，组名也不表示确定受益或受损。",
"表16置于高敏感列": "表16和表17从本轮有效样本中选取代表性品规，列示其处理前状态、CATE及实际下一期变化。案例用于检查模型排序与经营情境是否相符，不以单次事前事后变化证明因果；图8进一步展示轨迹差异，强调品牌活动、季节与区域冲击均可能造成同步变化。",
"基于上述分层": "月度应用改为风险受控的三档复核：模型高排序对象进入优先人工复核，中间对象保留观察，低排序或共同支持不足对象暂缓缩投。由于现有处理变量为二元事件且缺少真实执行幅度，本研究不再给出3%～8%的剂量建议；具体幅度只能由业务审批或后续连续处理效应研究确定。",
"表18的核心思想": "表18将输出限定为复核顺序、触发条件和回滚条件。模型不自动下达缩投指令；任何试行均须记录实际幅度，次月若价格、库存或动销任一核心结果恶化即进入回滚复核。",
"式（11）中": "式（11）仅作为未来接入真实调控幅度后的优化接口。本文数据只识别二元缩投事件，不能从CATE反推出百分比剂量，因此本稿不对各档给出固定幅度；实际动作须由业务约束、审批记录和可回滚试点共同确定。",
"本文的稳健性证据仍有清晰边界": "本研究通过重构结果变量消除了可见的指标循环，并补充双向固定效应、匹配、E-value、置换和处理前负对照。负对照显著说明客户经理判断、临时政策或既有趋势仍可能同时影响缩投与后续状态，故当前证据只能支持探索性对象排序，不能支持无偏部署效果。后续需接入真实决策日志和连续幅度，并开展分期试点或前瞻性随机/准实验验证。"
}
for p in root.xpath("//p"):
 t="".join(p.itertext())
 for k,v in rev.items():
  if k in t:
   for c in list(p):p.remove(c)
   p.text=v;break
for h in root.xpath("//h2"):
 if "SHAP解释" in (h.text or ""):h.text="3.3　异质性变量重要性与解释边界"
 if "回溯验证：高敏感组是否真的更有效" in (h.text or ""):h.text="3.6　排序回溯与基线差异"

# 结论必须完全采用本轮可复现实验结果，清除旧稿结论。
for h in root.xpath("//h1|//h2"):
 if "结论" in "".join(h.itertext()) and re.match(r"\s*6", "".join(h.itertext())):
  ps=[]
  n=h.getnext()
  while n is not None and n.tag not in ("h1","h2"):
   nxt=n.getnext()
   if n.tag=="p": ps.append(n)
   n=nxt
  vals=[
   f"（1）处理无关结果评分切断了供给收缩定义与结果变量之间的机械相关；诚实因果森林ATE为{m['ate']:.3f}，95%CI为{m['ate_ci'][0]:.3f}～{m['ate_ci'][1]:.3f}，总体效应不显著。",
   f"（2）双向固定效应估计为{m['twfe']['coef']:.3f}（P={m['twfe']['p']:.3f}），阈值敏感性方向大体一致但显著性不稳定，不能宣称缩投普遍改善。",
   f"（3）匹配后平均绝对标准化差异降至{m['psm']['mean_abs_smd_after']:.3f}，但处理前负对照效应为{m['negative_control']['coef']:.3f}（P<0.001），说明残余选择偏差仍存在；当前模型只适合探索性排序和人工复核。",
   "（4）由于缺少连续投放幅度和前瞻性试验，本研究不提供固定百分比缩投剂量。后续应接入真实决策日志，在共同支持域内开展分期、可回滚的随机或准实验验证。"
  ]
  for p in ps: p.getparent().remove(p)
  pos=h.getparent().index(h)+1
  for v in vals:
   p=etree.Element("p");p.text=v;h.getparent().insert(pos,p);pos+=1
  break

# 原稿式（10）为SHAP分解，修订后改为森林变量重要性的归一化定义。
formulas=root.xpath("//div[contains(@class,'formula')]")
for idx,txt in [(0,"S*ᵢₜ=100×Σⱼwⱼz*ᵢⱼₜ，Σⱼwⱼ=1　（1）"),(1,"Yᵢₜ=S*ᵢ,ₜ₊₁-S*ᵢₜ　（2）")]:
 if len(formulas)>idx:
  for c in list(formulas[idx]): formulas[idx].remove(c)
  formulas[idx].text=txt
for h in root.xpath("//h2"):
 if "2.4" in "".join(h.itertext()):
  n=h.getnext()
  while n is not None and n.tag not in ("h1","h2"):
   if n.tag=="div" and "formula" in (n.get("class") or ""):
    for c in list(n): n.remove(c)
    n.text="Iⱼ=Gⱼ/ΣₖGₖ　（10）"; break
   n=n.getnext()
  break

# 删除仅供内部定稿使用、明确标注“不随正文刊出”的旧说明。
for p in root.xpath("//p[contains(@class,'note')]"):
 if "补充说明（供作者投稿前处理" in "".join(p.itertext()): p.getparent().remove(p)

# 删除已不再采用的SHAP文献，并使倾向得分、E-value和负对照文献顺序连续且在正文引用。
for p in list(root.xpath("//p")):
 t="".join(p.itertext()).strip()
 if "李卓等[5]采用RFM模型" in t:
  p.text=(p.text or "").replace("李卓等[5]采用RFM模型研究零售客户盈利水平提升策略", "莫玉华等[5]基于消费行为数据构建卷烟消费迁移定量测算方法")
  t="".join(p.itertext()).strip()
 if t.startswith("[5] 李卓"):
  for c in list(p): p.remove(c)
  p.text="[5] 莫玉华, 陈昊, 谷越, 等. 基于消费行为数据的卷烟消费迁移定量测算方法[J]. 烟草科技, 2025, 58(7): 84-91. DOI:10.16135/j.issn1002-0861.2024.0762. MO Yuhua, CHEN Hao, GU Yue, et al. A quantitative method to measure cigarette consumption migration based on consumption behavior data[J]. Tobacco Science & Technology, 2025, 58(7): 84-91. DOI:10.16135/j.issn1002-0861.2024.0762."
  t="".join(p.itertext()).strip()
 if t.startswith("[13] LUNDBERG"):
  p.getparent().remove(p)
 elif t.startswith("[14] ROSENBAUM"):
  for c in list(p): p.remove(c)
  p.text="[13] ROSENBAUM P R, RUBIN D B. The central role of the propensity score in observational studies for causal effects[J]. Biometrika, 1983, 70(1): 41-55."
 elif t.startswith("[15] VANDERWEELE"):
  for c in list(p): p.remove(c)
  p.text="[14] VANDERWEELE T J, DING P. Sensitivity analysis in observational research: Introducing the E-value[J]. Annals of Internal Medicine, 2017, 167(4): 268-274."
 elif t.startswith("[16] LIPSITCH"):
  for c in list(p): p.remove(c)
  p.text="[15] LIPSITCH M, TCHETGEN TCHETGEN E, COHEN T. Negative controls: A tool for detecting confounding and bias in observational studies[J]. Epidemiology, 2010, 21(3): 383-388."
 elif t.startswith("稳健性分析包括：") and "[13-15]" not in t:
  p.text=(p.text or "")+"[13-15]"

raw=etree.tostring(root,encoding="unicode",method="html",doctype="<!DOCTYPE html>")
raw=re.sub(r'(?s)<p>\（1\）在诚实样本外口径下.*?</p><p>\（2\）.*?</p><p>\（3\）.*?</p><p>\（4\）.*?</p>',f'<p>（1）处理无关结果评分切断了供给收缩定义与结果变量之间的机械相关；主模型ATE为{m["ate"]:.3f}，95%CI跨0。</p><p>（2）双向固定效应方向为正但仅边际显著，阈值敏感性结果方向一致、显著性不稳，不能宣称缩投普遍改善。</p><p>（3）匹配改善了可观测平衡，但处理前负对照显著，表明残余选择偏差仍存在；模型当前只适合排序与人工复核。</p><p>（4）由于没有连续投放幅度与前瞻试验，本研究不提供百分比缩投剂量，后续须通过可回滚试点验证。</p>',raw)
P.write_text(raw,encoding="utf-8");print({"paper":str(P),"tables":len(root.xpath('//table')),"figures":len(root.xpath('//img'))})
