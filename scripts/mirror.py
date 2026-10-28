#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把正文中的远程图片镜像到本地 assets/img，并改写 src"""
import json, re, os, urllib.request, hashlib, concurrent.futures as cf

d = json.load(open('data.json', encoding='utf-8'))
OUT = 'assets/img'
os.makedirs(OUT, exist_ok=True)

urls = set()
for m in d['modules']:
    for a in m['articles']:
        urls |= set(re.findall(r'src="(https?://[^"]+)"', a['content']))


def fname(u):
    base = u.split('/')[-1].split('?')[0]
    if not base.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
        base = os.path.basename(u.split('?')[0]) or 'img'
        base = base + '.png'
    h = hashlib.md5(u.encode()).hexdigest()[:6]
    stem = re.sub(r'\.[^.]+$', '', base)
    return f'{stem}-{h}{os.path.splitext(base)[1]}'


mapping = {u: fname(u) for u in urls}


def dl(u):
    fn = mapping[u]
    path = os.path.join(OUT, fn)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return (u, fn, os.path.getsize(path), 'cached')
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.xygj.pro/'})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        with open(path, 'wb') as f:
            f.write(data)
        return (u, fn, len(data), 'ok')
    except Exception as e:
        return (u, fn, 0, f'FAIL {e}')


ok = fail = 0
failed = set()
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for u, fn, sz, st in ex.map(dl, sorted(urls)):
        if st in ('ok', 'cached'):
            ok += 1
        else:
            fail += 1
            failed.add(u)
            print('FAIL', u, st)

print(f'下载完成: ok={ok} fail={fail} / total={len(urls)}')

# 改写 src（下载失败的保持远程引用）
for m in d['modules']:
    for a in m['articles']:
        def rep(mo):
            u = mo.group(1)
            if u in failed:
                return mo.group(0)
            return f'src="{mapping.get(u, u)}"' if u in mapping else mo.group(0)
        a['content'] = re.sub(r'src="(https?://[^"]+)"', rep, a['content'])
        a['image_local'] = [s for s in re.findall(r'src="([^"]+)"', a['content']) if not s.startswith('http')]
        a['missing_images'] = [s for s in re.findall(r'src="(https?://[^"]+)"', a['content'])]

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print('data.json 已更新（src 本地化）')
