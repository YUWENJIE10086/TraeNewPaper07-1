# -*- coding: utf-8 -*-
import re
h = open(r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg4\论文v18-3-3-修订版.html", encoding="utf-8").read()
fs = re.findall(r'<div class="formula">(.*?)</div>', h, re.S)
print("公式数量:", len(fs))
for i, f in enumerate(fs, 1):
    t = re.sub(r"<sup>(.*?)</sup>", r"[^\1]", f, flags=re.S)
    t = re.sub(r"<sub>(.*?)</sub>", r"[\1]", t, flags=re.S)
    t = re.sub(r"<i>|</i>|<span class=\"n\">|</span>", "", t)
    print(f"式{i}:", t.strip()[:130])