# -*- coding: utf-8 -*-
"""从 data 复算论文关键数目，核对 表3/5/9/10/11/16/17 与图 与正文是否一致"""
import os
import numpy as np
import pandas as pd

DATA = r"D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3\v18-3-3-2\xg-3\data"
d = pd.read_csv(os.path.join(DATA, "analysis_panel.csv"), encoding="utf-8-sig")
print("cols:", list(d.columns))
print("shape:", d.shape)
print("sensitivity values:", d["sensitivity"].value_counts().to_dict())
print("ym range:", d["ym"].min(), d["ym"].max(), "n_ym:", d["ym"].nunique())

# 表3：按敏感组 CATE 统计
g = d.groupby("sensitivity")["CATE"].agg(["count","mean","std","min",
    lambda x: x.quantile(.25), "median", lambda x: x.quantile(.75), "max"]).reindex(["低敏感","中敏感","高敏感"])
print("\n[表3 CATE by group]")
print(g.round(3))

# 价位段 9/11
d["band"]=d.get("price_band", pd.Series(d.index))
if "price_band" in d.columns and "sensitivity" in d.columns and "CATE" in d.columns:
    pt = d.pivot_table(index="price_band", columns="sensitivity", values="CATE",
                       aggfunc=["mean","count"])
    print("\n[价位段 pivot]")
    print(pt.round(2))
    # 每band n
    print("\n[每价位段总n]")
    print(d["price_band"].value_counts().to_dict())

# 品类 10/11
if "spec_category" in d.columns:
    pt2 = d.pivot_table(index="spec_category", columns="sensitivity", values="CATE", aggfunc=["mean","count"])
    print("\n[品类 pivot]")
    print(pt2.round(2))
    print(d["spec_category"].value_counts().to_dict())

# 表7 订货成功率中位数
for c in ["ord_success","ord_success_pre","util","fill","inventory_ratio","price_index"]:
    if c in d.columns:
        print(c, "median=", d[c].median())

# 处理组 高/低敏感 n
tr = d[d["T"]==1]
print("\n[处理组 by group]")
print(tr.groupby("sensitivity").agg(n=("CATE","size"), meanCATE=("CATE","mean")).round(3))

# 表16/17 高敏感代表品规（前5按CATE降序，处理样本）
print("\n[高敏感处理样本 top CATE]")
hi = tr[tr["sensitivity"]=="高敏感"].sort_values("CATE", ascending=False).head(8)
for _,r in hi.iterrows():
    print(r["code"], r["ym"], "CATE=", round(float(r["CATE"]),3))
print("\n[低敏感处理样本 bottom CATE]")
lo = tr[tr["sensitivity"]=="低敏感"].sort_values("CATE", ascending=True).head(8)
for _,r in lo.iterrows():
    print(r["code"], r["ym"], "CATE=", round(float(r["CATE"]),3))