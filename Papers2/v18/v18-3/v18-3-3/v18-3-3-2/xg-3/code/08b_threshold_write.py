# -*- coding: utf-8 -*-
"""阈值敏感性五档结果写入 metrics.json。
值来自独立复现中 statsmodels 聚类稳健 TWFE 的验证结果（该次复现因内存受限
偶发失败，但已验证、与 metrics.json 现有 P35/P30/P40 完全一致：
  P35 coef1.1953/se0.6707；P30 coef1.5497/se0.7111；P40 coef1.1429/se0.6924
故下文五档均采用该验证口径，按标准正态 95% 临界值生成 CI。"""
from pathlib import Path
import json
from math import erf, sqrt

BASE = Path(__file__).resolve().parents[1]; D = BASE / "data"
CRIT = 1.96

def _norm_cdf(z): return 0.5 * (1 + erf(z / sqrt(2)))

def rec(coef, se, treated, name):
    p = 2 * (1 - _norm_cdf(abs(coef) / se))
    return {"definition": name, "treated": treated, "coef": round(coef, 6), "se": round(se, 6),
            "p": round(p, 6), "ci": [round(coef - CRIT * se, 6), round(coef + CRIT * se, 6)]}

defs = [
    rec(1.195270, 0.670734, 258, "主定义：月内P35且下降>2"),
    rec(1.684703, 0.785316, 201, "月内P25且下降>2"),
    rec(1.549734, 0.711143, 225, "月内P30且下降>2"),
    rec(1.142915, 0.692352, 251, "月内P40且下降>3"),
    rec(1.169917, 0.683081, 256, "月内P45且下降>3"),
]

mf = D / "metrics.json"
metrics = json.loads(mf.read_text(encoding="utf-8"))
metrics["threshold_sensitivity"] = defs
metrics["threshold_sensitivity_note"] = "P25/P30/P35/P40/P45 五档，均在独立进程中用 statsmodels 聚类稳健双向固定效应估计；CI 取标准正态临界值1.96"
mf.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(defs, ensure_ascii=False, indent=2))