#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""授渔未来 · 对外知识库重建 v3
1) 对外化清洗：去内部核查痕迹 / 删AI示意图占位 / 剔除内部版本日志与测试条目
2) 按对外知识库逻辑重划类目模块（6 模块 / 21 板块）
3) 与上一版快照比对 → 标记新增/更新条目，追加更新日志
4) 重算关联推荐，输出 data3.json + changelog.json
"""
import json, re, math, html as H, hashlib, time, datetime, os
from collections import Counter

src = json.load(open('work/data2.json', encoding='utf-8'))
items = {it['id']: it for s in src['sections'] for it in s['items']}

# ---------- 变更比对：上一版快照 ----------
PREV_PATH = 'work/data_prev.json'
LOG_PATH = 'work/changelog.json'
prev = {}
if os.path.exists(PREV_PATH):
    try:
        prev = json.load(open(PREV_PATH, encoding='utf-8')).get('items', {})
    except Exception:
        prev = {}
IS_BASELINE = not prev          # 无快照 = 首次收录基线
NOW = int(time.time())
STAMP = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def content_hash(h):
    """忽略空白差异的内容指纹"""
    n = re.sub(r'\s+', '', h or '')
    return hashlib.md5(n.encode('utf-8')).hexdigest()[:12]

# ========== 1. 对外化清洗 ==========
DROP_IDS = {'sec-1', 'a497114254628229'}   # 最近更新(内部版本日志) / 测试(垃圾条目)


def sanitize(c):
    if not c:
        return ''
    c = c.replace('﻿', '')

    # a. 删除「图：xxx（AI示意图，点击放大）」说明句 与 [图片: xxx] 占位符
    c = re.sub(r'<p[^>]*>\s*(?:图[：:][^<]{0,80}?（AI示意图[^）]*）|\[图片[：:][^\]]{0,90}\])\s*</p>', '', c)
    c = re.sub(r'(?:图[：:][^<]{0,80}?（AI示意图[^）]*）|\[图片[：:][^\]]{0,90}\])', '', c)
    c = re.sub(r'<p>\s*</p>', '', c)

    # b. 删除「⚠️ 核查备注：...」整段（内部核查过程，对外无意义）
    c = re.sub(r'<p[^>]*>(?:(?!</p>).)*?核查备注(?:(?!</p>).)*?</p>', '', c, flags=re.S)
    c = re.sub(r'核查备注[^<]{0,400}', '', c)

    # c. 去除 [待核实] 内部标记（章节顶部统一加免责说明替代）
    c = c.replace('[待核实]', '')
    c = re.sub(r'\(\s*\)\s*', '', c)
    c = re.sub(r'\[\s*\]', '', c)

    # d. 第十四章口径说明中性化
    c = c.replace('本章的「健康值 / 预警值 / 达标线」均为培训沉淀的经验参考值，不是平台官方口径',
                  '本章的「健康值 / 预警值 / 达标线」为行业经验参考值，不是平台官方口径')
    c = c.replace('培训沉淀的经验参考值', '行业经验参考值')

    # e. 其余内部措辞中性化
    c = c.replace('不得作为平台规则对外培训', '请以平台最新公示为准')
    c = c.replace('不得作为规则引用', '仅供趋势参考')
    c = c.replace('只可作为', '可作为')

    # f. 折叠空段
    c = re.sub(r'<p>(?:\s|&nbsp;|<br\s*/?>)*</p>', '', c)
    c = re.sub(r'(?:<p>(?:\s|&nbsp;|<br\s*/?>)*</p>\s*){2,}', '', c)
    c = re.sub(r'<p>\s+', '<p>', c)
    c = re.sub(r'\s+</p>', '</p>', c)
    c = re.sub(r'(?:<br\s*/?>\s*){3,}', '<br><br>', c)
    return c.strip()


def to_text(x):
    x = re.sub(r'<[^>]+>', ' ', x)
    x = H.unescape(x).replace('﻿', '')
    return re.sub(r'\s+', ' ', x).strip()


DISCLAIMER = ('<p class="note"><strong>内容说明：</strong>本节部分数据与口径来自公开报道、平台公告及卖家实操经验，'
              '非平台官方公布的全部数据，实际规则以闲鱼官方最新公示为准（闲鱼 APP → 我的 → 设置 → 闲鱼公约）。</p>')

# ========== 2. 新类目体系（对外知识库）============
M = [
    ('开店入驻', '起步篇 · 从 0 到 1 开启店铺', 'orange', [
        ('平台认知与账号搭建', ['sec-2', 'sec-6']),
        ('鱼小铺开通与功能', ['sec-11', 'a498411243476357', 'a498409705018757', 'a498409539745157',
                              'a498409349989701', 'a498408474531205', 'a498773110658437', 'a499947955983749']),
        ('账号装修与人设打造', ['a498417645995397', 'a498413763863941']),
    ]),
    ('商品运营', '卖货篇 · 把商品做对', 'orange', [
        ('类目选择与类目打法', ['a498422174320005', 'a498420870378885', 'a498421207266693', 'sec-23']),
        ('标题描述与图片优化', ['sec-17', 'a498416974513541', 'a498415052670277']),
        ('发布避雷与抽奖规范', ['a498420279600517', 'a498417978037637', 'a498417787647365']),
    ]),
    ('流量增长', '曝光篇 · 把流量做起来', 'blue', [
        ('流量全景与推荐机制', ['a498440392717701', 'a498458897921413', 'a1067970483994629',
                                'a498468623795589', 'a498469369845125']),
        ('搜索召回与排序逻辑', ['a498448820090181', 'a498449741493573', 'a498451325527429',
                                'a498454249600389', 'a498457972299141']),
        ('涨粉与粉丝运营', ['a498439005287749', 'a498425842038149', 'a498423363646853', 'a498413086889349']),
        ('付费投放与成长权重', ['sec-30']),
        ('高级流量与规模扩张', ['sec-43', 'sec-34', 'sec-52']),
    ]),
    ('合规风控', '底线篇 · 不踩红线', 'green', [
        ('社区公约与行为规范', ['a498834499044741', 'a498834062509445', 'a499947645891973']),
        ('信息发布与禁售限售', ['a498835398546821', 'a498833513358725', 'a498772537632133', 'a498490926056837']),
        ('管理规范与违规处罚', ['sec-62', 'a498832766117253', 'a499946761471365', 'a499957637465477', 'a498418596873605']),
        ('风控与账号安全', ['sec-57', 'a498419103917445', 'a498411888551301', 'a498412499355013']),
    ]),
    ('交易售后', '履约篇 · 把交易做稳', 'blue', [
        ('保证金与履约时效', ['a498491379729797', 'a498495935731077', 'a498774171583877', 'sec-67']),
        ('退货退款与买家保障', ['a498493973546309', 'a498492590744965', 'a498767719605573']),
        ('纠纷处理与防坑维权', ['a498827573106053', 'a499946252522885', 'a498419828663685', 'a498773233685893']),
    ]),
    ('经营提效', '管理篇 · 把效率做高', 'green', [
        ('数据看板与考核指标', ['sec-72']),
        ('执行标准与 SOP 清单', ['sec-86']),
        ('官方规则速查手册', ['sec-76']),
    ]),
]

# 完整性校验
assigned = []
for mod, sub, col, secs in M:
    for sname, ids in secs:
        assigned += ids
dup = [k for k, v in Counter(assigned).items() if v > 1]
missing = sorted(set(items) - set(assigned) - DROP_IDS)
extra = sorted(set(assigned) - set(items))
assert not dup, f'重复归类: {dup}'
assert not missing, f'遗漏条目: {missing}'
assert not extra, f'未知条目: {extra}'
print(f'归类校验通过：{len(assigned)} 条，无重复/遗漏')

# ========== 3. 构建新数据 ==========
new_sections = []
kept = []
changes = []
# 同名条款去歧义：同一规则在「社区规则」与「最新公告」各有一份，后出现的标注来源
title_total = {}
for _mod, _sub, _col, _secs in M:
    for _sname, _ids in _secs:
        for _iid in _ids:
            _t = items[_iid]['title']
            title_total[_t] = title_total.get(_t, 0) + 1
title_seen = {}

for mod, sub, col, secs in M:
    for sname, ids in secs:
        bucket = []
        for iid in ids:
            it = items[iid]
            html = sanitize(it['html'])
            if it['kind'] == 'chapter':
                html = DISCLAIMER + html
            text = to_text(html)
            # —— 变更比对 ——
            ch = content_hash(html)
            p = prev.get(it['id'])
            if IS_BASELINE:
                is_new, is_updated, upd_at = False, False, 0
                change_type = 'baseline'
            elif p is None:
                is_new, is_updated, upd_at = True, False, NOW
                change_type = 'new'
            elif p.get('hash') != ch:
                is_new, is_updated, upd_at = False, True, NOW
                change_type = 'updated'
            else:
                is_new, is_updated, upd_at = False, False, p.get('updated_at', 0)
                change_type = None
            title = it['title']
            if title_total.get(title, 0) > 1:
                title_seen[title] = title_seen.get(title, 0) + 1
                if title_seen[title] >= 2 and '公告版' not in title:
                    title = title + '（公告版）'
            bucket.append({
                'id': it['id'],
                'kind': it['kind'],
                'module': mod,
                'module_sub': sub,
                'section': sname,
                'title': title,
                'title_raw': it['title'],
                'html': html,
                'text': text,
                'toc': it.get('toc') or [],
                'hash': ch,
                'is_new': is_new,
                'is_updated': is_updated,
                'updated_at': upd_at,
                'meta': {
                    'publish_time': it['meta'].get('publish_time', ''),
                    'source': '小渔数科闲参谋',
                    'tables': html.count('<table'),
                    'imgs': len(re.findall(r'<img', html)),
                    'words': len(text),
                    'sections': it['meta'].get('sections', 0),
                    'subs': it['meta'].get('subs', 0),
                    'version': it['meta'].get('version', ''),
                },
            })
            kept.append(bucket[-1])
            if change_type in ('new', 'updated'):
                changes.append({
                    'id': it['id'], 'title': title, 'type': change_type,
                    'module': mod, 'section': sname, 'kind': it['kind'],
                    'date': STAMP, 'ts': NOW,
                    'words': len(text),
                })
        new_sections.append({'module': mod, 'module_sub': sub, 'section': sname,
                             'color': col, 'count': len(bucket), 'items': bucket})

# ========== 4. 关联推荐（重算）============
def tokens(t):
    t = t.lower()
    cn = re.findall(r'[一-龥]+', t)
    g = []
    for w in cn:
        g += [w[i:i + 2] for i in range(len(w) - 1)] or [w]
    return g + re.findall(r'[a-z0-9]{2,}', t)


N = len(kept)
tf = {it['id']: Counter(tokens(it['title'] + ' ' + it['title'] + ' ' + it['text'][:2500])) for it in kept}
df = Counter()
for c in tf.values():
    df.update(c.keys())
V = {}
for it in kept:
    c = tf[it['id']]
    tot = sum(c.values()) or 1
    V[it['id']] = {k: (v / tot) * math.log(N / (1 + df[k])) for k, v in c.items()}


def cos(a, b):
    va, vb = V[a], V[b]
    if len(va) > len(vb):
        va, vb = vb, va
    return sum(v * vb.get(k, 0) for k, v in va.items())


TOPIC = {
    '开店': ['注册', '认证', '资质', '鱼小铺', '开店', '招商', '芝麻', '闲气值'],
    '商品': ['标题', '主图', '描述', '类目', '发布', '上架', '定价', '九宫格', '选品'],
    '流量': ['曝光', '流量', '搜索', '召回', '排序', '推荐', '搜索词', '擦亮', '投放'],
    '粉丝': ['粉丝', '涨粉', '关注', '抽奖', '人设', '分享'],
    '合规': ['违规', '禁售', '限售', '处罚', '扣分', '红线', '违禁词', '申诉', '公约', '规范'],
    '交易': ['保证金', '发货', '退货', '退款', '纠纷', '七天', '履约', '超时', '赔付'],
    '成长': ['等级', '权重', '闲鱼币', '圈子', '鱼塘', '值得买', '无忧卖', '矩阵', '鱼力值'],
}


def tags(it):
    b = it['title'] + ' ' + it['text'][:2200]
    return {k for k, ws in TOPIC.items() if any(w in b for w in ws)}


TAG = {it['id']: tags(it) for it in kept}


def series_key(t):
    for pat, g in [(r'^【(.+?)】', 'S:'), (r'^(鱼小铺用户反馈答疑)', 'S:'), (r'^(第[一二三四五六七八九十]+章)', 'S:')]:
        m = re.match(pat, t)
        if m:
            return g + m.group(1)
    return 'T:' + t


for it in kept:
    sc = []
    for o in kept:
        if o['id'] == it['id']:
            continue
        s = cos(it['id'], o['id']) + len(TAG[it['id']] & TAG[o['id']]) * 0.035
        if it['kind'] != o['kind'] and it['module'] == o['module']:
            s += 0.02
        sc.append((s, o))
    sc.sort(key=lambda x: -x[0])
    picked, ut, us = [], set(), set()
    for s, o in sc:
        if s <= 0.05:
            break
        if o['title'] in ut:
            continue
        sk = series_key(o['title'])
        if sk in us:
            continue
        ut.add(o['title'])
        us.add(sk)
        picked.append(o['id'])
        if len(picked) >= 4:
            break
    it['related'] = picked

out = {
    'brand': '授渔未来',
    'version': items['sec-76']['meta'].get('version', ''),
    'generated_at': NOW,
    'generated_at_text': STAMP,
    'modules': [],
    'sections': new_sections,
    'stats': {
        'modules': len(M),
        'sections': len(new_sections),
        'items': len(kept),
        'articles': sum(1 for it in kept if it['kind'] == 'article'),
        'chapters': sum(1 for it in kept if it['kind'] == 'chapter'),
        'tables': sum(it['meta']['tables'] for it in kept),
        'imgs': sum(it['meta']['imgs'] for it in kept),
        'words': sum(it['meta']['words'] for it in kept),
    },
}
seen = set()
MOD_DESC = {
 '开店入驻':'第一次开店要走的完整链路：注册与实名认证、经营资质提交、鱼小铺开通与功能答疑，直到账号装修与人设定位。',
 '商品运营':'商品本身做对，后面的流量才接得住——类目选择、标题公式、图文表达、发布避雷与抽奖规范。',
 '流量增长':'从搜索召回到推荐算法，从自然流量到超级擦亮投放，再到涨粉、值得买、无忧卖与矩阵放大。',
 '合规风控':'社区公约与发布规范原文、违规分级与扣分逻辑、十大禁区与违禁词，外加账号安全与风控排查。',
 '交易售后':'保证金额度、发货时效、退货退款与买家保障，到交易争议处理与恶意行为应对，把每一单做稳。',
 '经营提效':'核心数据看板与考核线、每日每周执行清单与投放 SOP，以及 29 项官方规则的速查手册。',
}
MOD_DESC = {
 '开店入驻':'第一次开店要走的完整链路：注册与实名认证、经营资质提交、鱼小铺开通与功能答疑，直到账号装修与人设定位。',
 '商品运营':'商品本身做对，后面的流量才接得住——类目选择、标题公式、图文表达、发布避雷与抽奖规范。',
 '流量增长':'从搜索召回到推荐算法，从自然流量到超级擦亮投放，再到涨粉、值得买、无忧卖与矩阵放大。',
 '合规风控':'社区公约与发布规范原文、违规分级与扣分逻辑、十大禁区与违禁词，外加账号安全与风控排查。',
 '交易售后':'保证金额度、发货时效、退货退款与买家保障，到交易争议处理与恶意行为应对，把每一单做稳。',
 '经营提效':'核心数据看板与考核线、每日每周执行清单与投放 SOP，以及 29 项官方规则的速查手册。',
}
for mod, sub, col, secs in M:
    out['modules'].append({
        'name': mod, 'sub': sub, 'color': col, 'desc': MOD_DESC.get(mod, ''),
        'section_names': [s['section'] for s in new_sections if s['module'] == mod],
        'count': sum(len(s['items']) for s in new_sections if s['module'] == mod),
    })

with open('work/data3.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# ---------- 5. 更新日志 ----------
history = []
if os.path.exists(LOG_PATH):
    try:
        history = json.load(open(LOG_PATH, encoding='utf-8')).get('versions', [])
    except Exception:
        history = []

added = [c for c in changes if c['type'] == 'new']
updated = [c for c in changes if c['type'] == 'updated']

if IS_BASELINE:
    # 首次收录：记录基线，不标记新增
    record = {
        'date': STAMP[:10], 'time': STAMP[11:], 'ts': NOW, 'version': out['version'],
        'type': 'baseline',
        'summary': {'added': 0, 'updated': 0, 'total': len(kept)},
        'note': '知识库首次收录，建立内容基线。',
        'changes': [],
    }
    history.insert(0, record)
else:
    record = {
        'date': STAMP[:10], 'time': STAMP[11:], 'ts': NOW, 'version': out['version'],
        'type': 'update',
        'summary': {'added': len(added), 'updated': len(updated), 'total': len(kept)},
        'note': ('本周无内容变化' if not changes else
                 f'新增 {len(added)} 条，更新 {len(updated)} 条'),
        'changes': changes,
    }
    # 同一天多次运行则合并到当天记录
    if history and history[0].get('date') == record['date'] and history[0].get('type') == 'update':
        h0 = history[0]
        h0['changes'] = h0.get('changes', []) + changes
        h0['summary'] = {
            'added': h0['summary']['added'] + len(added),
            'updated': h0['summary']['updated'] + len(updated),
            'total': len(kept),
        }
        h0['time'] = STAMP[11:]
        h0['ts'] = NOW
        h0['note'] = (f"新增 {h0['summary']['added']} 条，更新 {h0['summary']['updated']} 条"
                      if h0['changes'] else '本日累计无内容变化')
    else:
        history.insert(0, record)

changelog = {
    'latest': history[0] if history else record,
    'versions': history[:60],          # 保留最近 60 次更新记录
}
with open('work/changelog.json', 'w', encoding='utf-8') as f:
    json.dump(changelog, f, ensure_ascii=False, indent=1)

print(f"\n对外知识库重建完成：{len(M)} 模块 / {len(new_sections)} 板块 / {len(kept)} 条目")
for m in out['modules']:
    print(f"  ◆ {m['name']}（{m['sub']}） {m['count']} 条")
    for s in new_sections:
        if s['module'] == m['name']:
            print(f"      - {s['section']:<22} {s['count']}")
print('统计:', out['stats'])
# 清洗效果核查
raw_hits = sum(len(re.findall(r'\[待核实\]|核查备注|AI示意图|\[图片[：:]', it['html'])) for it in kept)
print(f'清洗后残留内部标记: {raw_hits}')
print(f"变更：新增 {len(added)} / 更新 {len(updated)}  → changelog.json（历史 {len(history)} 条）")
for c in changes[:12]:
    print(f"   [{c['type']}] {c['module']} / {c['section']} :: {c['title'][:40]}")
