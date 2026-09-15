# -*- coding: utf-8 -*-
"""
01 数据面板构建：从0805数据 3套品规级月度报表 + 终端侧增补，构造「品规×月」面板
输出：rich指标体系下的完整面板、状态评分、处理/结果/协变量
配色规范与后续02/03共用 constants.py
"""
import os, re, json, glob
import numpy as np
import pandas as pd

# ---------- 常量 ----------
BASE = r"D:\TraeNewPaper07-1\0805数据"
OUT  = r"D:\TraeNewPaper07-1\Papers2\v18\data"
os.makedirs(OUT, exist_ok=True)
MONTHS = [f"{y}{m:02d}" for y in (2025,2026) for m in range(1,13)][:19]  # 202501..202607
CODE_RE = re.compile(r"^\d{13}$")

def clean_num(x):
    """把 '-  ' 等转为 nan"""
    if x is None: return np.nan
    s = str(x).strip().replace("\xa0","")
    if s in ("","-","nan","None","N/A"): return np.nan
    try: return float(s)
    except: return np.nan

# ============================================================
# 数据源1：多指标销售汇总 —— 量价存利 + 基础档案
# ============================================================
def load_sales_sum():
    rows=[]
    for m in MONTHS:
        fp = os.path.join(BASE,"多指标销售汇总",f"{m}.xls")
        if not os.path.exists(fp): continue
        df = pd.read_excel(fp, header=None)
        # col map (0-based): 2名称 3条码 4类别 5批发 6零售; 每指标 [本期,同期,同比]
        idx = {5:"wholesale",6:"retail",7:"demand",10:"vol",13:"amt",16:"unitval",19:"inv",22:"fill",25:"cost",28:"profit"}
        for _,r in df.iterrows():
            code = str(r[3]).strip().replace("\xa0","")
            if not CODE_RE.match(code): continue
            d={"ym":m,"code":code}
            d["name"]=str(r[2]).strip()
            d["cat"]=str(r[4]).strip()
            for i,k in idx.items():
                d[k]=clean_num(r[i])
            rows.append(d)
    return pd.DataFrame(rows)

# ============================================================
# 数据源2：多规格按日查询 —— 需渠道/动销(货源利用率/订足面/社会库存/可销天数)
# ============================================================
def load_daily():
    rows=[]
    for m in MONTHS:
        fp = os.path.join(BASE,"多规格按日查询",f"{m}.xls")
        if not os.path.exists(fp): continue
        df = pd.read_excel(fp, header=None)
        # cols: 0空 1名称 2编码 3条码 4类别 5批发 6投放 7需求 8销量 9应订 10投放客户 11订货客户
        #       12订执(应订) 13订执(投放) 14订单满足 15订足客户 16货源利用率 17订足面 18社会销量 19社会库存 20动销率 21可销天数
        cols={5:"put",7:"need",8:"vol",9:"should_cust",10:"put_cust",
              11:"ord_cust",12:"ord_success",13:"ord_success_put",14:"fill",15:"full_cust",
              16:"util",17:"full_surf",18:"soc_vol",19:"soc_inv",20:"sell_rate",21:"salable_days"}
        for _,r in df.iterrows():
            code=str(r[3]).strip() if False else None
            # 用编码col2
            code=str(r[2]).strip().replace("\xa0","")
            if not CODE_RE.match(code):
                # 兜底用条码col3
                code=str(r[3]).strip().replace("\xa0","")
                if not CODE_RE.match(code): continue
            d={"ym":m,"code":code}
            for i,k in cols.items():
                d[k]=clean_num(r[i])
            rows.append(d)
    return pd.DataFrame(rows)

# ============================================================
# 数据源3：品牌月进货查询情况 —— 渠道质量(进货面/投放面/重复进货率/新进货)
# ============================================================
def load_purchase():
    rows=[]
    for m in MONTHS:
        fp = os.path.join(BASE,"品牌月进货情况查询",f"{m}.xls")
        if not os.path.exists(fp): continue
        df = pd.read_excel(fp, header=None)
        # cols: 2商品编码 3规格 4销量 5要货 6订单满足 7应进客户 8实际进货 9投放面 10进货面
        #       重复进货户数>=2..>=5 =11..14; 重复进货率 =15..18; 新进货户数=19
        cols={4:"vol",5:"req",6:"fill",7:"should_cust",8:"act_cust",
              9:"put_surf",10:"purch_surf",11:"rep_cust2",12:"rep_cust3",13:"rep_cust4",
              14:"rep_cust5",15:"rep_rate2",16:"rep_rate3",17:"rep_rate4",18:"rep_rate5",19:"new_cust"}
        for _,r in df.iterrows():
            code=str(r[2]).strip().replace("\xa0","")
            if not CODE_RE.match(code): continue
            d={"ym":m,"code":code}
            for i,k in cols.items():
                d[k]=clean_num(r[i])
            rows.append(d)
    return pd.DataFrame(rows)

# ============================================================
# 合并构建面板
# ============================================================
def build():
    print(">> 加载 多指标销售汇总 ..."); S = load_sales_sum()
    print(">> 加载 多规格按日查询 ..."); D = load_daily()
    print(">> 加载 品牌月进货查询情况 ..."); P = load_purchase()
    print(f"   销售汇总 {S.shape[0]} | 按日 {D.shape[0]} | 进货 {P.shape[0]}")

    # 主面板以多指标销售汇总为骨架
    panel = S.merge(D, on=["ym","code"], how="left", suffixes=("","_d"))
    panel = panel.merge(P, on=["ym","code"], how="left", suffixes=("","_p"))

    # 剔除类别缺失或打包的无效行
    panel = panel[panel["cat"].notna()]
    code_counts = panel.groupby("code")["ym"].nunique()
    panel = panel[panel["code"].map(code_counts)>=6]   # 保留至少6个月有效序列的品规

    cols = list(panel.columns)
    # 构造星期排序轴
    panel["ym_dt"] = pd.to_datetime(panel["ym"], format="%Y%m")
    panel["month"] = panel["ym_dt"].dt.month
    panel["year"]  = panel["ym_dt"].dt.year

    # ---------- 派生指标 ----------
    # 顺价指数 = 零售价/批发价；毛利率=毛利/销售额；存销比=库存/销量；需求缺口=1-填充率
    panel["price_index"]   = panel["retail"] / panel["wholesale"].replace(0,np.nan)
    panel["gross_margin"]  = panel["profit"] / panel["amt"].replace(0,np.nan)
    panel["inventory_ratio"] = panel["inv"] / panel["vol"].replace(0,np.nan)
    panel["demand_gap"]    = 1 - panel["fill"]
    panel["unit_growth"]   = panel.groupby("code")["vol"].pct_change(fill_method=None)
    panel["amt_per_cust"]  = panel["amt"] / panel["should_cust"].replace(0,np.nan)  # 户均订货金额

    # 渠道覆盖（社会口径缺失高，暂不纳入派生；保留原始字段 salable_days 等）
    panel["channel_coverage"] = panel["put_cust"] / panel["should_cust"].replace(0,np.nan)  # 投放客户覆盖率

    # 价位段由零售价划分
    def price_band(rp):
        if rp>=120: return 5
        if rp>=80:  return 4
        if rp>=40:  return 3
        if rp>=20:  return 2
        return 1
    panel["price_band"] = panel["retail"].apply(lambda x: price_band(x) if not np.isnan(x) else np.nan)
    panel["price_band_cat"] = panel["price_band"].map({1:"低档",2:"中低档",3:"中档",4:"中高档",5:"高档"})

    # 保存中间面板
    panel.to_csv(os.path.join(OUT,"raw_panel_v1.csv"), index=False, encoding="utf-8-sig")
    print(f">> 面板已保存: {panel.shape[0]} 行 × {panel.shape[1]} 列")
    print("   品规数:", panel["code"].nunique(), "月份数:", panel["ym"].nunique())
    return panel

if __name__=="__main__":
    p = build()
    # 诊断
    print("\n=== 关键数值缺失率(%) ===")
    for c in ["vol","amt","fill","util","inventory_ratio","price_index","soc_inv_ratio","purch_surf","rep_rate2"]:
        if c in p.columns:
            print(f"  {c:>16}: {(p[c].isna().mean()*100):.1f}")
