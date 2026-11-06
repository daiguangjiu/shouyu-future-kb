#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成新增内容源：闲鱼开店100问（11 章）+ 运营工具（数据统计表）
输出 work/new_sources.json，供 merge.py 合并
"""
import json, re, html as H, os
from urllib.parse import quote

FAQ = 'work/faq100.json'
OUT = 'work/new_sources.json'
TOOL_FILE = '闲鱼店铺链接数据统计表(1).xlsx'
TOOL_DIR = 'work/assets/tools'
TOOL_URL = 'assets/tools'


def esc(t):
    return H.escape(t or '', quote=False)


def ans_to_html(a):
    """答案多段 → 多段落 HTML；保留换行结构"""
    parts = [p.strip() for p in re.split(r'\n+', a or '') if p.strip()]
    if not parts:
        return ''
    out = []
    for p in parts:
        # 行内换行用 <br>
        out.append('<p>' + esc(p).replace('\n', '<br>') + '</p>')
    return ''.join(out)


# FAQ 数据源回退：本地 → 站点仓库副本
FAQ_CANDIDATES = [FAQ, 'output/授渔未来/data/faq100.json']
faq_path = next((f_ for f_ in FAQ_CANDIDATES if os.path.exists(f_)), None)
if not faq_path:
    raise SystemExit('✗ 未找到 100 问数据源（work/faq100.json 或站点仓库副本），本轮跳过新增来源')
if faq_path != FAQ:
    print(f'  · 100 问数据取自站点仓库副本：{faq_path}')
faq = json.load(open(faq_path, encoding='utf-8'))

sections = []
faq_items = []
for ci, ch in enumerate(faq, 1):
    cid = f'faq-c{ci}'
    toc = []
    body = []
    if ch.get('lead'):
        body.append(f'<p class="lead">{esc(ch["lead"])}</p>')
    for qi, q in enumerate(ch['questions'], 1):
        aid = f'{cid}-q{qi}'
        toc.append({'id': aid, 'title': q['q']})
        body.append(f'<h3 id="{aid}">{esc(q["q"])}</h3>')
        body.append(ans_to_html(q['a']))
    html = ''.join(body)
    text = H.unescape(re.sub(r'<[^>]+>', ' ', html))
    text = re.sub(r'\s+', ' ', text).strip()
    item = {
        'id': cid,
        'kind': 'faq_chapter',
        'module': '开店100问',
        'section': ch['title'],
        'title': ch['title'],
        'summary': ch.get('lead', '')[:120],
        'html': html,
        'text': text,
        'toc': toc,
        'meta': {
            'publish_time': '2026-11',
            'source': '闲鱼开店100问手册',
            'tables': html.count('<table'),
            'imgs': 0,
            'words': len(text),
            'sections': len(ch['questions']),
            'subs': 0,
            'version': '2026年11月版',
            'qcount': len(ch['questions']),
        },
    }
    faq_items.append(item)
    sections.append({
        'module': '开店100问', 'section': ch['title'], 'kind': 'faq', 'color': 'purple',
        'count': 1, 'items': [item],
    })

# ---------- 运营工具 ----------
dl_name = '闲鱼店铺链接数据统计表.xlsx'
dl_url = f'{TOOL_URL}/{quote(dl_name)}'

tool_html = f'''
<p class="lead">这是一份可以直接拿去用的闲鱼店铺运营数据台账。把每天的链接变化和核心指标填进去，看板会自动算出你要的数，再照着「使用说明」里的五条诊断思路反推该改哪个链接。</p>

<div class="toolbox">
  <div class="tool-dl">
    <div class="tool-ico">📊</div>
    <div class="tool-info">
      <div class="tool-name">{esc(dl_name)}</div>
      <div class="tool-meta">Excel 工作簿 · 4 个子表 · 含公式与图表 · 可直接填写</div>
    </div>
    <a class="dlbtn" href="{dl_url}" download>下载表格 ↓</a>
  </div>
</div>

<h3>四个子表分别做什么</h3>
<table>
<thead><tr><th>子表</th><th>用途</th><th>怎么填</th></tr></thead>
<tbody>
<tr><td><strong>看板</strong></td><td>6 个核心 KPI、在架链接趋势图、每日成交额图、类目汇总，全部自动刷新</td><td>不用填，引用下面两张表自动算</td></tr>
<tr><td><strong>每日数据</strong></td><td>按天记录新增/下架链接、曝光、浏览、想要、咨询、成交单数与成交额</td><td>每天固定时间加一行，约 2 分钟</td></tr>
<tr><td><strong>链接明细</strong></td><td>登记需要重点跟踪的宝贝：标题、发布日期、类目、状态、售价与各项数据</td><td>每周集中更新一次重点链接即可</td></tr>
<tr><td><strong>使用说明</strong></td><td>填写流程 + 五条数据诊断规则（曝光低改标题、浏览低换首图、想要率低调价格等）</td><td>照着做，不用改</td></tr>
</tbody>
</table>

<h3>每天怎么填（约 2 分钟）</h3>
<ol>
<li>打开「每日数据」，每天固定时间（建议晚上）加一行：日期、新增链接、下架链接、曝光量、浏览量、新增想要数、咨询数、成交单数、成交额。</li>
<li>星期、净增链接、想要率、成交转化率都是公式自动算的，不要手填。</li>
<li>「在架链接总数」自动累计：新行把上一行公式往下拖即可（首行公式为期初在架数 + 新增 − 下架）。</li>
<li>新增行后，把看板图表引用范围和合计行 SUM 公式范围同步拉大。</li>
</ol>

<h3>「链接明细」怎么用</h3>
<ol>
<li>登记需要重点跟踪的链接（宝贝）：标题、发布日期、类目、状态、售价、曝光/浏览/想要/咨询/成交。</li>
<li>成交额、想要率自动计算；状态和类目有下拉选项（在售 / 已售 / 已下架）。</li>
<li>数据更新频率不用每天，建议每周集中更新一次重点链接。</li>
</ol>

<h3>怎么用数据反推该改哪里</h3>
<table>
<thead><tr><th>数据表现</th><th>问题定位</th><th>该怎么改</th></tr></thead>
<tbody>
<tr><td>曝光量低</td><td>标题关键词覆盖不够、没有擦亮</td><td>改标题（塞品牌词 + 型号 + 成色）、每天擦亮、鱼塘发帖</td></tr>
<tr><td>浏览量低于曝光的 15%</td><td>首图不吸引</td><td>换实拍首图：光线好、干净背景、多角度</td></tr>
<tr><td>想要率低于 2%（红色高亮）</td><td>价格偏高或描述没打动人</td><td>对标同行降价，描述里写清成色和入手故事</td></tr>
<tr><td>咨询多但成交少</td><td>回复话术与价格问题</td><td>设自动回复 + 小刀话术，报邮费砍掉犹豫</td></tr>
<tr><td>类目汇总里想要率、成交额高的类目（绿色高亮）</td><td>——</td><td>多铺同款/同类链接；连续两周 0 成交的链接下架换新</td></tr>
</tbody>
</table>

<p class="note"><strong>使用建议：</strong>这份表的价值不在记录，而在于「每日数据」和「链接明细」两张表交叉比对 —— 用类目维度找出高想要率、高成交额的那一类，再把链接明细里的同类链接全部按这个模板优化一遍，比凭感觉改标题有效得多。</p>
'''

tool_text = H.unescape(re.sub(r'<[^>]+>', ' ', tool_html))
tool_text = re.sub(r'\s+', ' ', tool_text).strip()

tool_item = {
    'id': 'tool-link-stats',
    'kind': 'tool',
    'module': '运营工具',
    'section': '数据统计工具',
    'title': '闲鱼店铺链接数据统计表',
    'summary': '可填写的运营数据台账：4 个子表、6 项 KPI、自动图表与诊断规则。',
    'html': tool_html,
    'text': tool_text,
    'toc': [],
    'meta': {
        'publish_time': '2026-11',
        'source': '小渔数科闲参谋',
        'tables': tool_html.count('<table'),
        'imgs': 0,
        'words': len(tool_text),
        'sections': 0,
        'subs': 0,
        'version': '',
        'download': dl_url,
        'download_name': dl_name,
    },
}

sections.append({
    'module': '运营工具', 'section': '数据统计工具', 'kind': 'tool', 'color': 'teal',
    'count': 1, 'items': [tool_item],
})

# 工具文件复制到站点资源目录
os.makedirs(TOOL_DIR, exist_ok=True)
import shutil
dst_xlsx = os.path.join(TOOL_DIR, dl_name)
src_xlsx = ('/Users/daiguangjiu/Library/Containers/com.tencent.xinWeChat/Data/Documents/'
            'xwechat_files/wxid_0436794366512_1309/temp/RWTemp/2026-11/'
            '3be966e1de835edeace23678badd90cb/' + TOOL_FILE)
repo_xlsx = os.path.join('output', '授渔未来', 'assets', 'tools', dl_name)
if os.path.exists(src_xlsx):
    shutil.copy(src_xlsx, dst_xlsx)
    print(f'工具文件已更新 → {TOOL_DIR}/{dl_name}（{os.path.getsize(dst_xlsx)//1024} KB）')
elif os.path.exists(repo_xlsx):
    shutil.copy(repo_xlsx, dst_xlsx)
    print(f'工具文件沿用仓库副本（{os.path.getsize(dst_xlsx)//1024} KB）')
else:
    print('⚠ 未找到工具源文件，工具下载可能失效')

out = {'sections': sections,
       'stats': {'faq_chapters': len(faq_items), 'faq_questions': sum(len(c['questions']) for c in faq),
                  'tools': 1}}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f'新增来源：100 问 {len(faq_items)} 章 / {out["stats"]["faq_questions"]} 问 + 运营工具 1 个')
