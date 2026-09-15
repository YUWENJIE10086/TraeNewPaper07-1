# -*- coding: utf-8 -*-
"""批量提取参考论文正文为文本，便于结构化研读。"""
from pathlib import Path
import pymupdf

SRC = Path(r"D:\TraeNewPaper07-1\中国烟草学报等三大刊")
OUT = Path(r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\refs_text")
OUT.mkdir(exist_ok=True)

for f in sorted(SRC.glob("*.pdf")):
    out = OUT / (f.stem + ".txt")
    if out.exists():
        print("skip (exists):", f.name)
        continue
    try:
        doc = pymupdf.open(str(f))
        parts = []
        for i, page in enumerate(doc):
            parts.append(f"\n===== PAGE {i+1} =====\n")
            parts.append(page.get_text("text"))
        doc.close()
        text = "\n".join(parts)
        out.write_text(text, encoding="utf-8")
        print(f"OK {f.name}: {len(text)} chars, {len(doc)} pages->" if False else f"OK {f.name}: {len(text)} chars")
    except Exception as e:
        print("ERR", f.name, e)