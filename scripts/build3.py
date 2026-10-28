#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 授渔未来 对外知识库 v3"""
import json, os, shutil, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'output', '授渔未来')

d = json.load(open('work/data3.json', encoding='utf-8'))


def fix_src(c):
    def rep(m):
        u = m.group(1)
        if u.startswith('http') or u.startswith('assets/'):
            return m.group(0)
        return f'src="assets/img/{u}"'
    return re.sub(r'src="([^"]+)"', rep, c)


for s in d['sections']:
    for it in s['items']:
        it['html'] = fix_src(it['html'])

tpl = open('work/template3.html', encoding='utf-8').read()
js = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = tpl.replace('__DATA_JSON__', js)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)

dst = os.path.join(OUT, 'assets', 'img')
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree('work/assets/img', dst)

shutil.copy('work/data3.json', os.path.join(OUT, 'data.json'))
sc = os.path.join(OUT, 'scripts')
os.makedirs(sc, exist_ok=True)
for f_ in ['scrape.py', 'mirror.py', 'parse_manual.py', 'merge.py', 'rebuild.py', 'build3.py']:
    p_ = os.path.join('work', f_)
    if os.path.exists(p_):
        shutil.copy(p_, os.path.join(sc, f_))
shutil.copy('work/template3.html', os.path.join(sc, 'template.html'))

print('生成完成 ->', OUT)
print('index.html', os.path.getsize(os.path.join(OUT, 'index.html')) // 1024, 'KB')
print('统计:', d['stats'])
