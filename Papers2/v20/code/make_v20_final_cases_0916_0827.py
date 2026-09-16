# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'Papers2'/'v18'/'data'/'raw_panel_v1.csv'
PRED=ROOT/'Papers2'/'v20'/'experiments'/'0916_0827'/'oot_dr_predictions.csv'
OUT=ROOT/'Papers2'/'v20'/'experiments'/'0916_0827'
r=pd.read_csv(RAW,encoding='utf-8-sig').sort_values(['code','ym'])
r['fill_prev']=r.groupby('code')['fill'].shift(1);r['fill_drop_pp']=r.fill_prev-r.fill
p=pd.read_csv(PRED,encoding='utf-8-sig')
x=p[p['T']==1].merge(r[['code','ym','name','cat','fill','fill_prev','fill_drop_pp','price_index','gross_margin','inventory_ratio','sell_rate']],on=['code','ym'],how='left')
a=x.nlargest(5,'tau_oot').copy();a['case_group']='高排序5例';b=x.nsmallest(5,'tau_oot').copy();b['case_group']='低排序5例'
c=pd.concat([a,b],ignore_index=True)
cols=['case_group','ym','code','name','cat','tau_oot','Y','lag_Sstar','lag_inventory_ratio','fill_prev','fill','fill_drop_pp','price_index','gross_margin','inventory_ratio','sell_rate']
c[cols].to_csv(OUT/'representative_cases_final.csv',index=False,encoding='utf-8-sig')
print(c[cols].to_string(index=False))
