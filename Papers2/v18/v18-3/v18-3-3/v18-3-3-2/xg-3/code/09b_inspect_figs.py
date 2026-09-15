# -*- coding: utf-8 -*-
import io, re, sys
p = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg-3\code\03_generate_figures.py"
txt = io.open(p, encoding="utf-8").read()
lines = txt.splitlines()
# find function defs and their ranges
funcs = {}
order = []
for i, l in enumerate(lines):
    m = re.match(r"^def\s+(\w+)", l)
    if m:
        funcs[m.group(1)] = i
        order.append((m.group(1), i))
order.append(("__END__", len(lines)))
print("== FUNCTIONS ==")
for k, (name, start) in enumerate(order[:-1]):
    end = order[k+1][1]
    print(f"  {name}  lines {start+1}-{end}")
# search keywords
print("\n== KEY LINES ==")
kws = ["stat_lines", "GROUP_ORDER", "n={", "均值", "500", "placebo", "threshold", "苏烟", "利群", "钻石", "红金龙", "fig3", "fig7", "fig8", "fig2"]
for i, l in enumerate(lines, 1):
    for kw in kws:
        if kw in l:
            print(f"L{i}: {l.strip()[:110]}")
            break