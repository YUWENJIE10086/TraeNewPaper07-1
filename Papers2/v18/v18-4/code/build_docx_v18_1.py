# -*- coding: utf-8 -*-
"""论文 v17 → DOCX 构建脚本（公式为标准 OMML 可编辑 Word 公式）。

解析 论文v17.html，生成符合《中国烟草学报》排版规范的 DOCX：
- 标题/摘要/Keywords
- 一~三级标题（黑体、顶格）
- 正文（首行缩进、宋体）
- 公式：Word 原生 OMML（m:oMath），Word 中可点击为"公式"对象再编辑
- 三线表、插图（居中）与双语图注/表注
- 参考文献
"""
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from lxml import etree

BASE = Path(r"D:\TraeNewPaper07-1\Papers2\v18\v18-4")
HTML = BASE / "论文v18-1.html"
TEMPLATE = BASE / "rendered" / "论文模板.docx"
OUT = BASE / "论文v18-1.docx"
CONTENT_W = 15.92  # cm

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


# ---------------------------------------------------------------------------
# OMML 公式构建符：输出 m:oMath 内的 XML 片段（不重复 OMML 容器前缀）
# ---------------------------------------------------------------------------
def _q(tag):
    return "{%s}%s" % (M_NS, tag)


def om_run(text, sty=None):
    """普通数学 run，可选 sty: i(斜体) / p(正体)。"""
    rpr = "<m:rPr>%s</m:rPr>" % ('<m:sty m:val="%s"/>' % sty if sty else "")
    return "<m:r>%s<m:t xml:space=\"preserve\">%s</m:t></m:r>" % (rpr, text)


def om_i(text):
    return om_run(text, "i")


def om_sub(base, sub):
    return ("<m:sSub><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>" % (base, sub))


def om_sup(base, sup):
    return ("<m:sSup><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>" % (base, sup))


def om_subsup(base, sub, sup):
    return ("<m:sSubSup><m:e>%s</m:e><m:sub>%s</m:sub>"
            "<m:sup>%s</m:sup></m:sSubSup>" % (base, sub, sup))


def om_frac(num, den):
    return ("<m:f><m:num>%s</m:num><m:den>%s</m:den></m:f>" % (num, den))


def om_acc(base, ch="ˆ"):
    return ("<m:acc><m:accPr><m:chr m:val=\"%s\"/></m:accPr>"
            "<m:e>%s</m:e></m:acc>" % (ch, base))


def om_sum(sub, sup, body):
    """大累加符号 Σ，带上下限与主体。sub/sup 为 OMML 片段。"""
    subsup = "<m:sub>%s</m:sub><m:sup>%s</m:sup>" % (sub or om_run(""), sup or om_run(""))
    return ("<m:nary><m:naryPr><m:chr m:val=\"∑\"/><m:limLoc m:val=\"subSup\"/>"
            "<m:grow m:val=\"1\"/></m:naryPr>%s<m:e>%s</m:e></m:nary>"
            % (subsup, body))


def om_paren(body):
    return ("<m:d><m:dPr><m:begChr m:val=\"(\"/><m:endChr m:val=\")\"/>"
            "</m:dPr><m:e>%s</m:e></m:d>" % body)


def om_had(body):
    """换行分组（用于逗号分隔的多段）不做处理，直接返回。"""
    return body


# --- 十个公式的 OMML 主体（不含编号） ---------------------------------------


def F1():
    return (om_sub(om_i("S"), "it") + "=" + om_run("100×") +
            om_sum(om_i("j=1"), om_i("p"),
                   om_sub(om_i("w"), om_i("j")) + om_sub(om_i("z"), "ijt")) +
            om_run(",") + om_sum(om_i("j=1"), om_i("p"), om_sub(om_i("w"), om_i("j"))) +
            "=" + om_run("1"))


def F2():
    return om_sub(om_i("Y"), "it") + "=" + om_sub(om_i("S"), "i,t+1") + "−" + om_sub(om_i("S"), "it")


def F3():
    return (om_sub(om_i("τ"), om_paren(om_i("x"))) + "=" + om_i("E") +
            om_run("[") + om_i("Y") + om_run("(1)−") + om_i("Y") + om_run("(0)") +
            om_run("|") + om_i("X") + om_run("=") + om_i("x") + om_run("]"))


def F4():
    return (om_sub(om_i("m"), om_paren(om_i("x"))) + "=" + om_i("E") +
            om_run("(") + om_i("Y") + om_run("|") + om_i("X") + om_run("=") + om_i("x") + om_run(")") +
            om_run(",") + om_sub(om_i("e"), om_paren(om_i("x"))) + "=" + om_i("P") +
            om_run("(") + om_i("T") + om_run("=1|") + om_i("X") + om_run("=") + om_i("x") + om_run(")"))


def F5():
    return (om_sub(om_acc(om_i("Y"), "ˆ"), om_i("i")) + "=" + om_sub(om_i("Y"), om_i("i")) + "−" +
            om_acc(om_sub(om_i("m"), om_paren(om_i("X"))), "ˆ") + om_run(",") +
            om_sub(om_acc(om_i("T"), "˜"), om_i("i")) + "=" + om_sub(om_i("T"), om_i("i")) + "−" +
            om_acc(om_sub(om_i("e"), om_paren(om_i("X"))), "ˆ"))


def F6():
    return (om_sub(om_i("ρ"), om_i("i")) + "=" +
            om_frac(om_sub(om_acc(om_i("Y"), "ˆ"), om_i("i")),
                    om_sub(om_acc(om_i("T"), "˜"), om_i("i"))) + om_run(",") +
            om_sub(om_i("ω"), om_i("i")) + "=" +
            om_sup(om_sub(om_acc(om_i("T"), "˜"), om_i("i")), om_run("2")))


def F7():
    return (om_acc(om_i("τ"), "ˆ") + "=" + om_sub(om_run("arg min"), om_i("τ")) +
            om_sum(om_i("i=1"), om_i("n"),
                   om_sup(om_paren(om_sub(om_acc(om_i("Y"), "ˆ"), om_i("i")) + "−" +
                                   om_sub(om_i("τ"), om_paren(om_i("X"))) +
                                   om_sub(om_acc(om_i("T"), "˜"), om_i("i"))), om_run("2"))))


def F8():
    return (om_acc(om_i("τ"), "ˆ") + "=" + om_sub(om_run("arg min"), om_i("τ")) +
            om_sum(om_i("i=1"), om_i("n"),
                   om_sub(om_i("ω"), om_i("i")) +
                   om_sup(om_paren(om_sub(om_i("ρ"), om_i("i")) + "−" +
                                   om_sub(om_i("τ"), om_paren(om_i("X")))), om_run("2"))))


def F9():
    return (om_sub(om_acc(om_i("τ"), "ˆ"), om_paren(om_i("x"))) + "=" +
            om_sup(om_i("B"), om_run("−1")) +
            om_sum(om_i("b=1"), om_i("B"),
                   om_sub(om_acc(om_i("τ"), "ˆ"), om_i("b")) + om_paren(om_i("x"))))


def F10():
    return (om_sub(om_i("g"), om_paren(om_i("x"))) + "=" + om_sub(om_i("φ"), "0") + "+" +
            om_sum(om_i("j=1"), om_i("p"), om_sub(om_i("φ"), om_i("j"))))


def F11():
    left = om_run("max ") + om_sum(om_i("r=1"), om_i("R"),
                                  om_sub(om_i("I"), om_i("r")) +
                                  om_acc(om_i("τ"), "ˆ") + om_paren(om_sub(om_i("x"), om_i("r"))) +
                                  om_sub(om_i("c"), om_i("r")))
    csum = om_sum(om_i("r=1"), om_i("R"), om_sub(om_i("c"), om_i("r")))
    return (left + om_run(", s.t. ") + csum + "≤" + om_i("C") +
            om_run(", 0≤") + om_sub(om_i("c"), om_i("r")) + "≤" +
            om_acc(om_sub(om_i("c"), om_i("r")), "¯"))


FORMULAS = {
    1: F1(), 2: F2(), 3: F3(), 4: F4(), 5: F5(),
    6: F6(), 7: F7(), 8: F8(), 9: F9(), 10: F10(), 11: F11(),
}


def add_omml_formula(doc, formula_no):
    """向文档添加一个标准 OMML 公式段落，编号靠右。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    tabs = p.paragraph_format.tab_stops
    tabs.add_tab_stop(Cm(CONTENT_W / 2), WD_TAB_ALIGNMENT.CENTER)
    tabs.add_tab_stop(Cm(CONTENT_W), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t")

    # 构造 m:oMath 元素
    xml = ('<m:oMath xmlns:m="%s">%s</m:oMath>' % (M_NS, FORMULAS[formula_no]))
    omath = etree.fromstring(xml)
    p._p.append(omath)

    # 编号 run（右制表位，正体小四）
    p.add_run("\t")
    run = p.add_run("（%d）" % formula_no)
    run.font.size = Pt(12)
    runPr = run._element.get_or_add_rPr()
    rfonts = runPr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); runPr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), "宋体"); rfonts.set(qn("w:ascii"), "Times New Roman")
    return p


# ---------------------------------------------------------------------------
# HTML 块解析（复用 v16-2 解析器）
# ---------------------------------------------------------------------------
class BlockParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.in_p = None
        self.raw = []
        self.in_table = False
        self.rows = []
        self.row = None
        self.cell = None
        self.cell_html = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        if tag in {"h1", "h2", "h3", "p"}:
            self.in_p = (tag, cls, []); self.raw = self.in_p[2]
        elif tag == "div" and cls in {"formula", "caption", "figcap"} :
            self.in_p = ("div", cls, []); self.raw = self.in_p[2]
        elif tag == "table":
            self.in_table = True; self.rows = []
        elif tag == "tr" and self.in_table:
            self.row = []
        elif tag in {"td", "th"} and self.in_table:
            self.cell = []; self.cell_html = []
        elif tag == "img":
            src = attrs.get("src", "")
            if src:
                self.blocks.append(("img", src))
        elif self.in_p is not None:
            self.raw.append(self.raw_tag(tag, attrs))

    def raw_tag(self, tag, attrs):
        out = "<" + tag
        for k, v in attrs.items():
            out += ' %s="%s"' % (k, v)
        return out + ">"

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data); self.cell_html.append(data)
        elif self.in_p is not None:
            self.raw.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append("".join(self.cell)); self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.in_table:
            self.blocks.append(("table", self.rows)); self.in_table = False
        elif self.in_p is not None and tag == self.in_p[0]:
            html = "".join(self.raw)
            self.blocks.append((self.in_p[0], self.in_p[1], html))
            self.in_p = None


class Inline:
    TOKEN = re.compile(r"(<[^>]+>)|([^<]+)")

    def __init__(self):
        self.flags = {"i": False, "b": False, "sub": False, "sup": False}

    def parse(self, html):
        runs = []
        buf = ""
        for tag, text in self.TOKEN.findall(html):
            if text:
                buf += unescape(text)
            else:
                if buf:
                    runs.append((buf, dict(self.flags))); buf = ""
                self._apply(tag)
        if buf:
            runs.append((buf, dict(self.flags)))
        return runs

    def _apply(self, tag):
        close = tag.startswith("</")
        name = re.sub(r"[</>]", "", tag).strip().split()[0] if tag else ""
        name = name.lower()
        if name in self.flags:
            self.flags[name] = not close


def clean(text):
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text.strip()


def clear_document(doc):
    body = doc._body._element
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def set_run_font(run, east="宋体", west="Times New Roman", size=12, bold=False, italic=None):
    run.font.name = west
    run.font.size = Pt(size)
    run.bold = bold
    if italic is not None:
        run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), east)
    rfonts.set(qn("w:ascii"), west)
    rfonts.set(qn("w:hAnsi"), west)


def add_rich_text(p, inline_runs, base_size=12, east="宋体"):
    for text, fl in inline_runs:
        run = p.add_run(text)
        if fl.get("sub"):
            run.font.subscript = True
        if fl.get("sup"):
            run.font.superscript = True
        size = base_size
        if fl.get("sub") or fl.get("sup"):
            size = max(8, base_size - 2)
        set_run_font(run, east=east, size=size, bold=fl.get("b", False), italic=fl.get("i", None))


def add_para(doc, html, size=12, bold=False, align=None, first_indent=True, east="宋体"):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    if first_indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    add_rich_text(p, Inline().parse(html), base_size=size, east=east)
    return p


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(clean(text))
    size = 15 if level == 1 else 12 if level == 2 else 10.5
    set_run_font(run, east="黑体", size=size, bold=True)
    return p


def add_caption_block(doc, html):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    parts = clean(html.replace("<br>", "\n")).split("\n")
    runs = Inline().parse(parts[0])
    add_rich_text(p, runs, base_size=9.5, east="黑体")
    for extra in parts[1:]:
        r = p.add_run("\n" + extra)
        set_run_font(r, east="黑体", size=9.5)
    return p


def set_cell_text(cell, text, header=False):
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(clean(text))
    set_run_font(run, east="宋体", size=9, bold=header)


def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders"); tc_pr.append(borders)
    for edge, edge_data in kwargs.items():
        tag = "w:%s" % edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag); borders.append(element)
        for key, val in edge_data.items():
            element.set(qn("w:%s" % key), str(val))


def apply_three_line_table(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    nil = {"val": "nil", "sz": "0", "color": "FFFFFF", "space": "0"}
    thin = {"val": "single", "sz": "6", "color": "000000", "space": "0"}
    medium = {"val": "single", "sz": "12", "color": "000000", "space": "0"}
    for row in table.rows:
        for cell in row.cells:
            set_cell_border(cell, **dict(top=nil, bottom=nil, left=nil, right=nil, insideH=nil, insideV=nil))
    for cell in table.rows[0].cells:
        set_cell_border(cell, **dict(top=medium, bottom=thin, left=nil, right=nil))
    for cell in table.rows[-1].cells:
        set_cell_border(cell, **dict(bottom=medium, left=nil, right=nil))


def add_table(doc, rows):
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    for i, row in enumerate(rows):
        for j in range(cols):
            text = row[j] if j < len(row) else ""
            table.cell(i, j).text = ""
            set_cell_text(table.cell(i, j), text, header=(i == 0))
    apply_three_line_table(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_image(doc, src):
    img_path = BASE / src
    if not img_path.exists():
        print("  [缺图]", src); return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(img_path), width=Inches if False else Pt(init_width(img_path)))
    p.paragraph_format.space_after = Pt(2)


def _img_width_px(path):
    from docx.shared import Inches
    return None


def init_width(img_path):
    return 430  # pt ≈ 15.2cm，占满版芯


def add_footer_page_number(doc):
    footer = doc.sections[0].footer
    for p in list(footer.paragraphs):
        p.clear()
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1); run._r.append(it); run._r.append(f2)
    set_run_font(run, size=9)


def build():
    text = HTML.read_text(encoding="utf-8")
    article = re.search(r"<article[^>]*>(.*)</article>", text, flags=re.S).group(1)
    parser = BlockParser(); parser.feed(article)

    doc = Document(str(TEMPLATE)) if TEMPLATE.exists() else Document()
    clear_document(doc)
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin = sec.right_margin = Cm(2.54)
    sec.header_distance = Cm(1.5); sec.footer_distance = Cm(1.5)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"; normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    bl = parser.blocks
    i = 0
    while i < len(bl):
        kind, *rest = bl[i]
        if kind == "h1":
            cls, html = rest
            if cls == "paper-title":
                add_para(doc, html, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False)
            else:
                add_heading(doc, html, 1)
        elif kind == "h2":
            add_heading(doc, rest[1], 2)
        elif kind == "h3":
            add_heading(doc, rest[1], 3)
        elif kind == "p":
            cls, html = rest
            if cls in {"paper-subtitle", "meta"}:
                add_para(doc, html, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=False)
            elif cls == "note":
                add_para(doc, html, size=10.5, first_indent=False)
            else:
                add_para(doc, html, size=12)
        elif kind == "div":
            cls, html = rest
            if cls == "formula":
                # 取公式编号（span 闭合在解析器中不保留，只匹配开头）
                pm = re.search(r'<span class="n">\s*（(\d+)）', html)
                no = int(pm.group(1)) if pm else None
                if no in FORMULAS:
                    add_omml_formula(doc, no)
                else:
                    add_para(doc, re.sub(r'<span class="n">.*?</span>', '', html, flags=re.S),
                             size=12, east="Cambria Math")
            else:
                add_caption_block(doc, html)
        elif kind == "table":
            cap = ""
            nxt = bl[i + 1] if i + 1 < len(bl) else None
            if nxt and nxt[0] == "div" and nxt[1] == "caption":
                cap = nxt[2]; i += 1
            if cap:
                add_caption_block(doc, cap)
            add_table(doc, rest[0])
            doc.paragraphs[-1].paragraph_format.space_after = Pt(4)
        elif kind == "img":
            from docx.shared import Inches
            src = rest[0]
            img_path = BASE / src
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(); run.add_picture(str(img_path), width=Inches(6.0))
            p.paragraph_format.space_after = Pt(2)
            nxt = bl[i + 1] if i + 1 < len(bl) else None
            if nxt and nxt[0] == "div" and nxt[1] == "figcap":
                add_caption_block(doc, nxt[2]); i += 1
        i += 1

    add_footer_page_number(doc)
    doc.save(str(OUT))
    print("已生成", OUT)


if __name__ == "__main__":
    build()

