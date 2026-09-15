# -*- coding: utf-8 -*-
"""从原始月报构建品规-月份面板。只读取原始文件，输出到 v18-1/data。"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[6]
SOURCE = ROOT / "0805数据"
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = [f"{y}{m:02d}" for y in (2025, 2026) for m in range(1, 13)][:19]
CODE_RE = re.compile(r"^\d{13}$")

def code13(x):
    s = str(x).strip().replace("\xa0", "")
    if s.endswith(".0"): s = s[:-2]
    return s

def num(x):
    s = str(x).strip().replace("\xa0", "")
    if s in {"", "-", "nan", "None", "N/A"}: return np.nan
    try: return float(s)
    except ValueError: return np.nan

def load_sales():
    rows = []
    cols = {5:"wholesale", 6:"retail", 7:"demand", 10:"vol", 13:"amt",
            16:"unitval", 19:"inv", 22:"fill", 25:"cost", 28:"profit"}
    for ym in MONTHS:
        p = SOURCE / "多指标销售汇总" / f"{ym}.xls"
        if not p.exists(): continue
        for _, r in pd.read_excel(p, header=None).iterrows():
            code = code13(r.iloc[3])
            if not CODE_RE.match(code): continue
            row = {"ym":ym, "code":code, "name":str(r.iloc[2]).strip(), "cat":str(r.iloc[4]).strip()}
            row.update({k:num(r.iloc[i]) for i,k in cols.items()}); rows.append(row)
    return pd.DataFrame(rows)

def load_daily():
    rows = []
    cols = {6:"put", 7:"need", 8:"vol_daily", 9:"should_cust", 10:"put_cust",
            11:"ord_cust", 12:"ord_success", 13:"ord_success_put", 14:"fill_daily",
            15:"full_cust", 16:"util", 17:"full_surf", 18:"soc_vol", 19:"soc_inv",
            20:"sell_rate", 21:"salable_days"}
    for ym in MONTHS:
        p = SOURCE / "多规格按日查询" / f"{ym}.xls"
        if not p.exists(): continue
        for _, r in pd.read_excel(p, header=None).iterrows():
            code = code13(r.iloc[2])
            if not CODE_RE.match(code):
                code = code13(r.iloc[3])
            if not CODE_RE.match(code): continue
            row = {"ym":ym, "code":code}; row.update({k:num(r.iloc[i]) for i,k in cols.items()}); rows.append(row)
    return pd.DataFrame(rows)

def load_purchase():
    rows = []
    cols = {4:"vol_purchase", 5:"req", 6:"fill_purchase", 7:"should_cust_purchase",
            8:"act_cust", 9:"put_surf", 10:"purch_surf", 11:"rep_cust2", 12:"rep_cust3",
            13:"rep_cust4", 14:"rep_cust5", 15:"rep_rate2", 16:"rep_rate3",
            17:"rep_rate4", 18:"rep_rate5", 19:"new_cust"}
    for ym in MONTHS:
        p = SOURCE / "品牌月进货情况查询" / f"{ym}.xls"
        if not p.exists(): continue
        for _, r in pd.read_excel(p, header=None).iterrows():
            code = code13(r.iloc[2])
            if not CODE_RE.match(code): continue
            row = {"ym":ym, "code":code}; row.update({k:num(r.iloc[i]) for i,k in cols.items()}); rows.append(row)
    return pd.DataFrame(rows)

def main():
    sales, daily, purchase = load_sales(), load_daily(), load_purchase()
    panel = sales.merge(daily, on=["ym","code"], how="left").merge(purchase, on=["ym","code"], how="left")
    panel = panel.drop_duplicates(["ym","code"]).copy()
    counts = panel.groupby("code")["ym"].nunique()
    panel = panel[panel["code"].map(counts).ge(6)].copy()
    panel["date"] = pd.to_datetime(panel["ym"], format="%Y%m")
    panel["month"] = panel["date"].dt.month
    panel["price_index"] = panel["retail"] / panel["wholesale"].replace(0, np.nan)
    panel["gross_margin"] = panel["profit"] / panel["amt"].replace(0, np.nan)
    panel["inventory_ratio"] = panel["inv"] / panel["vol"].replace(0, np.nan)
    panel["demand_gap"] = 100.0 - panel["fill"]
    panel["amt_per_cust"] = panel["amt"] / panel["should_cust"].replace(0, np.nan)
    panel["channel_coverage"] = panel["put_cust"] / panel["should_cust"].replace(0, np.nan) * 100
    panel["price_band_cat"] = pd.cut(panel["retail"], [-np.inf,20,40,80,120,np.inf],
                                      labels=["低档","中低档","中档","中高档","高档"], right=False)
    panel = panel.sort_values(["code","ym"]).reset_index(drop=True)
    panel.to_csv(OUT / "raw_panel.csv", index=False, encoding="utf-8-sig")
    quality = {
        "rows":int(len(panel)), "products":int(panel.code.nunique()), "months":int(panel.ym.nunique()),
        "duplicate_keys":int(panel.duplicated(["code","ym"]).sum()),
        "source_rows":{"sales":len(sales),"daily":len(daily),"purchase":len(purchase)},
        "missing_rate":{c:round(float(panel[c].isna().mean()),4) for c in
                        ["fill","util","full_surf","price_index","gross_margin","inventory_ratio",
                         "channel_coverage","ord_success","new_cust"]}
    }
    pd.Series(quality).to_json(OUT / "data_quality.json", force_ascii=False, indent=2)
    print(quality)

if __name__ == "__main__": main()
