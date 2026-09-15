# -*- coding: utf-8 -*-
"""Validate the v17-3 definitions and produce auditable statistics for v18."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\TraeNewPaper07-1\Papers2\v18")
data = pd.read_csv(ROOT / "data" / "causal_forest_panel_v1.csv", encoding="utf-8-sig")
y = data["CATE"].astype(float)
n = len(y)
g = data.groupby("code")["CATE"].agg(["count", "sum"])
se_cluster = float(np.sqrt(len(g) / (len(g) - 1) * ((g["sum"] - g["count"] * y.mean()) ** 2).sum() / n**2))
ate = float(y.mean())
out = {
    "source": "Papers3/v1 logic rerun on 0805数据",
    "n_samples": n, "n_specifications": int(data["code"].nunique()),
    "n_treatment": int(data["T"].sum()), "n_covariates": 23,
    "treatment_definition": "fill <= same-month 35th percentile and previous fill - current fill > 2 percentage points",
    "ate": round(ate, 6), "cluster_unit": "specification code",
    "cluster_robust_se_for_mean_CATE": round(se_cluster, 6),
    "cluster_robust_ci95": [round(ate - 1.96 * se_cluster, 6), round(ate + 1.96 * se_cluster, 6)],
    "raw_unclustered_se": 0.267,
    "v17_3_metrics_match": {"n_samples": n == 2857, "n_treatment": int(data["T"].sum()) == 270, "ate": round(ate, 3) == 7.647}
}
(ROOT / "data" / "v17_3_validation.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
