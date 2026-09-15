# -*- coding: utf-8 -*-
"""
02 综合状态评分 + R-learner 因果森林估计
构建状态评分S(熵-博弈组合赋权)->结果Y=S_{t+1}-S_t, 处理T(供给收缩)->LightGBM交叉拟合R-learner估计CATE
输出: CATE面板/分组画像/SHAP/决策规则/回溯验证
修复: 稳健缩尾+剔除无效指标(全0/全na)+伪结果分位数约束, 稳定CATE量级
"""
import os, json
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.tree import DecisionTreeRegressor, export_text
import lightgbm as lgb
import shap

DATA = r"D:\TraeNewPaper07-1\Papers2\v18\data"
OUT  = DATA

LGB_PARAMS = dict(objective="regression", n_estimators=300, learning_rate=0.06,
                  num_leaves=24, min_child_samples=30, subsample=0.8, colsample_bytree=0.8,
                  random_state=42, verbose=-1)

# ---------------- 状态指标（方向 +正向好 / -负向，越低越好）----------------
# 采用业务语义明确、覆盖充足的稳健指标; ord_success语义异常剔除, 其余保留以"指标体系丰富"
STATE_IND = [
    ("util",             "+", "货源利用率"),
    ("fill",             "+", "订单满足率"),
    ("full_surf",        "+", "订足面"),
    ("price_index",      "+", "顺价指数"),
    ("gross_margin",     "+", "毛利率"),
    ("unitval",          "+", "单箱销售额"),
    ("inventory_ratio",  "-", "存销比"),
    ("channel_coverage", "+", "投放客户覆盖率"),
]

def robust_rank(v):
    """分位数缩尾 -> min-max, 保留原始量纲但抑制重尾离群"""
    v = v.astype(float)
    lo, hi = v.quantile(0.02), v.quantile(0.98)
    v = v.clip(lo, hi)
    rng = (hi - lo)
    if rng <= 1e-9:
        return pd.Series(0.5, index=v.index)
    return (v - lo) / rng

def entropy_weights(X):
    X = np.asarray(X, float); X = np.maximum(X, 1e-6)
    p = X / X.sum(axis=0, keepdims=True)
    e = -np.nansum(p * np.log(p), axis=0) / np.log(len(X))
    w = (1 - e) / np.sum(1 - e)
    return w

def critic_weights(X):
    X = np.asarray(X, float)
    if X.ndim == 1: X = X[:, None]
    X = X + 1e-6 * np.random.RandomState(0).randn(*X.shape)
    s = np.nanstd(X, axis=0)
    R = np.nan_to_num(np.corrcoef(X, rowvar=False))
    conflict = (1 - np.abs(R)).sum(axis=1)
    C = s * conflict
    return C / np.sum(C)

def game_theory_fuse(w1, w2):
    A = np.array([[np.dot(w1, w1), np.dot(w1, w2)],
                  [np.dot(w2, w1), np.dot(w2, w2)]])
    coeff = np.linalg.solve(A, np.array([1.0, 1.0]))
    w = np.maximum(coeff[0]*w1 + coeff[1]*w2, 0); w = w / w.sum()
    return w, coeff

def build_score(df):
    """有效性筛选: 缺失率<50%。分位数秩归一化->熵/CRITIC/博弈赋权->S(0-100)"""
    inds = []
    for c, dr, _ in STATE_IND:
        if c not in df.columns: continue
        v = df[c]
        if v.isna().mean() > 0.50: continue
        if v.dropna().nunique() <= 1: continue
        inds.append((c, dr))
    m = df[["code", "ym"]].copy()
    Z = pd.DataFrame(index=m.index)
    for c, dr in inds:
        z = robust_rank(df[c])
        Z[c] = z if dr == "+" else (1 - z)
    X = Z.apply(lambda s: s.fillna(s.mean())).values
    w_e, w_c = entropy_weights(X), critic_weights(X)
    w_f, coeff = game_theory_fuse(w_e, w_c)
    m["S"] = (X @ w_f) * 100
    return m, w_e, w_c, w_f, coeff, [c for c, _ in inds]

# ---------------- 主流程 ----------------
def main():
    panel = pd.read_csv(os.path.join(DATA, "raw_panel_v1.csv"), encoding="utf-8-sig")
    panel = panel.sort_values(["code", "ym"]).reset_index(drop=True)

    score_df, w_e, w_c, w_f, coeff, eff_inds = build_score(panel)
    panel = panel.merge(score_df, on=["code", "ym"], how="left")

    panel["S_next"] = panel.groupby("code")["S"].shift(-1)
    panel["Y"] = panel["S_next"] - panel["S"]

    # 处理变量 T: 供给收缩(当月满足率<=同月35分位 且 满足率较上月降>2pp)
    q35 = panel.groupby("month")["fill"].transform(lambda x: x.quantile(0.35))
    fill_prev = panel.groupby("code")["fill"].shift(1)
    panel["T"] = ((panel["fill"] <= q35) & (fill_prev - panel["fill"] > 2.0)).astype(int)

    # 协变量：量/价/存/需/利/渠道/结构 富集
    cov_candidates = [
        "util", "fill", "full_surf", "ord_success", "price_index", "gross_margin",
        "unitval", "inventory_ratio", "channel_coverage", "demand_gap",
        "amt_per_cust", "new_cust", "S",
    ]
    tmp = pd.concat([pd.get_dummies(panel["cat"], prefix="cat").astype(int),
                     pd.get_dummies(panel["price_band_cat"], prefix="band").astype(int)], axis=1)
    panel = pd.concat([panel, tmp], axis=1)
    for d in ["一类烟", "二类烟", "三类烟", "四类烟", "五类烟"]:
        if f"cat_{d}" not in panel.columns: panel[f"cat_{d}"] = 0
    for d in ["低档", "中低档", "中档", "中高档", "高档"]:
        if f"band_{d}" not in panel.columns: panel[f"band_{d}"] = 0
    cov_candidates += [c for c in panel.columns if c.startswith("cat_") or c.startswith("band_")]

    covs_all = list(dict.fromkeys(cov_candidates))
    sel_cols = list(dict.fromkeys(covs_all + ["code", "ym", "T", "Y", "S"]))
    data = panel[sel_cols].copy()
    data = data.dropna(subset=["T", "Y"]).copy()
    cover = data[covs_all].notna().mean().fillna(0.0)
    keep = [c for c in covs_all if float(cover[c]) >= 0.35]
    final_cols = list(dict.fromkeys(["code", "ym", "T", "Y", "S"] + keep))
    data = data[final_cols].copy()
    for c in keep:
        data[c] = data[c].fillna(data[c].median())
    # Y 去极端(状态评分0-100, 月度变化截断在合理范围)
    y_lo, y_hi = np.percentile(data["Y"], [1, 99])
    data = data[data["Y"].between(y_lo, y_hi)].copy()
    if "inventory_ratio" in data.columns:
        data = data[data["inventory_ratio"] < np.percentile(data["inventory_ratio"], 99)]

    covs = list(dict.fromkeys(keep))
    dup_in_data = [c for c in set(covs) if list(data.columns).count(c) > 1]
    if dup_in_data:
        print("WARN 重复列:", dup_in_data)
    sub = data[covs]
    Xdata = sub.values.astype(float)
    T = data["T"].values.astype(float); Y = data["Y"].values.astype(float)
    n = len(Xdata); n_treat = int(T.sum())
    assert Xdata.shape[1] == len(covs), (Xdata.shape[1], len(covs))
    print(f"[完整样本] {data.shape[0]} 行 | 处理组 {n_treat} | 协变量 {len(covs)}")

    # ---------------- R-learner (5折交叉拟合 + 正交残差) ----------------
    nfold = 5
    kf = KFold(n_splits=nfold, shuffle=True, random_state=42)
    mu_oof = np.full(n, np.nan); e_oof = np.full(n, np.nan)
    for tr, va in kf.split(Xdata):
        m1 = lgb.LGBMRegressor(**LGB_PARAMS); m1.fit(Xdata[tr], Y[tr]); mu_oof[va] = m1.predict(Xdata[va])
        m2 = lgb.LGBMClassifier(objective="binary", n_estimators=300, learning_rate=0.06,
                                num_leaves=24, min_child_samples=30, subsample=0.8,
                                colsample_bytree=0.8, random_state=42, verbose=-1)
        m2.fit(Xdata[tr], T[tr].astype(int)); e_oof[va] = m2.predict_proba(Xdata[va])[:, 1]
    e_oof = np.clip(e_oof, 1e-3, 1 - 1e-3)
    Y_tilde = Y - mu_oof; T_tilde = T - e_oof
    rho = Y_tilde / T_tilde
    # 伪结果稳健约束: 抑制低处理率样本带来的极端伪结果
    rlo, rhi = np.percentile(rho, [3, 97])
    rho = np.clip(rho, rlo, rhi)
    wgt = T_tilde ** 2

    cate_model = lgb.LGBMRegressor(**LGB_PARAMS)
    cate_model.fit(Xdata, rho, sample_weight=wgt)
    tau = cate_model.predict(Xdata)
    # CATE 输出 clip 到业务合理窗(对应状态评分月度变化幅度±25), 抑制超量纲外推
    tau = np.clip(tau, -25, 25)
    data["CATE"] = tau
    ate = float(np.mean(tau)); ate_se = float(np.std(tau) / np.sqrt(len(tau)))

    # ---------------- 分群: 高/中/低敏感 ----------------
    q_hi, q_lo = np.quantile(tau, [0.667, 0.333])
    lab = pd.cut(tau, bins=[-np.inf, q_lo, q_hi, np.inf], labels=["低敏感", "中敏感", "高敏感"])
    data["sensitivity"] = lab.astype(str)

    # ---------------- SHAP ----------------
    explainer = shap.TreeExplainer(cate_model)
    sh = explainer.shap_values(Xdata)
    if isinstance(sh, list):
        sh = sh[0]
    sh = np.asarray(sh).reshape(n, len(covs))
    shap_imp = np.abs(sh).mean(axis=0)
    order = np.argsort(-shap_imp)
    shap_df = pd.DataFrame({"feature": [covs[i] for i in order], "importance": [shap_imp[i] for i in order]})

    # ---------------- 决策规则 ----------------
    tree = DecisionTreeRegressor(max_depth=3, min_samples_leaf=30, random_state=42)
    tree.fit(Xdata, tau)
    rules = export_text(tree, feature_names=covs)

    # ---------------- 回溯验证: 处理组内 高敏感(预测CATE上1/3) vs 其余 ----------------
    trt = data[T == 1].copy()
    q_hi_trt = np.quantile(trt["CATE"], 0.667)
    trt["is_high"] = trt["CATE"] >= q_hi_trt
    grp_h = trt[trt["is_high"]]; grp_l = trt[~trt["is_high"]]
    v_rule, v_ctl = float(grp_h["Y"].mean()), float(grp_l["Y"].mean())
    pr_rule = float((grp_h["Y"] > 0).mean()); pr_ctl = float((grp_l["Y"] > 0).mean())
    n1, n2 = len(grp_h), len(grp_l)
    base_all = float(data[data["T"] == 0]["Y"].mean())

    # ---------------- 保存 ----------------
    data.to_csv(os.path.join(OUT, "causal_forest_panel_v1.csv"), index=False, encoding="utf-8-sig")
    gcols = [c for c in ["CATE", "Y", "util", "inventory_ratio", "price_index", "S"] if c in data.columns]
    data.groupby("sensitivity")[gcols].mean().to_csv(os.path.join(OUT, "causal_forest_group_summary_v1.csv"), encoding="utf-8-sig")
    shap_df.to_csv(os.path.join(OUT, "causal_forest_shap_importance_v1.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame({"feature": covs, "shap_imp": [abs(sh[:, i]).mean() for i in range(len(covs))]}).sort_values("shap_imp", ascending=False)\
        .to_csv(os.path.join(OUT, "causal_forest_shap_named_v1.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame({"feature": eff_inds, "w_entropy": w_e, "w_critic": w_c, "w_fusion": w_f})\
        .to_csv(os.path.join(OUT, "entropy_weights_v1.csv"), index=False, encoding="utf-8-sig")

    metrics = {
        "n_samples": int(n), "n_treat": int(n_treat), "n_covs": len(covs),
        "ate": round(ate, 3), "ate_se": round(ate_se, 3), "ate_t": round(ate / ate_se, 2),
        "cate_mean": round(float(np.mean(tau)), 3), "cate_std": round(float(np.std(tau)), 3),
        "q_hi": round(q_hi, 3), "q_lo": round(q_lo, 3),
        "n_high": int((data["sensitivity"] == "高敏感").sum()),
        "n_mid": int((data["sensitivity"] == "中敏感").sum()),
        "n_low": int((data["sensitivity"] == "低敏感").sum()),
        "shap_top": [str(x) for x in shap_df["feature"].head(8).tolist()],
        "fusion_coeff": [round(float(coeff[0]), 3), round(float(coeff[1]), 3)],
        "backtest_rule_meanY": round(v_rule, 3), "backtest_ctl_meanY": round(v_ctl, 3),
        "backtest_base_untreated": round(base_all, 3),
        "backtest_rule_n": int(n1), "backtest_ctl_n": int(n2),
        "backtest_rule_impr": round(pr_rule, 3), "backtest_ctl_impr": round(pr_ctl, 3),
        "covs": covs,
    }
    with open(os.path.join(OUT, "causal_forest_metrics_v1.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "causal_forest_rules_v1.txt"), "w", encoding="utf-8") as f:
        f.write(rules)

    print("\n=== 结果摘要 ===")
    print(json.dumps(metrics, ensure_ascii=False, indent=1))
    print("\n=== 决策规则 ===\n", rules)

if __name__ == "__main__":
    main()

