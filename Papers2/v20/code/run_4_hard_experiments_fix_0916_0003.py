# -*- coding: utf-8 -*-
"""Compatibility wrapper for run_4_hard_experiments_0916_0003.py.
Pandas .T is transpose, so treatment-column attribute access is rewritten to ['T'] before execution.
"""
from pathlib import Path

p=Path(__file__).with_name('run_4_hard_experiments_0916_0003.py')
s=p.read_text(encoding='utf-8')
repls={
    'train.T.values': "train['T'].values",
    'train.T)': "train['T'])",
    'train.T;': "train['T'];",
    'test.T.values': "test['T'].values",
    'tr.T.sum()': "tr['T'].sum()",
    'te.T.sum()': "te['T'].sum()",
    'te.T==1': "te['T']==1",
    'te.T.values==1': "te['T'].values==1",
    'gkf.split(d,d.T,groups=d.code)': "gkf.split(d,d['T'],groups=d.code)",
    'd.T.values': "d['T'].values",
    'd.T.sum()': "d['T'].sum()",
    'ds.T.sum()': "ds['T'].sum()",
    "'T':d.T": "'T':d['T']",
    'd.iloc[tr_idx].T)': "d.iloc[tr_idx]['T'])",
    'train.T.values==0': "train['T'].values==0",
    'train.T.values==1': "train['T'].values==1",
}
for a,b in repls.items(): s=s.replace(a,b)
s=s.replace('np.trapz(cg,frac)','np.trapezoid(cg,frac)')
g={'__name__':'__main__','__file__':str(p)}
exec(compile(s,str(p),'exec'),g,g)
