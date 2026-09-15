# -*- coding: utf-8 -*-
"""分进程单图重跑:避免一次性生成全部图造成内存溢出。
用法: python run_fig.py fig2   (可选 fig_density_advanced / fig10 / fig8 等)"""
import sys, os
import importlib.util
os.environ.pop("MPLBACKEND", None)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["figure.dpi"] = 110
matplotlib.rcParams["savefig.dpi"] = 110
spec = importlib.util.spec_from_file_location("gf", r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\code\03_generate_figures.py")
gf = importlib.util.module_from_spec(spec); spec.loader.exec_module(gf)
# 覆盖全局高DPI设置
gf.rcParams["figure.dpi"] = 110
gf.rcParams["savefig.dpi"] = 110
plt.close("all")
which = sys.argv[1]
fn = getattr(gf, which)
fn()
import pathlib
plt.close("all")
print("OK 生成完成:", which, "| 波形图勾选→ figs 目录")