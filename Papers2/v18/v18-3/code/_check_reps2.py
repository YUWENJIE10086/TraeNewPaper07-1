# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
d = pd.read_csv(r'D:\TraeNewPaper07-1\Papers2\v18\v18-1\data\causal_forest_panel.csv', encoding='utf-8-sig')
tr = d[d['T']==1].copy()
rank = tr.groupby('name',as_index=False).agg(
    n=('T','size'),CATE=('CATE','mean'),Y=('Y','mean'),
    S=('S_pre','mean'),price=('price_index_pre','mean'),cat=('cat','first'),N=('code','size'))
hi = rank.sort_values(['CATE','n'],ascending=[False,False])['name'].dropna().drop_duplicates().head(5).tolist()
lo = rank.sort_values(['CATE','n'],ascending=[True,False])['name'].dropna().drop_duplicates().head(5).tolist()
for tag,names in [('HIGH',hi),('LOW',lo)]:
    print('====',tag,'====')
    for nm in names:
        r=rank[rank['name']==nm].iloc[0]
        vm=[('CATE',r['CATE'],'.2f'),('Y',r['Y'],'.1f'),('S_pre',r['S'],'.1f'),('price',r['price'],'.3f')]
        print('%-20s n=%d cat=%s' % (str(nm)[:20],r['n'],r['cat']))
        print('     '+'  '.join('%s=%'+fmt for k,v,fmt in v for _ in []) % tuple([r[k] for k,_,_ in vm]) if False else '     '+'  '.join('%s=%.2f'%(k,r[k]) for k,_,_ in vm))
        print('     price=%.3f  S=%.1f  Y=%.1f' % (r['price'],r['S'],r['Y']))
# 检查最高单月CATE的处理品规(图7用)
hirow=tr.sort_values('CATE',ascending=False).iloc[0]
print('\n=== fig7 当前选中的单月最大CATE ===')
print('name=%s ym=%s CATE=%.3f Y=%.2f Spre=%.1f'%(hirow['name'],hirow['ym'],hirow['CATE'],hirow['Y'],hirow.get('S_pre',np.nan)))