#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 授渔未来 对外知识库 v3"""
import json, os, shutil, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'output', '授渔未来')

d = json.load(open('work/data3.json', encoding='utf-8'))

# 更新日志（缺失时给空壳，保证站点不报错）
log = {'latest': None, 'versions': []}
if os.path.exists('work/changelog.json'):
    try:
        log = json.load(open('work/changelog.json', encoding='utf-8'))
    except Exception:
        pass
d['changelog'] = log


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
# 安全校验：JSON 必须可解析且条目数合理，否则中止，不覆盖线上可用文件
try:
    _chk = json.loads(js.replace('<\\/', '</'))
    _n = sum(len(s['items']) for s in _chk['sections'])
    assert _n >= 50, f'条目数异常: {_n}'
except Exception as e:
    print(f'✗ 构建中止：数据校验失败 {e}')
    sys.exit(1)
with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)

dst = os.path.join(OUT, 'assets', 'img')
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree('work/assets/img', dst)

shutil.copy('work/data3.json', os.path.join(OUT, 'data.json'))
if os.path.exists('work/changelog.json'):
    shutil.copy('work/changelog.json', os.path.join(OUT, 'changelog.json'))

# 内容指纹快照：id -> {hash, updated_at, title}，供下次刷新做差异比对
snap = {'items': {it['id']: {'hash': it.get('hash', ''),
                             'updated_at': it.get('updated_at', 0),
                             'title': it['title']}
                  for s in d['sections'] for it in s['items']},
        'generated_at': d.get('generated_at', 0)}
with open(os.path.join(OUT, 'data_prev.json'), 'w', encoding='utf-8') as f:
    json.dump(snap, f, ensure_ascii=False, indent=1)

sc = os.path.join(OUT, 'scripts')
os.makedirs(sc, exist_ok=True)
for f_ in ['scrape.py', 'mirror.py', 'parse_manual.py', 'rebuild.py', 'build3.py', 'refresh.py']:
    p_ = os.path.join('work', f_)
    if os.path.exists(p_):
        shutil.copy(p_, os.path.join(sc, f_))
shutil.copy('work/template3.html', os.path.join(sc, 'template.html'))

print('生成完成 ->', OUT)
print('index.html', os.path.getsize(os.path.join(OUT, 'index.html')) // 1024, 'KB')
print('统计:', d['stats'])
print('更新日志版本数:', len(log.get('versions', [])))
