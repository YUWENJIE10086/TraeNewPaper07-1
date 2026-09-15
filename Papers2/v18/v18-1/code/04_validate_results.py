# -*- coding: utf-8 -*-
from pathlib import Path
import json
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parents[1]; D=BASE/"data"
m=json.loads((D/"metrics.json").read_text(encoding="utf-8")); p=pd.read_csv(D/"causal_forest_panel.csv",encoding="utf-8-sig"); q=pd.read_csv(D/"psm_smd.csv",encoding="utf-8-sig")
checks={
 "unique_product_month":bool(not p.duplicated(["code","ym"]).any()),
 "covariates_exactly_23":m["covariates"]==23,
 "all_effects_finite":bool(np.isfinite(p[["CATE","CATE_lo","CATE_hi"]]).all().all()),
 "interval_order":bool((p.CATE_lo<=p.CATE_hi).all()),
 "psm_balance_improved":m["psm"]["mean_abs_smd_after"]<m["psm"]["mean_abs_smd_before"],
 "figures_complete":len(list((BASE/"figures").glob("*.png")))==8,
 "no_old_claim_7647":abs(m["ate"]-7.647)>.5,
}
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"critical_interpretation":{
 "ate_significant":not (m["ate_ci"][0]<=0<=m["ate_ci"][1]),
 "backtest_baseline_balanced":abs(m["backtest"]["baseline_smd"])<.1,
 "allowed_claim":"平均效应置信区间跨0；回溯分组存在明显基线差异，只能用于复核排序，不能作部署成效或严格因果提升解释。"}}
(D/"validation.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(out,ensure_ascii=False,indent=2))
if out["status"]!="PASS":raise SystemExit(1)
