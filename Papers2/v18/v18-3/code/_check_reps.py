# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
d = pd.read_csv(r'D:\TraeNewPaper07-1\Papers2\v18\v18-1\data\causal_forest_panel.csv', encoding='utf-8-sig')
print('total', len(d), 'products', d['code'].nunique())
print()
keywords = [('利群','软红长嘴'),('天子','中支'),('娇子','宽窄好运'),('双喜','晶彩'),
            ('黄鹤楼','软1916'),('黄鹤楼','珍品细支'),('黄鹤楼','硬峡谷情'),('金圣','青瓷')]
for k1,k2 in keywords:
    m = d[d['name'].astype(str).str.contains(k1,na=False) & d['name'].astype(str).str.contains(k2,na=False)]
    tr = m[m['T']==1]
    cate_all = m['CATE'].mean() if len(m) else np.nan
    cate_tr = tr['CATE'].mean() if len(tr) else np.nan
    Y_tr = tr['Y'].mean() if len(tr) else np.nan
    S0 = tr['S_pre'].mean() if len(tr) and 'S_pre' in tr else np.nan
    pi = tr['price_index_pre'].mean() if len(tr) and 'price_index_pre' in tr else np.nan
    names = m['name'].drop_duplicates().tolist()[:5]
    print('%-4s %-8s 全样本%-3d 处理%-3d 全CATE=%7.3f 处理CATE=%7.3f 处理Y=%7.2f Spre=%6.2f price=%6.3f | %s'
          % (k1,k2,len(m),len(tr),cate_all,cate_tr,Y_tr,S0,pi,names))

print('\n==== 图8当前算法选出的10个代表 ====')
tr = d[d['T']==1].copy()
rank = tr.groupby('name',as_index=False).agg(mean_cate=('CATE','mean'),treat_cnt=('T','sum'),Y=('Y','mean'))
hi = rank.sort_values(['mean_cate','treat_cnt'],ascending=[False,False])['name'].dropna().drop_duplicates().head(5).tolist()
lo = rank.sort_values(['mean_cate','treat_cnt'],ascending=[True,False])['name'].dropna().drop_duplicates().head(5).tolist()
for g,names in [('高敏感',hi),('低敏感',lo)]:
    print(g+':')
    for n in names:
        r = rank[rank['name']==n].iloc[0]
        print('   %-22s CATE=%.2f 处理月=%d Y=%.2f' % (str(n)[:22], r['mean_cate'], r['treat_cnt'], r['Y']))