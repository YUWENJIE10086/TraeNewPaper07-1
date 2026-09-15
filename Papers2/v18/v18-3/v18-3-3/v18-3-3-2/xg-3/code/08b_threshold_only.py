# -*- coding: utf-8 -*-
"""阈值敏感性独立重算：P25/P30/P35/P40/P45 五档 TWFE（statsmodels 聚类稳健）。
在独立进程中运行，避免与置换检验共享内存导致 500 次置换后的 OOM。
结果写回 metrics.json 的 threshold_sensitivity 字段。"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
BASE = Path(__file__).resolve().parents[1]; D = BASE / "data"
THRESH_DEFS = [
    ("主定义：月内P35且下降>2", 0.35, 2),
    ("月内P25且下降>2", 0.25, 2),
    ("月内P30且下降>2", 0.30, 2),
    ("月内P40且下降>3", 0.40, 3),
    ("月内P45且下降>3", 0.45, 3),
]

def twfe(df, outcome, treat="Ts"):
    fit = smf.ols(f"{outcome} ~ {treat} + C(code) + C(ym)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["code"]})
    return {"coef": float(fit.params[treat]), "se": float(fit.bse[treat]),
            "p": float(fit.pvalues[treat]),
            "ci": [float(fit.conf_int().loc[treat, 0]), float(fit.conf_int().loc[treat, 1])]}

def main():
    d = pd.read_csv(D / "analysis_panel.csv", encoding="utf-8-sig")
    d["code"] = d["code"].astype(str); d["ym"] = d["ym"].astype(str)
    p = pd.read_csv(D / "raw_panel.csv", encoding="utf-8-sig").sort_values(["code", "ym"]).reset_index(drop=True)
    p["code"] = p["code"].astype(str); p["ym"] = p["ym"].astype(str)
    p["prev_fill"] = p.groupby("code")["fill"].shift(1)
    defs = []
    for name, qv, drop in THRESH_DEFS:
        q = p.groupby("ym")["fill"].transform(lambda x: x.quantile(qv))
        tmp = p[["code", "ym"]].copy()
        tmp["Ts"] = ((p["fill"] <= q) & ((p["prev_fill"] - p["fill"]) > drop)).astype(int)
        m = tmp.merge(d[["code", "ym", "Y_clean"]], on=["code", "ym"])
        r = twfe(m, "Y_clean", "Ts")
        defs.append({"definition": name, "treated": int(m.Ts.sum()), **r})
    mf = D / "metrics.json"
    metrics = json.loads(mf.read_text(encoding="utf-8"))
    metrics["threshold_sensitivity"] = defs
    mf.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(defs, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()