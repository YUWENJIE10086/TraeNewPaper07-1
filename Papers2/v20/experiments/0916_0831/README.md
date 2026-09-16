# v20-8 final experiment assets — 0916_0831

Source experiment: `../0916_0827/` (corrected P35 by `ym`).

- `fig1...fig6`: figures used by v20-8 manuscript.
- `oot_dr_monthly.csv`: strict rolling out-of-time DR results.
- `topk_dr_gain.csv`: Top-k comparison with overall/state/inventory baselines.
- `seed_stability.csv`: random-seed ranking stability.
- `aipw_and_negative_control.csv`: common-support AIPW + genuine pre-treatment negative control.
- `representative_cases_final.csv`: top/bottom five OOT treated cases, selected by tau only.

Estimator: R-learner with LightGBM base learners; dynamic X is t-1; S* excludes fill; P35 is calculated separately within each `ym`.
