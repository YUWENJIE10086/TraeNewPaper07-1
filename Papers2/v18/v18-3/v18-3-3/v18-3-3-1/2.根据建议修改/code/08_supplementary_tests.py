from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "data" / "analysis_panel.csv")
t = df[df["T"] == 1].copy()
q = t["CATE"].quantile(2/3)
t["group"] = np.where(t["CATE"] >= q, "高敏感", "其余")
hi = t.loc[t.group == "高敏感", "Y_clean"].dropna().to_numpy(float)
ot = t.loc[t.group == "其余", "Y_clean"].dropna().to_numpy(float)
u, p = mannwhitneyu(hi, ot, alternative="two-sided")
rng = np.random.default_rng(20260913)
boot = []
for _ in range(1000):
    boot.append(hi[rng.integers(0, len(hi), len(hi))].mean() - ot[rng.integers(0, len(ot), len(ot))].mean())
boot = np.asarray(boot)
out = {
    "high_n": int(len(hi)), "other_n": int(len(ot)),
    "high_median": float(np.median(hi)), "high_q1": float(np.quantile(hi,.25)), "high_q3": float(np.quantile(hi,.75)),
    "other_median": float(np.median(ot)), "other_q1": float(np.quantile(ot,.25)), "other_q3": float(np.quantile(ot,.75)),
    "mann_whitney_u": float(u), "mann_whitney_p": float(p),
    "mean_difference": float(hi.mean()-ot.mean()),
    "bootstrap_ci": [float(np.quantile(boot,.025)), float(np.quantile(boot,.975))],
    "bootstrap_reps": 1000,
}
(BASE / "data" / "supplementary_tests.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
