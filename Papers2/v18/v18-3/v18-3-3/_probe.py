# -*- coding: utf-8 -*-
import os, re, glob
p = r'D:\TraeNewPaper07-1\Papers2\v18\v18-3\v18-3-3'
print('=== v18-3-3 下的 html ===')
for f in glob.glob(p + r'\**\*.html', recursive=True):
    print('FILE:', f)
    try:
        src = open(f, encoding='utf-8').read()
    except Exception as e:
        print('  read err', e); continue
    m = re.search(r'<title>(.*?)</title>', src)
    print('  title:', m.group(1) if m else None)
    imgs = re.findall(r'<img[^>]+src=\"([^\"]+)\"', src)
    print('  imgs:', imgs[:12])