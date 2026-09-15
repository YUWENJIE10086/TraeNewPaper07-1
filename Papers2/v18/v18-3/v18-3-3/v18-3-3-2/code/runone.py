# -*- coding: utf-8 -*-
"""分进程单图重跑:避免一次性生成全部图造成内存溢出。用法 python runone.py fig2"""
import sys
sys.argv = [sys.argv[0], None]
import importlib.util, os
spec = importlib.util.spec_from_file_location("gf", r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\code\03_generate_figures.py")
gf = importlib.util.module_from_spec(spec); spec.loader.exec_module(gf)
import matplotlib.pyplot as plt
plt.close("all")
which = sys.argv[1] if len(sys.argv) > 1 else "fig2"
fn = getattr(gf, which)
fn()
print("OK 生成完成:", which)