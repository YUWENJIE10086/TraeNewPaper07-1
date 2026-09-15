# -*- coding: utf-8 -*-
from pathlib import Path
import json
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parents[1]; D=BASE/"data"
m=json.loads((D/"metrics.json").read_text(encoding="utf-8")); p=pd.read_csv(D/"causal_forest_panel.csv",encoding="utf-8-sig"); q=pd.read_csv(D/"psm_smd.csv",encoding="utf-8-sig")
paper=(BASE/"论文v18-4.html").read_text(encoding="utf-8") if (BASE/"论文v18-4.html").exists() else ""
checks={
 "unique_product_month":bool(not p.duplicated(["code","ym"]).any()),
 "covariates_exactly_23":m["covariates"]==23,
 "all_effects_finite":bool(np.isfinite(p[["CATE","CATE_lo","CATE_hi"]]).all().all()),
 "interval_order":bool((p.CATE_lo<=p.CATE_hi).all()),
 "psm_balance_improved":m["psm"]["mean_abs_smd_after"]<m["psm"]["mean_abs_smd_before"],
 "figures_complete":all((BASE/"figures"/f).exists() for f in ["fig1_framework.png","fig2_cate_dist.png","fig3_cate_density_groups.png","fig4_effect_absorption_map.png","fig6_subgroup_forest.png","fig5_priceband_heatmap.png","fig7_trajectory.png","fig8_product_panel.png"]),
 "paper_has_8_figures":paper.count("<img")==8,
 "paper_has_21_tables":paper.count("<table")==21,
 "paper_has_no_nan_cells":">nan<" not in paper.lower(),
 "no_old_claim_7647":abs(m["ate"]-7.647)>.5,
}
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"critical_interpretation":{
 "ate_significant":not (m["ate_ci"][0]<=0<=m["ate_ci"][1]),
 "backtest_baseline_balanced":abs(m["backtest"]["baseline_smd"])<.1,
 "allowed_claim":"平均效应显著为正；处理组内回溯分组仍存在基线差异，改善率差异仅作排序复核证据，不作无偏部署增益解释。"}}
(D/"validation.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(out,ensure_ascii=False,indent=2))
if out["status"]!="PASS":raise SystemExit(1)
