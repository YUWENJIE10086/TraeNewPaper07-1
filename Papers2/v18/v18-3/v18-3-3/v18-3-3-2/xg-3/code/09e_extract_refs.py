# -*- coding: utf-8 -*-
"""检查可用的PDF库并从指定论文首页提取文献题录信息"""
import sys, os, glob
from pypdf import PdfReader

base = r"D:\TraeNewPaper07-1\中国烟草学报等三大刊"
targets = ["崔建华", "端木杰", "李焕森", "王锐", "骆宇峰", "蒋兴恒", "欧阳世波", "张益明", "蒋晨辰", "杨佳东"]
for name in targets:
    hits = glob.glob(os.path.join(base, f"*{name}*.pdf"))
    if not hits:
        print(f"\n### {name}: NOT FOUND"); continue
    p = hits[0]
    print(f"\n##### {name}: {os.path.basename(p)}")
    try:
        r = PdfReader(p)
        t = (r.pages[0].extract_text() or "") if r.pages else ""
        print(t[:900])
    except Exception as e:
        print("ERR", e)