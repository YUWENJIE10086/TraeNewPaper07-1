# -*- coding: utf-8 -*-
"""Patch-and-run wrapper for strict v2 hard experiments."""
from pathlib import Path
p=Path(__file__).with_name('run_4_hard_experiments_v2_0916_0014.py')
s=p.read_text(encoding='utf-8')
bad="overlap=pd.DataFrame([['full',len(d),int(d['T'].sum()),1.0,full_ate,cif[0],cif[1],float(np.mean(tau))],np.nan,np.nan],['common_support',len(ds),int(ds['T'].sum()),len(ds)/len(d),sup_ate,cis[0],cis[1],float(np.mean(ts)),lo,hi]],columns=['sample','n','n_treated','retained_share','dr_ate','ci_low','ci_high','mean_oof_cate','prop_low','prop_high']); overlap.to_csv(OUT/f'overlap_reestimate_{STAMP}.csv',index=False,encoding='utf-8-sig')"
good="overlap=pd.DataFrame([['full',len(d),int(d['T'].sum()),1.0,full_ate,cif[0],cif[1],float(np.mean(tau)),np.nan,np.nan],['common_support',len(ds),int(ds['T'].sum()),len(ds)/len(d),sup_ate,cis[0],cis[1],float(np.mean(ts)),lo,hi]],columns=['sample','n','n_treated','retained_share','dr_ate','ci_low','ci_high','mean_oof_cate','prop_low','prop_high']); overlap.to_csv(OUT/f'overlap_reestimate_{STAMP}.csv',index=False,encoding='utf-8-sig')"
if bad not in s:
    raise RuntimeError('Expected overlap line not found; inspect source before running')
s=s.replace(bad,good)
s=s.replace("'T':d.T,", "'T':d['T'],")
old="a=train[xcols].apply(pd.to_numeric,errors='coerce'); b=test[xcols].apply(pd.to_numeric,errors='coerce')\n    med=a.median().replace([np.inf,-np.inf],np.nan).fillna(0); return a.fillna(med).values,b.fillna(med).values"
new="a=train[xcols].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan); b=test[xcols].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan)\n    med=a.median().replace([np.inf,-np.inf],np.nan).fillna(0); return a.fillna(med).values,b.fillna(med).values"
if old not in s:
    raise RuntimeError('Expected matrices definition not found')
s=s.replace(old,new)
g={'__name__':'__main__','__file__':str(p)}
exec(compile(s,str(p),'exec'),g,g)
