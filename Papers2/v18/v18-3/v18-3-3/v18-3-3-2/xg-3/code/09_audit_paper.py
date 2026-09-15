# -*- coding: utf-8 -*-
"""审计当前论文 HTML：核对审稿意见逐条落实情况"""
import io, re, sys

def load(p):
    return io.open(p, encoding="utf-8").read()

def audit(path):
    f = load(path)
    print("=" * 70)
    print("FILE:", path, "| LEN:", len(f))
    print("=" * 70)

    # 标题
    m = re.search(r"<title>(.*?)</title>", f, re.S)
    print("\n[TITLE]", (m.group(1) if m else None))
    mh = re.search(r"<h1[^>]*>(.*?)</h1>", f, re.S)
    print("[H1]", re.sub(r"<[^>]+>", "", mh.group(1)).strip() if mh else None)
    men = re.search(r"<h2[^>]*>(.*?)</h2>", f, re.S)

    # 表/图数量
    tables = re.findall(r"<caption[^>]*>(.*?)</caption>", f, re.S)
    print("\n[TABLE CAPTIONS]", len(tables))
    for i, t in enumerate(tables[:40], 1):
        print(f"   T{i}:", re.sub(r"<[^>]+>", "", t).strip()[:80])

    # 关键词统计
    def cnt(kw):
        return f.count(kw)
    print("\n[KEYWORD COUNTS]")
    for kw in ["缩投", "供给收缩", "诚实因果森林", "95% CI", "95%CI", "1.679",
               "0.659", "1.832", "-0.321", "3.931", "59.3",
               "置换", "500", "P25", "P45", "E-value", "PSM",
               "标准化均值差", "倾向得分匹配", "请填写", "［请填写", "SMD＝", "SMD="]:
        c = cnt(kw)
        if c:
            print(f"   {kw}: {c}")

    # 参考文献计数
    refs_start = f.find("参考文献")
    if refs_start > 0:
        seg = f[refs_start: refs_start + 20000]
        items = re.findall(r"\[\s*\d+\s*\]", seg)
        print("\n[REFERENCE markers after first '参考文献']:", len(items), "unique:", len(set(items)))

    # 置换检验500
    print("\n[placebo mentions]", len(re.findall(r"置换", f)))
    print("[P值格式 sample]")
    for m in re.finditer(r"P\s*=\s*[0-9eE\.\-]+", f):
        pass
    pvals = set(re.findall(r"P\s*=\s*[0-9eE\.]+", f))
    print("   ", list(pvals)[:15])

    print("\n[DONE]", path)

if __name__ == "__main__":
    base = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg-3"
    for p in [base + r"\论文v18-3-3-修订版.html", base + r"\论文v18-3-3.html"]:
        audit(p)