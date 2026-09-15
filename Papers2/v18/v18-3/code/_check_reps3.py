# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
d = pd.read_csv(r'D:\TraeNewPaper07-1\Papers2\v18\v18-1\data\causal_forest_panel.csv', encoding='utf-8-sig')
print('cols:', list(d.columns))
tr = d[d['T']==1].copy()
gk = dict(n=('T','size'),CATE=('CATE','mean'),Y=('Y','mean'),cat=('cat','first'))
for scol in ['S','S_pre']:
    if scol in tr.columns: gk['S']=(scol,'mean')
for scol in ['price_index_pre','price_index']:
    if scol in tr.columns: gk['price']=(scol,'mean')
rank = tr.groupby('name',as_index=False).agg(**gk)
hi = rank.sort_values(['CATE','n'],ascending=[False,False])['name'].dropna().drop_duplicates().head(5).tolist()
lo = rank.sort_values(['CATE','n'],ascending=[True,False])['name'].dropna().drop_duplicates().head(5).tolist()
for tag,names in [('HIGH',hi),('LOW',lo)]:
    print('====',tag,'====')
    for nm in names:
        r=rank[rank['name']==nm].iloc[0]
        print('  %-20s n=%d CATE=%.2f Y=%.1f S=%.1f price=%.3f cat=%s' % (
            str(nm)[:20],r['n'],r['CATE'],r['Y'],r['S'],r['price'],r['cat']))
hirow=tr.sort_values('CATE',ascending=False).iloc[0]
print('\n=== fig7 当前单月最大CATE ===')
scol = 'S_pre' if 'S_pre' in tr.columns else 'S'
print('name=%s ym=%s CATE=%.3f Y=%.2f Spre=%.1f'%(hirow['name'],hirow['ym'],hirow['CATE'],hirow['Y'],hirow.get(scol,np.nan)))