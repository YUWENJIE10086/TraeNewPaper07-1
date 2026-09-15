# -*- coding: utf-8 -*-
"""v20 scientific repairs: correct permutation test and real 0.02-caliper PSM.

This script deliberately reads the registered xg-3 analysis panel and writes only to
Papers2/v20/results and Papers2/v20/tables. It never patches the manuscript.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from importlib import import_module
cfg = import_module("00_config")


def two_way_residual(values, code, ym, iterations=20):
    z = pd.Series(np.asarray(values, float)).copy()
    code = pd.Series(np.asarray(code))
    ym = pd.Series(np.asarray(ym))
    for _ in range(iterations):
        z = z - z.groupby(code).transform("mean")
        z = z - z.groupby(ym).transform("mean")
    return z.to_numpy()


def twfe_point(df, outcome="Y_clean", treatment="T"):
    y = two_way_residual(df[outcome], df["code"], df["ym"])
    t = two_way_residual(df[treatment], df["code"], df["ym"])
    den = float(np.dot(t, t))
    if den <= 0:
        raise ValueError("TWFE treatment residual has zero variance")
    return float(np.dot(t, y) / den)


def permutation_test(df, reps=1000, seed=20260915):
    """Month-stratified treatment permutation, compared with the observed TWFE coefficient."""
    rng = np.random.default_rng(seed)
    observed = twfe_point(df)
    y_res = two_way_residual(df["Y_clean"], df["code"], df["ym"])
    effects = np.empty(reps, dtype=float)

    month_index = {m: idx.to_numpy() for m, idx in df.groupby("ym").groups.items()}
    t_original = df["T"].to_numpy(int)
    code = df["code"].to_numpy()
    ym = df["ym"].to_numpy()

    for b in range(reps):
        t_perm = t_original.copy()
        for idx in month_index.values():
            t_perm[idx] = rng.permutation(t_perm[idx])
        t_res = two_way_residual(t_perm, code, ym)
        den = float(np.dot(t_res, t_res))
        effects[b] = np.nan if den <= 0 else float(np.dot(t_res, y_res) / den)

    effects = effects[np.isfinite(effects)]
    extreme = int(np.sum(np.abs(effects) >= abs(observed)))
    p_empirical = float((1 + extreme) / (len(effects) + 1))
    return {
        "definition": "month-stratified treatment-label permutation compared with observed TWFE coefficient",
        "observed_twfe": observed,
        "reps_requested": int(reps),
        "reps_valid": int(len(effects)),
        "mean": float(np.mean(effects)),
        "median": float(np.median(effects)),
        "ci_95": [float(np.quantile(effects, 0.025)), float(np.quantile(effects, 0.975))],
        "extreme_count": extreme,
        "p_empirical": p_empirical,
    }, effects


def smd(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    den = np.sqrt((np.nanvar(a, ddof=1) + np.nanvar(b, ddof=1)) / 2)
    return 0.0 if not np.isfinite(den) or den <= 0 else float((np.nanmean(a) - np.nanmean(b)) / den)


def caliper_match(df, features, caliper=0.02, seed=20260915):
    """1:1 nearest-neighbour matching without replacement, enforcing an absolute PS caliper."""
    work = df.copy()
    X = work[features].apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)
    T = work["T"].astype(int).to_numpy()

    Xs = StandardScaler().fit_transform(X)
    ps = LogisticRegression(
        max_iter=3000, class_weight="balanced", random_state=seed
    ).fit(Xs, T).predict_proba(Xs)[:, 1]
    work["ps_v20"] = ps

    treated = list(np.flatnonzero(T == 1))
    controls = set(np.flatnonzero(T == 0).tolist())
    pairs = []
    unmatched = []

    # Most constrained treated units first reduces avoidable greedy losses.
    for a in sorted(treated, key=lambda i: ps[i]):
        if not controls:
            unmatched.append(a)
            continue
        b = min(controls, key=lambda j: abs(ps[j] - ps[a]))
        distance = float(abs(ps[b] - ps[a]))
        if distance <= caliper:
            controls.remove(b)
            pairs.append((a, b, distance))
        else:
            unmatched.append(a)

    if not pairs:
        raise RuntimeError(f"No PSM pairs satisfy caliper={caliper}")

    ti = [a for a, _, _ in pairs]
    ci = [b for _, b, _ in pairs]
    balance = []
    for feature in features:
        balance.append({
            "feature": feature,
            "before": smd(work.loc[T == 1, feature], work.loc[T == 0, feature]),
            "after": smd(work.iloc[ti][feature], work.iloc[ci][feature]),
        })
    balance_df = pd.DataFrame(balance)

    yt = work.iloc[ti]["Y_clean"].to_numpy(float)
    yc = work.iloc[ci]["Y_clean"].to_numpy(float)
    distances = np.array([d for _, _, d in pairs])

    result = {
        "method": "1:1 nearest-neighbour propensity-score matching without replacement with enforced absolute caliper",
        "caliper": float(caliper),
        "treated_total": int(np.sum(T == 1)),
        "matched_pairs": int(len(pairs)),
        "unmatched_treated": int(len(unmatched)),
        "match_rate": float(len(pairs) / max(np.sum(T == 1), 1)),
        "max_pair_distance": float(np.max(distances)),
        "median_pair_distance": float(np.median(distances)),
        "matched_mean_difference": float(np.mean(yt - yc)),
        "treated_improve_rate": float(np.mean(yt > 0)),
        "control_improve_rate": float(np.mean(yc > 0)),
        "mean_abs_smd_before": float(balance_df["before"].abs().mean()),
        "mean_abs_smd_after": float(balance_df["after"].abs().mean()),
        "max_abs_smd_after": float(balance_df["after"].abs().max()),
        "n_abs_smd_after_gt_0_1": int((balance_df["after"].abs() > 0.1).sum()),
    }
    pair_df = pd.DataFrame({
        "treated_row": ti,
        "control_row": ci,
        "ps_treated": ps[ti],
        "ps_control": ps[ci],
        "distance": distances,
        "y_treated": yt,
        "y_control": yc,
    })
    return result, balance_df, pair_df


def main():
    cfg.assert_source_files()
    df = pd.read_csv(cfg.ANALYSIS_PANEL, encoding="utf-8-sig")
    source_balance = pd.read_csv(cfg.SOURCE_PSM_BALANCE, encoding="utf-8-sig")
    features = source_balance["feature"].astype(str).tolist()

    required = {"code", "ym", "T", "Y_clean", *features}
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError("analysis_panel missing required columns: " + ", ".join(missing))

    perm, effects = permutation_test(df, cfg.PERMUTATION_REPS, cfg.RANDOM_SEED)
    psm, balance, pairs = caliper_match(df, features, cfg.PSM_CALIPER, cfg.RANDOM_SEED)

    out = {
        "source_analysis_panel": str(cfg.ANALYSIS_PANEL.relative_to(cfg.REPO_ROOT)),
        "random_seed": cfg.RANDOM_SEED,
        "permutation": perm,
        "psm_caliper": psm,
    }
    (cfg.RESULTS / "robustness_v20.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame({"placebo_effect": effects}).to_csv(
        cfg.TABLES / "permutation_effects_v20.csv", index=False, encoding="utf-8-sig"
    )
    balance.to_csv(cfg.TABLES / "psm_balance_v20.csv", index=False, encoding="utf-8-sig")
    pairs.to_csv(cfg.TABLES / "psm_pairs_v20.csv", index=False, encoding="utf-8-sig")

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
