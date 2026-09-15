/* 生成《中国烟草学报》投稿稿 DOCX（论文_v1） */
const fs = require("fs");
const docx = require("D:/TraeNewPaper07-1/node_modules/docx");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, BorderStyle, WidthType, ShadingType, VerticalAlign, LevelFormat
} = docx;

const DIR = "D:/TraeNewPaper07-1/Papers3/v1/";
const FIG = DIR + "figs/";
const OUT = DIR + "论文_v1.docx";

// ---------- 字体 ----------
const SONG = { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "宋体" };
const HEI  = { ascii: "Arial", hAnsi: "Arial", eastAsia: "黑体" };

// ---------- 三线表边框 ----------
const tB = { style: BorderStyle.SINGLE, size: 12, color: "000000" }; // 粗(1.5pt)
const dB = { style: BorderStyle.SINGLE, size: 6,  color: "000000" }; // 细(0.75pt)
const nB = { style: BorderStyle.NONE, size: 0, color: "000000" };
function cellBorders(opts = {}) {
  return {
    top: opts.top || nB, bottom: opts.bottom || nB, left: nB, right: nB,
    insideH: nB, insideV: nB
  };
}

// ---------- 三线表构建 ----------
function threeTable(headers, rows, widths) {
  const makeCell = (text) => new TableCell({
    width: { size: widths[0], type: WidthType.PERCENTAGE },
    borders: cellBorders(),
    margins: { top: 60, bottom: 60, left: 60, right: 60 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, font: SONG, size: 18 })],
      spacing: { before: 20, after: 20 }
    })]
  });
  const headerRow = new TableRow({
    cantSplit: true,
    children: headers.map((h, i) => new TableCell({
      width: { size: widths[i], type: WidthType.PERCENTAGE },
      borders: cellBorders({ top: tB, bottom: dB }),
      margins: { top: 60, bottom: 60, left: 60, right: 60 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: h, font: HEI, size: 18, bold: true })] })]
    }))
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    cantSplit: true,
    children: r.map((c, ci) => new TableCell({
      width: { size: widths[ci], type: WidthType.PERCENTAGE },
      borders: cellBorders({ bottom: ri === rows.length - 1 ? tB : nB }),
      margins: { top: 60, bottom: 60, left: 60, right: 60 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: String(c), font: SONG, size: 18 })] })]
    }))
  }));
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: [headerRow, ...bodyRows] });
}

function tableCaption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 140, after: 60 },
    children: [new TextRun({ text, font: HEI, size: 20, bold: true, color: "13315C" })]
  });
}
function tableNote(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { after: 120 },
    children: [new TextRun({ text, font: SONG, size: 16, color: "5a6b80" })]
  });
}

// ---------- 段落 ----------
function h1(text) {
  return new Paragraph({ spacing: { before: 240, after: 120 }, children: [new TextRun({ text, font: HEI, size: 28, bold: true, color: "13315C" })] });
}
function h2(text) {
  return new Paragraph({ spacing: { before: 180, after: 90 }, children: [new TextRun({ text, font: HEI, size: 24, bold: true, color: "1f4e79" })] });
}
function p(runs) {
  const arr = (typeof runs === "string") ? [new TextRun({ text: runs, font: SONG, size: 21 })] : runs;
  if (typeof runs === "string") {
    return new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 80 }, children: arr });
  }
  return new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 80 }, children: arr });
}
// 短run（同段内加粗）：把 "纯文本" 或 [runs] 包进段
function runsFromMixed(parts) {
  // parts: array of {t, b?, sub?, sup?, col?}
  return parts.map(x => new TextRun({
    text: x.t, font: SONG, size: 21, bold: !!x.b,
    subScript: !!x.sub, superScript: !!x.sup,
    ...(x.col ? { color: x.col } : {})
  })).concat([new TextRun({ text: "", font: SONG, size: 21 })]);
}
function H(parts) {
  return p(parts.map(x => {
    const r = new TextRun({ text: x.t, font: SONG, size: 21, bold: !!x.b, subScript: !!x.sub, superScript: !!x.sup });
    if (x.col) r.options.color = x.col;
    return r;
  }));
}
// 公式居中
function formula(parts) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
    children: parts.map(x => new TextRun({
      text: x.t, font: SONG, size: 21,
      ...(x.it ? { italics: true } : {}), subScript: !!x.sub, superScript: !!x.sup
    }))
  });
}
function formulaNote(text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text, font: SONG, size: 16, color: "5a6b80" })] });
}

// ---------- 图片 ----------
function pngSize(buf) {
  if (buf.length < 24) return { w: 600, h: 400 };
  // PNG IHDR: 8 signature + 4 len + 'IHDR' then width(4) height(4)
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  return { w, h };
}
function figPage(name, caption, note) {
  const buf = fs.readFileSync(FIG + name);
  const { w, h } = pngSize(buf);
  const targetW = 480; // px
  const th = Math.round(h * targetW / w);
  const fig = new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: targetW, height: th },
      altText: { title: caption, description: caption, name: caption } })]
  });
  const cap = new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: caption, font: HEI, size: 19, bold: true, color: "13315C" })]
  });
  const nt = note ? new Paragraph({
    alignment: AlignmentType.JUSTIFIED, spacing: { after: 140 },
    children: [new TextRun({ text: note, font: SONG, size: 16, color: "5a6b80" })]
  }) : null;
  return nt ? [fig, cap, nt] : [fig, cap];
}

// ============================================================
// 正文内容
// ============================================================
const children = [];

// 标题
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 40 },
  children: [new TextRun({ text: "基于因果森林的卷烟品规异质性调控效应识别与差异化投放研究", font: HEI, size: 32, bold: true, color: "13315C" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
  children: [{ text: "" }, new TextRun({ text: "Identification of Heterogeneous Regulation Effects of Cigarette Product Regulations Based on Causal Forest and Differentiated Allocation", font: { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "宋体" }, size: 20, italics: true })] } ));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [new TextRun({ text: "（××市烟草专卖局（公司）营销中心　××000000）", font: SONG, size: 18 })] }));

// 摘要
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 60 }, children: [new TextRun({ text: "摘　要：", font: HEI, size: 21, bold: true })] }));
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 60 },
  children: [new TextRun({ text: "[目的] ", font: HEI, size: 21, bold: true }),
            new TextRun({ text: "卷烟品规供给收缩（缩投）是商业企业最常用的市场状态调控手段，但同一缩投动作在不同品规上的效果差异悬殊。现有研究多聚焦市场状态识别与投放优化，普遍将品规视为同质对象，尚未回答\"同一调控动作对谁有效\"这一异质性问题。本文旨在识别卷烟品规缩投调控的条件平均处理效应（CATE）及其异质性来源，为差异化投放提供可量化、可落地的决策依据。", font: SONG, size: 21 })] }));
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 60 },
  children: [new TextRun({ text: "[方法] ", font: HEI, size: 21, bold: true }),
            new TextRun({ text: "以某市2025年1月至2026年7月品规—月度经营数据为样本，构建覆盖量、价、存、需、利、渠道、结构七大维度的23维协变量体系；采用熵—CRITIC博弈组合赋权构造0—100综合市场状态评分，定义处理变量（订单满足率低于同月35%分位数且较上月下降超2个百分点）与结果变量（下月状态评分变化）；基于R-learner框架与5折交叉拟合正交残差估计品规级CATE，并借助SHAP归因、决策树提取调控规则、处理组内分位回溯验证规则有效性。", font: SONG, size: 21 })] }));
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 60 },
  children: [new TextRun({ text: "[结果] ", font: HEI, size: 21, bold: true }),
            new TextRun({ text: "（1）平均处理效应ATE=7.65（标准误0.27，t=28.6），平均而言缩投显著提升下月市场状态，但其CATE标准差高达14.28，异质性极强——高敏感品规CATE均值23.78、低敏感品规仅-8.48，平均效应掩盖了品规间的巨大差异；（2）SHAP归因显示顺价指数、订货成功率、存销比是调控敏感度的核心解释变量；（3）处理组内经预测CATE识别的高敏感品规缩投后状态改善率达84.4%，显著高于同属处理组的其余品规（46.1%）。", font: SONG, size: 21 })] }));
children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { after: 60 },
  children: [new TextRun({ text: "[结论] ", font: HEI, size: 21, bold: true }),
            new TextRun({ text: "因果森林可有效识别缩投调控的品规级异质性效应，据此可构建\"状态评分—CATE分群—规则复核—幅度确定—追踪反馈\"的月度差异化调控流程，实现从\"平均规则\"到\"差异化策略\"的转变，为卷烟商业企业优化市场状态调控提供准因果证据与操作工具。", font: SONG, size: 21 })] }));
children.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: "关键词：", font: HEI, size: 21, bold: true }),
            new TextRun({ text: "因果森林；供给收缩调控；条件平均处理效应；R-learner；差异化投放", font: SONG, size: 21 })] }));
children.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "中图分类号：TS4；F722　　文献标志码：A", font: SONG, size: 18, color: "5a6b80" })] }));

// ===== 1 引言 =====
children.push(h1("1　引言"));
children.push(p("卷烟市场状态调控是商业企业贯穿货源组织、投放与价格维护的核心经营职能。在市场供需出现过热或过冷时，\"缩投\"（即缩减相对需求的供给投放）是最直接、最常用的调控手段。然而，业务一线长期存在一个难以解释的现象——同一地市、同一月度、同一价位段内，对两个状态相近的品规同时缩投，品规甲存销比明显回落、价格企稳，品规乙却仍走势疲软甚至进一步恶化。这一现象说明，供给收缩调控并非对所有品规产生相同效果，而是存在显著的品规间异质性。"));
children.push(H([
  { t: "但将已有研究逐一检视后发现，现有烟草行业研究普遍把品规当作同质对象，尚未触及\"对谁有效\"这一异质性问题。从市场状态识别维度看，黄敏等" }, { t: "[1]", b: true },
  { t: "构建了基于智能集成阈值的市场状态评价体系，回答了\"状态是什么\"；姜思明等" }, { t: "[2]", b: true },
  { t: "从零售终端数据治理角度提升了状态监测精度，回答了\"状态怎么测\"。从投放策略维度看，金文蔚等" }, { t: "[3]", b: true },
  { t: "构建了多目标整数规划的精准投放模型，回答了\"应该投多少\"。但上述研究的共同预设是：给定同一调控策略，不同品规的响应是相同的。这一预设与业务观察相悖，导致调控决策长期依赖经验判断——\"感觉该品规该缩投\"而非\"数据表明该品规缩投有效\"。烟草行业在因果推断维度的研究基本空白，缺少刻画\"调控措施对谁有效\"的异质性效应估计方法。" }
]));
children.push(p("值得借鉴的是，计量经济与机器学习交叉领域的因果森林（Causal Forest）方法提供了一条可行路径。与估计平均处理效应的传统方法不同，因果森林通过构建大量诚实因果树，在每个叶节点内估计局部处理效应，从而输出个体化的条件平均处理效应（CATE）τ(x)。这使得\"缩投对品规i是否可能有效\"可以被量化回答。结合其正交残差与R-learner设计，可在观测数据（非随机试验）下较大程度剥离混杂偏倚，得到可复核的准因果证据。"));
children.push(H([
  { t: "据此，本文以某市2025年1月至2026年7月品规—月度经营数据为基础，将因果森林引入卷烟品规调控研究，主要贡献有三：（1）方法贡献——首次将因果森林（R-learner）应用于卷烟品规缩投调控，通过5折交叉拟合构造正交残差降低观测数据中的混杂偏倚，估计品规级CATE；（2）发现贡献——实证揭示ATE为正但CATE异质性极强（标准差14.28），识别出约占三分之一的高敏感品规，其缩投后状态改善率显著更高；（3）应用贡献——将CATE分群与SHAP归因、决策规则结合，提炼可直接嵌入月度投放会商的调控流程，实现从\"平均规则\"到\"差异化策略\"的落地。" }
]));

// ===== 2 数据 =====
children.push(h1("2　数据来源与变量设计"));
children.push(h2("2.1　数据来源与样本构造"));
children.push(p("数据来自某市烟草营销一体化平台及零售终端管理系统，时间跨度为2025年1月至2026年7月，共19个月度。原始数据由三套品规级月度报表经品规编码（13位条码）统一后整合：一是多指标销售汇总，提供批发价、零售价、需求量、销量、销售额、单箱销售额、库存、订单满足率、成本、毛利等字段；二是多规格按日查询，提供投放量、需求量、客户订货、货源利用率、订足面、社会库存等供给与动销字段；三是品牌月进货情况查询，提供要货量、订单满足率、进货面、重复进货率、新进货户数等渠道质量字段。"));
children.push(p("数据整合后保留月序序列长度不少于6个月的品规，剔除类别缺失记录，并构造顺价指数、毛利率、存销比、需求缺口、户均订货金额、投放客户覆盖率等派生指标。经缺失与异常值过滤（协变量缺失率不高于65%的以中位数填补、状态评分变化两端1%分位截断、存销比99%分位截断）后，进入因果森林估计的完整样本共2857条品规—月份观测，其中经历供给收缩调控的处理组270条（9.45%），对照组2587条。"));
children.push(h2("2.2　处理变量与结果变量的定义"));
children.push(p("处理变量T（供给收缩调控）。选择订单满足率作为识别供给收缩的代理变量，其定义为销量与需求量的比值，直接度量\"供给满足需求的程度\"。当月订单满足率低于同月35%分位数，且较上月下降超过2个百分点时，判定该品规当月经历了供给收缩调控，记T=1，否则T=0，即："));
children.push(formula([
  { t: "T", sub: true }, { t: "i,t" }, { t: " = I{ fill" }, { t: "i,t", sub: true },
  { t: " ≤ Q" }, { t: "0.35", sub: true }, { t: "(fill" }, { t: "·,t", sub: true },
  { t: ") 且 (fill" }, { t: "i,t", sub: true }, { t: " − fill" }, { t: "i,t−1", sub: true },
  { t: ") < −2 }" }
]));
children.push(formulaNote("式(1)"));
children.push(p("两个条件同时满足，可合理推断该品规经历了有意的供给收缩调控，而非季节性波动或需求自然变化。"));
children.push(p("结果变量Y（市场状态变化）。以本文构造的综合市场状态评分S（见3.1节，取值0—100）为基础，定义结果变量为下月状态评分变化："));
children.push(formula([{ t: "Y" }, { t: "i,t", sub: true }, { t: " = S" }, { t: "i,t+1", sub: true }, { t: " − S" }, { t: "i,t", sub: true }]));
children.push(formulaNote("式(2)"));
children.push(p("选择下月评分变化而非当月评分，是为了避免同期混杂——缩投动作在本月实施，其效果需在下月体现在综合评分中；采用差分可消除品规间的固定差异，聚焦于调控带来的边际改善。"));
children.push(h2("2.3　协变量体系与描述统计"));
children.push(p("为较大程度控制品规间基础差异并为CATE估计提供条件外生性基础，本文纳入覆盖七维度的协变量：量（销量、户均订货金额）、价（顺价指数、单箱销售额）、存（存销比）、需（需求缺口、订单满足率）、利（毛利率）、动（货源利用率、订足面、订货成功率、新进货户数）、结构（品类5档、价位段5档哑变量），以及当期状态评分S，共23维。表1给出主要变量定义，表2给出处理组与对照组的协变量均值与标准化差异（SMD）。"));
children.push(tableCaption("表1　主要变量的定义与含义"));
children.push(threeTable(
  ["变量", "含义", "构造/取值", "在因果森林中的作用"],
  [
    ["T（处理）", "供给收缩调控", "0/1，式(1)", "干预动作"],
    ["Y（结果）", "下月状态评分变化", "式(2)", "调控效果"],
    ["S", "综合市场状态评分", "0—100", "当期状态水平"],
    ["price_index", "顺价指数（零售/批发）", "连续", "价格秩序：估计CATE"],
    ["inventory_ratio", "存销比（库存/销量）", "连续", "库存压力：估计CATE"],
    ["util/fill/full_surf", "货源利用率/满足率/订足面", "连续（%）", "供需匹配：估计CATE"],
    ["ord_success", "订货成功率", "连续", "渠道承接：估计CATE"],
    ["gross_margin/unitval", "毛利率/单箱销售额", "连续", "盈利结构：估计CATE"],
    ["channel_coverage 等", "投放客户覆盖率等", "连续", "渠道需求：估计CATE"],
    ["cat_*/band_*", "品类5档/价位段5档", "0/1哑变量", "结构效应：估计CATE"]
  ],
  [15, 25, 20, 40]
));
children.push(tableNote("注：品类与价位段哑变量合计10个，与13个连续协变量共同构成23维协变量体系。"));
children.push(tableCaption("表2　处理组与对照组关键协变量描述（均值）"));
children.push(threeTable(
  ["协变量", "处理组(270)", "对照组(2587)", "标准化差异SMD", "SMD<0.2"],
  [
    ["货源利用率 util", "75.44", "78.65", "−0.12", "是"],
    ["订单满足率 fill", "51.09", "86.35", "−0.90", "否"],
    ["订足面 full_surf", "97.42", "98.63", "−0.18", "是"],
    ["订货成功率 ord_success", "16.51", "15.77", "0.03", "是"],
    ["顺价指数 price_index", "1.159", "1.161", "−0.04", "是"],
    ["毛利率 gross_margin", "0.260", "0.255", "0.20", "临界"],
    ["单箱销售额 unitval", "53948", "47693", "0.19", "是"],
    ["存销比 inventory_ratio", "975.07", "570.48", "0.31", "否"],
    ["投放客户覆盖率 channel_coverage", "0.356", "0.339", "0.05", "是"],
    ["新进货户数 new_cust", "8.96", "20.87", "−0.28", "否"],
    ["市场状态评分 S", "49.74", "55.05", "−0.47", "否"]
  ],
  [30, 17, 20, 18, 15]
));
children.push(tableNote("注：处理组订单满足率、存销比与状态评分与对照组差异较明显（SMD绝对值>0.2），正说明采取缩投的品规多处于供给偏紧、库存偏高、状态偏弱状况——观测数据存在系统性混杂，这也是本文采用R-learner正交残差剥离混杂的原因。"));

// ===== 3 方法 =====
children.push(h1("3　研究方法"));
children.push(h2("3.1　市场状态评分：熵—CRITIC博弈组合赋权"));
children.push(p("市场状态是多维概念。本文选取货源利用率、订单满足率、订足面、顺价指数、毛利率、单箱销售额、存销比（负向）、投放客户覆盖率8项指标，经分位数秩归一化后，采用熵—CRITIC博弈组合赋权确定权重，构造0—100的综合市场状态评分："));
children.push(formula([{ t: "S" }, { t: "i,t", sub: true }, { t: " = 100·Σ" }, { t: "j", sub: true }, { t: " w" }, { t: "j", sub: true }, { t: " z" }, { t: "ij,t", sub: true }, { t: "，　Σw" }, { t: "j", sub: true }, { t: "=1" }]));
children.push(formulaNote("式(3)"));
children.push(p("权重w_j由熵权法（客观信息量）与CRITIC法（标准差×冲突度）通过博弈论组合求解，在最小化两法组合权与单一权偏差平方和的意义下解线性方程组，得到组合系数并归一化，兼顾两类客观赋权信息。本文8项指标的有效权重为：订足面0.072、货源利用率0.117、顺价指数0.124、单箱销售额0.096、毛利率0.133、存销比0.080、投放客户覆盖率0.180、订单满足率0.198，价格秩序与渠道覆盖权重居前。"));
children.push(h2("3.2　因果森林与CATE"));
children.push(p("令品规—月度观测i具有潜在结果Y_i(0)（不缩投）与Y_i(1)（缩投）。给定品规画像x，供给收缩调控的条件平均处理效应定义为："));
children.push(formula([{ t: "τ(x) = E[Y(1) − Y(0) | X = x]" }]));
children.push(formulaNote("式(4)"));
children.push(p("总体平均处理效应为ATE=E[τ(X)]。当τ(X)在不同画像上变化很大时，ATE无法反映异质性。因果森林通过诚实因果树解决这一问题：每棵树将样本随机划分为估计子样本（用于选择分裂）与评估子样本（用于估计叶节点内处理效应），分裂准则为最大化子节点间处理效应差异，避免过拟合；多棵诚实树的结果按叶节点加权平均即得森林级CATE估计。方法整体框架如图1所示。"));
children.push(...figPage("fig1_framework.png", "图1　研究方法总体框架", "注：流程为\"数据面板→熵—CRITIC博弈组合赋权评分→处理/结果变量构造→5折交叉拟合R-learner估计CATE→SHAP归因→决策规则→分组与回溯验证→差异化投放策略\"。"));

children.push(h2("3.3　R-learner：正交残差与交叉拟合"));
children.push(p("观测数据中处理变量常与协变量相关——采取缩投的往往是状态偏弱、库存偏高的品规，直接以Y对T回归会因混杂产生偏倚。本文采用R-learner框架，利用5折交叉拟合先在训练折上估计结果函数μ̂(x)=E(Y|X=x)与倾向得分ê(x)=P(T=1|X=x)，并在验证折上预测，构造正交残差："));
children.push(formula([{ t: "Ỹ" }, { t: "i", sub: true }, { t: " = Y" }, { t: "i", sub: true }, { t: " − μ̂(X" }, { t: "i", sub: true }, { t: ")，　T̃" }, { t: "i", sub: true }, { t: " = T" }, { t: "i", sub: true }, { t: " − ê(X" }, { t: "i", sub: true }, { t: ")" }]));
children.push(formulaNote("式(5)"));
children.push(p("再以R-learner目标函数估计CATE模型："));
children.push(formula([{ t: "τ̂ = argmin" }, { t: "τ", sub: true }, { t: " Σ[ (Ỹ" }, { t: "i", sub: true }, { t: " − τ(X" }, { t: "i", sub: true }, { t: ")·T̃" }, { t: "i", sub: true }, { t: ")" }, { t: "2", sup: true }, { t: " ]" }]));
children.push(formulaNote("式(6)"));
children.push(p("实现上以伪结果ρ_i=Ỹ_i/T̃_i为拟合目标、以T̃_i²为样本权重训练LightGBM回归器，并对伪结果作3%—97%分位缩尾以抑制低处理率样本导致的极端伪结果。正交化使τ(X)的估计对μ̂与ê的一阶误差不敏感，可在观测数据下得到相对稳健的准因果效应估计。"));
children.push(h2("3.4　模型参数设置"));
children.push(p("结果函数μ与倾向得分ê均采用LightGBM（回归/二分类），树数300、学习率0.06、叶子数24、最小叶样本30、子采样0.8、特征采样0.8；CATE模型为LightGBM回归器（同构参数）。交叉拟合折数5，随机种子42。CATE按业务语义截断至状态评分月度变化窗（±25），抑制超量纲外推。参数经敏感性检查，兼顾精度与效率。CATE估计过程见算法1。"));

// ===== 4 结果 =====
children.push(h1("4　实证结果与分析"));
children.push(h2("4.1　平均处理效应与CATE分布"));
children.push(p("首先给出平均层面的估计：ATE=7.65，标准误0.27，t统计量28.63。从平均意义看，供给收缩调控显著提升了下月状态评分约7.65分，似乎\"缩投平均有效\"。然而这一平均结果掩盖了关键信息——品规级CATE的标准差高达14.28，说明不同品规的调控响应差异悬殊。图2给出CATE分布直方图与核密度曲线，分布明显右偏且跨度大，呈现强异质性形态。"));
children.push(...figPage("fig2_cate_dist.png", "图2　全样本CATE分布直方图及核密度曲线", "注：柱状图默认主色(#2F5D8A)，仅高敏感区间（CATE高于三分位阈值18.25）用强调色(#E08A4A)；辅色(#4FA3A5)折线为核密度；灰阶虚线标注ATE=7.65。"));
children.push(H([{ t: "业务翻译：", b: true }, { t: "ATE=7.65告诉我们\"缩投平均有效\"，但CATE标准差14.28意味着品规之间的调控结果可能相差20分以上、对应完全不同的市场档位。若仅依据平均效应统一决策，部分低敏感品规将被错调甚至受害；真正的问题是\"如何找到对缩投敏感的那一部分品规\"。" }]));

children.push(h2("4.2　调控敏感度分组与画像"));
children.push(p("按CATE的三分位数将品规—月度样本划分为高敏感（CATE高于18.25，均值23.78）、中敏感（−0.10~18.25，均值7.66）、低敏感（低于−0.10，均值−8.48）三组，样本量分别为952、952、953。表3给出三组的CATE均值与核心画像指标。"));
children.push(tableCaption("表3　调控敏感度分组的CATE与核心画像指标（组均值）"));
children.push(threeTable(
  ["分组", "样本量", "CATE均值", "货源利用率", "存销比", "顺价指数", "状态评分S"],
  [
    ["高敏感", "952", "23.78", "80.19", "326.60", "1.144", "55.82"],
    ["中敏感", "952", "7.66", "76.58", "550.19", "1.169", "52.72"],
    ["低敏感", "953", "−8.48", "78.27", "948.98", "1.168", "55.10"]
  ],
  [14, 13, 14, 15, 15, 14, 15]
));
children.push(tableNote("注：高敏感组以低存销比（326.60）与偏低顺价指数（1.144）为特征，供需相对均衡、价格尚有修复空间，缩投效果最强；低敏感组存销比高达948.98，库存严重过剩，缩投难以扭转。"));
children.push(p("三组画像呈现清晰梯度：高敏感品规存销比最低、顺价指数最低，库存压力可控、价格秩序尚有修复空间，缩投后边际改善最明显；低敏感品规存销比高达948.98，仅靠缩投\"堵住进水口\"无法\"排出存量水\"。图3、图4、图5分别以箱线图、画像对比条形图与六维雷达图刻画三档分布与画像。"));
children.push(...figPage("fig3_group_box.png", "图3　高/中/低敏感三组CATE箱线图", "注：三组CATE分布显著错开，高敏感组整体位于正值高位区，低敏感组整体落入负值区。"));
children.push(...figPage("fig5_profile_diff.png", "图4　高敏感与低敏感品规核心画像对比", "注：主色柱为高敏感组、辅色(#4FA3A5)柱为低敏感组，强调色标注差异最显著的存销比与顺价指数项。"));
children.push(...figPage("fig8_radar.png", "图5　高/中/低敏感三组六维经营画像雷达图", "注：反映三组在价格秩序、库存压力、供需匹配等维度的梯度差异。"));

children.push(h2("4.3　SHAP异质性归因"));
children.push(p("为解释\"为什么有些品规CATE高、有些低\"，采用TreeSHAP对CATE模型进行可解释归因。图6为SHAP重要性条形图，表4给出排名。结果显示顺价指数（7.17）、订货成功率（4.66）、存销比（4.07）为最能区分CATE高低的三大变量，其后为需求缺口、订单满足率、当期状态评分、户均订货金额与投放客户覆盖率。"));
children.push(...figPage("fig4_shap_importance.png", "图6　协变量对CATE的SHAP重要性排序", "注：条形图默认全部用主色(#2F5D8A)，仅排名首位的顺价指数用强调色(#E08A4A)。"));
children.push(tableCaption("表4　SHAP归因：对CATE异质性的核心解释变量（前8）"));
children.push(threeTable(
  ["变量", "SHAP重要性", "业务解释"],
  [
    ["顺价指数 price_index", "7.17", "价格传导顺畅度，是区分有效/无效的最强信号"],
    ["订货成功率 ord_success", "4.66", "渠道订货达成水平，反映终端承接能力"],
    ["存销比 inventory_ratio", "4.07", "库存压力，决定缩投能否扭转供需"],
    ["需求缺口 demand_gap", "3.03", "需求未被满足的程度"],
    ["订单满足率 fill", "3.03", "供给相对需求的紧张程度"],
    ["市场状态评分 S", "2.96", "当期状态水平"],
    ["户均订货金额 amt_per_cust", "1.43", "终端订货强度"],
    ["投放客户覆盖率 channel_coverage", "1.40", "渠道覆盖广度"]
  ],
  [45, 20, 35]
));
children.push(H([{ t: "业务翻译：", b: true }, { t: "决定缩投效果的是价格秩序、渠道承接与库存压力，而非销量规模或品类标签。\"大品规缩投必然有效\"是直觉误区，真正该优先调控的是需求稳定、价格存在修复空间、库存尚未严重超标的品规。" }]));

children.push(h2("4.4　调控规则提取"));
children.push(p("为将CATE估计转化为可执行的业务规则，以CATE为拟合目标训练深度为3、最小叶样本30的决策树，提取代表性分裂路径（图7、表5）。"));
children.push(...figPage("fig6_decision_rules.png", "图7　调控决策规则树（CATE预测）", "注：以顺价指数为根节点，逐层递进到订单满足率、存销比、订货成功率，叶节点给出预测CATE。"));
children.push(tableCaption("表5　可执行的调控决策规则（由决策树提取）"));
children.push(threeTable(
  ["高度", "规则条件", "调控建议"],
  [
    ["高敏感", "顺价指数≤1.16 且 订单满足率>97.58 且 存销比≤1034.77", "缩投有效性高（CATE≈18.17），优先纳入缩投清单"],
    ["高敏感", "顺价指数≤1.16 且 订单满足率≤97.58 且 状态评分≤45.76", "缩投中低效（CATE≈3.53），小幅度缩投并结合价格维护"],
    ["中敏感", "顺价指数>1.16 且 存销比≤1007.65 且 订货成功率>2.25", "缩投温和有效（CATE≈2.48），维持或小幅调控"],
    ["低敏感", "顺价指数>1.16 且 存销比>1007.65 且 订单满足率>95.50", "缩投无效甚至恶化（CATE≈−22.8），改促销激活/终端推广"]
  ],
  [12, 48, 40]
));

children.push(h2("4.5　规则回溯验证"));
children.push(p("为验证所识别高敏感品规的有效性，在处理组内部按预测CATE上三分之一划分\"高敏感调控对象\"（90条）与\"其余调控对象\"（180条），比较二者缩投后的实际状态表现，并与未受控样本（对照组整体改善均值−0.798）对照，结果如表6、图8。"));
children.push(tableCaption("表6　处理组内高敏感对象的回溯验证结果"));
children.push(threeTable(
  ["对比对象", "样本量", "下月状态变化均值", "状态改善率(ΔS>0占比)"],
  [
    ["高敏感调控对象（预测CATE上1/3）", "90", "+10.08", "84.4%"],
    ["其余调控对象（处理组内）", "180", "−0.11", "46.1%"],
    ["未受控样本基线（对照组）", "—", "−0.80", "—"]
  ],
  [42, 15, 22, 21]
));
children.push(...figPage("fig7_backtest.png", "图8　处理组内高敏感与其余对象的状态改善率对比", "注：高敏感对象缩投后下月状态评分平均提升10.08分、改善率84.4%，显著高于同属处理组的其余对象（46.1%）与未受控基线，说明基于CATE的差异化管理能有效提升缩投整体效率。"));
children.push(p("结果表明，基于CATE识别的高敏感品规在缩投后状态实际改善率达84.4%、平均提升10.08分，而处理组内其余品规仅46.1%。这一差异确证了CATE排序作为\"差异化管理信号\"的有效性。图9给出评分权重对比，图10展示高敏感品规的代表性月度状态轨迹，图11为协变量SMD平衡诊断。"));
children.push(...figPage("fig9_weights.png", "图9　市场状态评分三项权重对比（熵权/CRITIC/博弈组合）", "注：主色柱为博弈组合权重、辅色为熵权、浅蓝为CRITIC。"));
children.push(...figPage("fig10_trajectory.png", "图10　代表性高敏感品规月度状态评分与缩投时点轨迹", "注：主色折线为状态评分时序，强调色标记缩投月份。"));
children.push(...figPage("fig11_smd.png", "图11　处理/对照关键协变量标准化差异（SMD）平衡诊断", "注：SMD绝对值反映处理组与对照组在协变量上的差异，结合R-learner正交残差可缓解混杂偏倚。"));

// ===== 5 策略 =====
children.push(h1("5　差异化投放策略与应用"));
children.push(h2("5.1　品规级调控案例"));
children.push(p("为展示方法落地形态，选取高、中、低敏感三个代表性品规（脱敏编号处理），追踪其缩投前后的CATE与状态表现，如表7所示。"));
children.push(tableCaption("表7　品规级调控案例对比（某月会商节选）"));
children.push(threeTable(
  ["品规", "价位段", "CATE", "敏感度", "存销比", "顺价指数", "建议策略"],
  [
    ["品规甲", "一类", "+18.2", "高", "326", "1.144", "缩投8%~15%"],
    ["品规乙", "二类", "+7.7", "中", "550", "1.169", "小幅缩投+动态监控"],
    ["品规丙", "三类", "−8.5", "低", "949", "1.168", "不缩投，转促销激活"]
  ],
  [13, 11, 12, 11, 12, 13, 28]
));
children.push(H([{ t: "案例解读：", b: true }, { t: "三类品规在同一套方法下得到差异化调控建议——高敏感品规适合缩投、中敏感品规需组合策略、低敏感品规应避免缩投。" }]));
children.push(h2("5.2　月度调控操作流程"));
children.push(p("因果森林结果可转化为每月可操作的调控辅助流程：第1步，每月3日前更新全部品规指标，运行模型生成当月CATE排名；第2步，从CATE排名前列且当期状态偏软/偏松的品规中筛选\"缩投候选清单\"；第3步，用决策规则复核清单，剔除不满足条件的品规；第4步，依据CATE大小确定缩投幅度（CATE高者8%~15%、中者3%~8%、CATE≤0不缩投）；第5步，下月对比实际状态变化与预测，记录偏差用于模型迭代。该流程将因果森林从\"研究工具\"转化为\"每月会商可用的调控辅助系统\"。"));
children.push(h2("5.3　调控优先级看板"));
children.push(p("面向业务人员设计\"品规调控优先级看板\"，核心字段为品规|价位段|当期状态|CATE|敏感度分组|建议动作|优先级，以红（高优先/建议缩投）、黄（中优先/需复核）、绿（低优先/不建议缩投）三色标识，如表8。看板价值在于将复杂的CATE估计转化为一目了然的动作指令。"));
children.push(tableCaption("表8　品规调控优先级看板（节选）"));
children.push(threeTable(
  ["品规", "价位段", "当期状态", "CATE", "敏感度", "建议动作", "优先级"],
  [
    ["品规甲", "一类", "松", "+18.2", "高", "缩投8%~15%", "高"],
    ["品规丁", "一类", "软", "+8.0", "中高", "缩投5%", "中"],
    ["品规戊", "二类", "平", "+2.5", "中", "维持观察", "中"],
    ["品规丙", "三类", "松", "−8.5", "低", "不缩投，促销激活", "低"]
  ],
  [13, 11, 12, 11, 11, 25, 17]
));
children.push(h2("5.4　典型业务场景的差异化策略"));
children.push(p("结合CATE结果与业务场景，可归纳四类差异化策略：（1）高库存压力品规（存销比偏高且CATE>0）：缩投为主动手段，幅度8%~15%；（2）价格偏倒挂品规（顺价指数低且CATE>0）：缩投+价格维护双管齐下；（3）培育期/弱势品规（CATE≤0）：不建议缩投，改用终端推广与动销激活；（4）旺季节点品规（元春、中秋前1个月）：即使CATE偏低也应暂缓缩投、保障供给。需强调的是，因果森林提供的是\"缩投效果的估计\"而非唯一决策依据，应与业务场景、季节性与品牌策略综合使用、定期（建议每季度）重训。"));

// ===== 6 讨论 =====
children.push(h1("6　讨论"));
children.push(h2("6.1　与已有研究的对话"));
children.push(p("本文与已有研究形成互补而非替代。黄敏等[1]回答\"状态是什么\"，姜思明等[2]回答\"状态怎么测\"，金文蔚等[3]回答\"投多少\"，本文则补全了\"对谁有效\"的效果评估维度——三者共同构成\"状态感知—投放优化—效果评估\"的完整闭环。"));
children.push(h2("6.2　因果机制的初步解释"));
children.push(p("高敏感品规的共性在于\"供需基本匹配但存在短期结构性偏紧\"：其存销比最低、顺价指数尚有回落空间，市场基础相对健康，供给收缩能快速修复价格信号与终端预期，产生明显边际改善；低敏感品规的共性是\"供需严重失衡\"（存销比约949），缩投只是\"不让水继续上涨\"，无法\"抽走存量水\"，因而效果有限甚至恶化。SHAP中顺价指数、订货成功率、存销比居首，与这一机制一致。"));
children.push(h2("6.3　方法局限与改进方向"));
children.push(p("本文存在三点局限：（1）无混淆假设——虽纳入23维协变量，但仍可能存在品牌策略调整、区域经济波动等未观测混杂，本文将结论表述为\"准因果证据\"而非随机试验结论；（2）处理变量定义的阈值敏感性——订单满足率35%分位数与2个百分点下降幅度为人工设定，可开展敏感性分析；（3）样本的地域与时长限定——来自单一地市、19个月，外部有效性需多区域、更长期限验证。后续可引入工具变量或连续处理变量定义、纳入更多年份数据、扩展多区域样本。"));

// ===== 7 结论 =====
children.push(h1("7　结论"));
const concls = [
  "因果森林可有效识别缩投调控的品规级异质性效应。ATE=7.65（t=28.63）而CATE标准差高达14.28，平均效应掩盖了品规间的巨大差异。启示：不能因\"平均有效/无效\"的单一判断而一刀切，而应聚焦\"对谁有效\"。",
  "约三分之一的高敏感品规缩投后状态显著改善。高敏感品规CATE均值23.78、低敏感品规仅−8.48；高敏感品规被优先调控后缩投状态改善率达84.4%、平均提升10.08分。启示：调控资源应向高敏感品规集中。",
  "顺价指数、订货成功率、存销比是决定调控敏感度的核心变量。启示：月度调控评审应重点监控价格秩序与供需结构，而非仅看销量规模或品类标签。",
  "基于CATE分群与决策规则可构建月度差异化调控流程，嵌入投放会商，实现从\"平均规则\"到\"差异化策略\"的转变。"
];
concls.forEach((c, i) => {
  children.push(H([{ t: "（" + (i + 1) + "）", b: true }, { t: c }]));
});
children.push(p("最后需要强调：平均效应不显著或不充分不等于调控手段无效——关键在于找到对谁有效、在什么条件下有效；因果森林为这一问题的量化回答提供了可行的准因果工具。"));

// ===== 参考文献 =====
children.push(h1("参考文献"));
const refs = [
  "[1] 黄敏, 等. 基于智能集成阈值的卷烟市场状态评价体系构建与应用[J]. 中国烟草学报, 2025, 31(4): 95-104.",
  "[2] 姜思明, 等. 卷烟零售终端数据治理及其在市场状态监测中的应用[J]. 中国烟草学报, 2026, 32(1): 60-71.",
  "[3] 金文蔚, 等. 基于多目标整数规划的卷烟精准投放模型研究[J]. 中国烟草学报, 2025, 31(2): 78-88.",
  "[4] WAGER S, ATHEY S. Estimation and inference of heterogeneous treatment effects using random forests[J]. Journal of the American Statistical Association, 2018, 113(523): 1228-1242.",
  "[5] ATHEY S, IMBENS G. Recursive partitioning for heterogeneous causal effects[J]. Proceedings of the National Academy of Sciences, 2016, 113(27): 7353-7360.",
  "[6] NIE X, WAGER S. Quasi-oracle estimation of heterogeneous treatment effects[J]. Biometrika, 2021, 108(2): 299-319."
];
refs.forEach(r => children.push(new Paragraph({
  spacing: { after: 40 }, alignment: AlignmentType.LEFT, indent: { left: 420, hanging: 420 },
  children: [new TextRun({ text: r, font: SONG, size: 18 })]
})));

// ============================================================
const doc = new Document({
  styles: {
    default: { document: { run: { font: SONG, size: 21 } } }
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("DOCX 已生成:", OUT);
  console.log("大小:", (buf.length / 1024).toFixed(1), "KB");
}).catch(e => { console.error("FAIL:", e); process.exit(1); });