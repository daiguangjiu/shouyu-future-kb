#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 xygj.pro 小铺学堂(type=21) 与 闲鱼社区公约(type=22) 全量内容"""
import json, time, urllib.request, os, sys

API_LIST = 'https://www.xygj.pro/api/seller/cms/article/list'
API_DETAIL = 'https://www.xygj.pro/api/seller/cms/article/detail'

# (type, category_id, 模块名, 板块名)
GROUPS = [
    (21, 210001, '小铺学堂', '流量曝光'),
    (21, 210002, '小铺学堂', '规则解读'),
    (21, 210003, '小铺学堂', '新人必看'),
    (21, 210004, '小铺学堂', '表达技巧'),
    (22, 220001, '闲鱼社区公约', '社区规则'),
    (22, 220002, '闲鱼社区公约', '最新闲鱼公告'),
    (22, 220003, '闲鱼社区公约', '闲鱼用户违规公示'),
]

HDR = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'}


def post(url, payload, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=HDR)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def main():
    out = {'source': 'https://www.xygj.pro', 'modules': []}
    total = 0
    for typ, cid, module, section in GROUPS:
        r = post(API_LIST, {'type': typ, 'category_id': cid, 'page_size': 500})
        lst = (r.get('data') or {}).get('list') or []
        print(f'[{module}/{section}] 列表 {len(lst)} 篇', flush=True)
        articles = []
        for idx, a in enumerate(lst, 1):
            try:
                d = (post(API_DETAIL, {'article_id': a['article_id']}).get('data') or {})
            except Exception as e:
                print(f'  !! 详情失败 {a["article_id"]} {e}', flush=True)
                continue
            content = d.get('content') or ''
            articles.append({
                'article_id': a['article_id'],
                'title': (d.get('title') or a.get('title') or '').strip(),
                'summary': (d.get('summary') or '').strip(),
                'content': content,
                'text': html_to_text(content),
                'image': d.get('image') or '',
                'link': d.get('link') or '',
                'video': d.get('video') or '',
                'publish_time': d.get('publish_time') or a.get('publish_time') or '',
                'category_name': d.get('category_name') or section,
                'section': section,
                'module': module,
            })
            print(f'  [{idx}/{len(lst)}] {a["title"][:36]}  ({len(content)} chars)', flush=True)
            time.sleep(0.12)
        out['modules'].append({
            'type': typ, 'category_id': cid, 'module': module,
            'section': section, 'count': len(articles), 'articles': articles,
        })
        total += len(articles)

    out['total_articles'] = total
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'\n完成：{total} 篇 -> data.json')
    for m in out['modules']:
        print(f"  {m['module']} / {m['section']}: {m['count']}")


def html_to_text(html):
    import re
    h = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.S | re.I)
    h = re.sub(r'<br\s*/?>', '\n', h, flags=re.I)
    h = re.sub(r'</(p|div|li|h[1-6]|tr)>', '\n', h, flags=re.I)
    h = re.sub(r'<[^>]+>', '', h)
    h = h.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    h = h.replace('﻿', '')
    lines = [ln.strip() for ln in h.split('\n')]
    return '\n'.join([ln for ln in lines if ln])


if __name__ == '__main__':
    main()
