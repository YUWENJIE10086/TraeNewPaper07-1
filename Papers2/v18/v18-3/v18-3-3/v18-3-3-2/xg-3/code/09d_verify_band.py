# -*- coding: utf-8 -*-
import os, numpy as np, pandas as pd
DATA = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg-3\data"
d = pd.read_csv(os.path.join(DATA, "analysis_panel.csv"), encoding="utf-8-sig")
print("\n== price_band_cat value_counts ==")
print(d["price_band_cat"].value_counts().to_dict())
print("\n== price_band_cat x sensitivity counts ==")
print(pd.crosstab(d["price_band_cat"], d["sensitivity"]))
print("\n== price_band_cat x sensitivity mean CATE ==")
print(pd.pivot_table(d, index="price_band_cat", columns="sensitivity", values="CATE", aggfunc="mean").round(3))
print("\n== cat value_counts ==")
print(d["cat"].value_counts().to_dict())
print("\n== cat x sensitivity counts ==")
print(pd.crosstab(d["cat"], d["sensitivity"]))
print("\n== cat x sensitivity mean CATE ==")
print(pd.pivot_table(d, index="cat", columns="sensitivity", values="CATE", aggfunc="mean").round(3))
# 低价位段历史月份 on 高敏感
m = d[(d["price_band_cat"]=="中低档") & (d["sensitivity"]=="高敏感")]
print("\n中低档&高敏感 n=", len(m), "months:", sorted(m["ym"].unique()), "codes:", m["code"].nunique())