# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments'/'0916_0014'
a=pd.read_csv(EXP/'analysis_panel_0916_0014.csv',encoding='utf-8-sig',low_memory=False)
o=pd.read_csv(EXP/'oof_predictions_0916_0014.csv',encoding='utf-8-sig')
d=a.merge(o[['code','ym','tau_oof','dr_oof']],on=['code','ym'],how='inner')
t=d[d['T']==1].copy()
# Select both ends by OOF CATE, without conditioning on realized Y.
sel=pd.concat([t.nlargest(5,'tau_oof'),t.nsmallest(5,'tau_oof')]).drop_duplicates(['code','ym'])
cols=['code','name','ym','T','Y','tau_oof','dr_oof','L1_S','L1_price_index','L1_gross_margin','L1_inventory_ratio','L1_unit_growth']
cols=[c for c in cols if c in sel.columns]
sel[cols].sort_values('tau_oof',ascending=False).to_csv(EXP/'representative_cases_strict_0916_0023.csv',index=False,encoding='utf-8-sig')
# Also summarize high/low ends for manuscript text.
q20=t['tau_oof'].quantile(.8); q80=t['tau_oof'].quantile(.2)
summary=pd.DataFrame([
 {'group':'treated_top20_tau','n':int((t.tau_oof>=q20).sum()),'mean_tau':t.loc[t.tau_oof>=q20,'tau_oof'].mean(),'mean_Y':t.loc[t.tau_oof>=q20,'Y'].mean(),'mean_L1_S':t.loc[t.tau_oof>=q20,'L1_S'].mean()},
 {'group':'treated_bottom20_tau','n':int((t.tau_oof<=q80).sum()),'mean_tau':t.loc[t.tau_oof<=q80,'tau_oof'].mean(),'mean_Y':t.loc[t.tau_oof<=q80,'Y'].mean(),'mean_L1_S':t.loc[t.tau_oof<=q80,'L1_S'].mean()}
])
summary.to_csv(EXP/'representative_groups_strict_0916_0023.csv',index=False,encoding='utf-8-sig')
print(sel[cols].to_string(index=False))
print(summary.to_string(index=False))
