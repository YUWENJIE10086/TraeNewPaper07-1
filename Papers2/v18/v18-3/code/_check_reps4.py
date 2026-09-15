# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
d = pd.read_csv(r'D:\TraeNewPaper07-1\Papers2\v18\v18-1\data\causal_forest_panel.csv', encoding='utf-8-sig')
# 天子(中支)轨迹
sub = d[d['name'].astype(str)=='天子(中支)'].sort_values('ym')
print('=== 天子(中支) 轨迹 (ym, S, T, Y, CATE) ===')
for _,r in sub.iterrows():
    print('  %s  S=%6.2f  T=%d  Y=%6.2f  CATE=%6.3f' % (r['ym'],r['S'],r['T'],r.get('Y',np.nan),r['CATE']))
print('S_pre 全体均值=%.1f  min=%.1f max=%.1f' % (sub['S_pre'].mean(), sub['S_pre'].min(), sub['S_pre'].max()))
print('name variants:', list(d[d['name'].astype(str).str.contains('天子')]['name'].drop_duplicates()))
print()
# 表5: 高/低敏感新代表 的S_pre与price index 区间
print('=== 图8代表的高/低敏感图像指标 ===')
hi = ['好猫(细支长乐吉祥)','天子(中支)','娇子(宽窄好运)','双喜(百年经典)','好猫(长乐九美)']
lo = ['红金龙(软蓝九州腾龙)','钻石(荷花)','黄鹤楼(硬1916红爆)','黄鹤楼(硬珍品)','黄鹤楼(硬1916如意)']
for tag,names in [('高敏感',hi),('低敏感',lo)]:
    print('--',tag,'--')
    for n in names:
        sub=d[d['name'].astype(str)==n]
        tr=sub[sub['T']==1]
        print('  %-18s n=%d CATEtr=%.2f Ytr=%.1f Spre=%.1f price=%.3f' % (
            n,len(tr),(tr['CATE'].mean() if len(tr) else np.nan),(tr['Y'].mean() if len(tr) else np.nan),
            tr['S_pre'].mean() if len(tr) else np.nan, tr['price_index_pre'].mean() if len(tr) else np.nan))
    vals=[ (d[d['name'].astype(str)==n].T==1).sum() for n in names]
    print('  处理期数:', dict(zip(names,vals)))