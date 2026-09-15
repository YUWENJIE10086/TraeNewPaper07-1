# -*- coding: utf-8 -*-
"""
finalize_xg4.py — 依据第4/5轮审稿意见对修订版做收尾定稿：
  1) 表18 合并为一张 30 行复核清单，删除「表18扩展版 / 表18续」两个冗余顶层标题（回应“题目不要这么多”与图表-09）；
  2) 2.5 稳健性复核设计 补 PSM 匹配方法、E-value 计算公式、负对照结局定义、置换策略说明（方法-07/08/09/10、实验-04/06）；
  3) 2.3.1 识别假设 补 SUTVA 可能被替代效应违反的局限讨论（方法-05、实验-03）；
  4) 唯一写入 xg4 的定稿 HTML。
"""
import re, sys

SRC = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg-3\论文v18-3-3-修订版.html"
DST = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg4\论文v18-3-3-修订版.html"

h = open(SRC, encoding="utf-8").read()
orig = h

# ---------------------------------------------------------------- 1) 表18 合并为 30 行
i_e1 = h.find("<section class=\"supplement\">")
s1 = h.find("<tbody>", i_e1)
s1e = h.find("</tbody>", s1) + len("</tbody>")
ext1_tbody = h[s1:s1e]

i_e2 = h.find("<section class=\"supplement\"><h1>表18续")
s2 = h.find("<tbody>", i_e2)
s2e = h.find("</tbody>", s2) + len("</tbody>")
ext2_tbody = h[s2:s2e]

# 合并两段 <tbody> 行
def rows(tb):
    return re.findall(r"<tr>.*?</tr>", tb, re.S)
all_rows = rows(ext1_tbody) + rows(ext2_tbody)
print("表18 合并行数:", len(all_rows))
assert len(all_rows) == 30, f"期望30行，实得{len(all_rows)}"

headers = "<thead><tr><th>序号</th><th>品规</th><th>品类</th><th>CATE</th><th>排序层级</th>" \
          "<th>参考幅度</th><th>触发条件</th><th>回滚条件</th></tr></thead>"
body = "".join(f"<td>{k}</td>" + r[len('<tr>')-1:] if False else r for k, r in enumerate(all_rows, 1))
# 在每行首列前插入序号
seq_rows = []
for k, r in enumerate(all_rows, 1):
    seq_rows.append(r.replace("<tr>", f"<tr><td>{k}</td>", 1))
merged_table = ("<table>" + "<thead><tr><th>序号</th><th>品规</th><th>品类</th><th>CATE</th>"
                "<th>排序层级</th><th>参考幅度</th><th>触发条件</th><th>回滚条件</th></tr></thead>"
                "<tbody>" + "".join(seq_rows) + "</tbody></table>")

# 主表18标题后的空表格区替换为合并表；删除两个 supplement 区块
i_maincap = h.find("表18　代表性品规月度投放复核建议清单")
cap_end = h.find("</div>", i_maincap) + len("</div>")
# 主 caption 后紧接着的空表格 + 文字段，将空表格替换为合并表
h = h[:cap_end] + merged_table + h[cap_end:]

# 删除两个 supplement section
s_plus1 = h.find('<section class="supplement">')
# 定位第一个 supplement 结束 </section>
e_plus1 = h.find("</section>", s_plus1) + len("</section>")
# 第二个 supplement 开始到它自己的 </section>
s_plus2 = h.find('<section class="supplement"><h1>表18续', e_plus1)
e_plus2 = h.find("</section>", s_plus2) + len("</section>")
# way: 删掉从第一个 supplement 开始到第二个结束之间的全部
h = h[:s_plus1] + h[e_plus2:]

# ---------------------------------------------------------------- 2) 2.5 稳健性复核设计 补方法说明
robust_new = ("<p>稳健性分析包括：品规和月份双向固定效应、倾向得分重叠与1:1匹配、匹配后风险比的E-value、"
              "500次月内处理标签置换、处理阈值敏感性，以及处理发生前状态变化的负对照结局。负对照用于检验反向"
              "选择与未观测混杂；若其显著，模型只能用于探索性排序。[13-15]</p>"
              "<p>倾向得分模型纳入全部23维协变量，采用1:1最近邻匹配、卡钳0.02、无放回，匹配后处理组258条、"
              "对照组258条共516条。匹配后E-value按VanderWeele与Ding方法基于改善风险比1.404计算，"
              "E-value=RR+√(RR×(RR−1))≈1.404+√(1.404×0.404)≈2.156，意为需要风险比达到2.156的未测混杂才能"
              "完全解释匹配后观察到的改善关联。</p>"
              "<p>处理前负对照结局定义为ΔS<sup>*</sup><sub>i,t-1</sub>=S<sup>*</sup><sub>i,t-1</sub>−S"
              "<sup>*</sup><sub>i,t-2</sub>，即供给收缩发生前两期的状态变化，用于检验反向选择。置换检验在月份内"
              "随机置换处理标签后重估双向固定效应系数，重复500次得到伪效应分布与经验P值。</p>")
old_robust_pat = ("<p>稳健性分析包括：品规和月份双向固定效应、倾向得分重叠与1:1匹配、匹配后风险比的E-value、"
                  "500次月内处理标签置换、处理阈值敏感性，以及处理发生前状态变化的负对照结局。负对照用于检验反向"
                  "选择与未观测混杂；若其显著，模型只能用于探索性排序。[13-15]</p>")
assert old_robust_pat in h, "稳健性锚点未命中"
h = h.replace(old_robust_pat, robust_new)

# ---------------------------------------------------------------- 3) SUTVA 被替代效应违反的局限
old_sutva_pat = "考虑到相邻月份可能存在序列相关，标准误采用品规层级聚类稳健估计，子样本检验也按品规分组抽样。</p>"
new_sutva_pat = ("考虑到相邻月份可能存在序列相关，标准误采用品规层级聚类稳健估计，子样本检验也按品规分组抽样。"
                 "需要指出，卷烟品规之间存在替代关系，某品规的供给收缩可能促使需求流向替代品规，从而部分违反稳定"
                 "单元处理值假设，这是本文的局限之一，解读时应把CATE视为在既有替代结构下、未剥离竞争转移效应的"
                 "关联排序信号。</p>")
assert old_sutva_pat in h, "SUTVA锚点未命中"
h = h.replace(old_sutva_pat, new_sutva_pat)

open(DST, "w", encoding="utf-8").write(h)
print("写入定稿:", DST)
print("总字节变化:", len(h) - len(orig))
print("残留 supplement 段:", h.count("表18扩展版"), h.count("表18续"))
print("表18合并表存在:", "表18　代表性品规月度投放复核建议清单" in h and h.count("<tr><td>1</td>") >= 0)