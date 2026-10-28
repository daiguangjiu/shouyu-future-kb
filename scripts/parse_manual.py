#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 xianyu-ops-manual 单文件手册 → manual.json（按章/节切分）"""
import re, json, html as H

SRC = 'work/manual/index.html'

h = open(SRC, encoding='utf-8').read()
body = re.search(r'<main class="content md-content">(.*?)</main>', h, re.S).group(1)

# 去掉标题与副标题
body = re.sub(r'<h1>.*?</h1>', '', body, flags=re.S)
body = re.sub(r'<p class="doc-sub">.*?</p>', '', body, flags=re.S)
body = re.sub(r'<p class="doc-foot">.*?</p>', '', body, flags=re.S)

# 按 h2 切章
chapters = []
parts = re.split(r'(<h2 id="[^"]+"[^>]*>.*?</h2>)', body, flags=re.S)
cur = None
for p in parts:
    if not p.strip():
        continue
    m = re.match(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', p, re.S)
    if m:
        raw = m.group(2)
        title = re.sub(r'<[^>]+>', '', raw).strip()
        emoji = ''
        em = re.match(r'^([\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]+)\s*(.*)$', title)
        if em:
            emoji, title = em.group(1), em.group(2).strip()
        cur = {'id': m.group(1), 'title': title, 'emoji': emoji, 'raw_title': title, 'sections': []}
        chapters.append(cur)
    elif cur is not None:
        # 章内按 h3 切节
        sub = re.split(r'(<h3 id="[^"]+"[^>]*>.*?</h3>)', p, flags=re.S)
        pre = sub[0]
        if pre.strip():
            cur['sections'].insert(0, {'id': '', 'title': '章前说明', 'html': pre.strip(), 'subs': []})
        for i in range(1, len(sub), 2):
            h3raw = sub[i]
            sid = re.search(r'id="([^"]+)"', h3raw).group(1)
            stitle = re.sub(r'<[^>]+>', '', h3raw).strip()
            content = sub[i+1] if i+1 < len(sub) else ''
            # h4 归入本节
            cur['sections'].append({'id': sid, 'title': stitle, 'html': content.strip(), 'subs': []})

# 为每个 section 抽取 h4 子标题（章内 TOC）
for c in chapters:
    for s in c['sections']:
        s['subs'] = [{'id': (re.search(r'id="([^"]+)"', x).group(1) if 'id="' in x else ''),
                       'title': re.sub(r'<[^>]+>', '', x).strip()}
                      for x in re.findall(r'<h4[^>]*>.*?</h4>', s['html'], re.S)]

# 全文纯文本（搜索用）
def to_text(x):
    x = re.sub(r'<[^>]+>', ' ', x)
    x = H.unescape(x)
    x = x.replace('﻿', '')
    return re.sub(r'\s+', ' ', x).strip()

for c in chapters:
    c['text'] = to_text(' '.join(s['title'] + ' ' + s['html'] for s in c['sections']))
    c['count'] = len(c['sections'])
    c['subs_count'] = sum(len(s['subs']) for s in c['sections'])
    c['tables'] = sum(s['html'].count('<table') for s in c['sections'])

meta_version = ''
mv = re.search(r'V(\d{4}\.\d{2}\.\d{2})', body)
if mv:
    meta_version = 'V' + mv.group(1)

out = {'title': '闲鱼平台运营完全手册', 'version': meta_version, 'chapters': chapters}

with open('work/manual.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f'解析完成：{len(chapters)} 章')
for c in chapters:
    print(f"  {c['id']:>10} | {c['title'][:36]:<38} 节{c['count']:>2} 小节{c['subs_count']:>3} 表{c['tables']:>3} | {len(c['text'])}字")
