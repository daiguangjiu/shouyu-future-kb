#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""授渔未来 · 每周自动刷新
流程：抓取官方文章 + 拉取手册最新版 → 图片镜像 → 融合 → 差异比对/标红 → 构建站点 → 提交推送 → 验证上线
任一步失败即中止，线上站点保持可用版本不变。
"""
import os, sys, json, subprocess, shutil, time, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PY = sys.executable
MANUAL_URL = 'https://daiguangjiu.github.io/xianyu-ops-manual/index.html'
REPO = 'daiguangjiu/shouyu-future-kb'
PAGES = f'https://{REPO.split("/")[0]}.github.io/{REPO.split("/")[1]}/'
OUT = os.path.join(ROOT, 'output', '授渔未来')

LOG_LINES = []


def step(msg):
    line = f'[{datetime.datetime.now():%H:%M:%S}] {msg}'
    print(line, flush=True)
    LOG_LINES.append(line)


def run(cmd, desc, allow_fail=False):
    step(desc)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (r.stdout or '').strip().splitlines()
    err = (r.stderr or '').strip().splitlines()
    for l in out[-6:]:
        print('   ', l, flush=True)
    if r.returncode != 0:
        for l in err[-8:]:
            print('  !', l, flush=True)
        if not allow_fail:
            step(f'✗ 失败中止：{desc}')
            sys.exit(1)
        step(f'⚠ 忽略失败：{desc}')
    return r.returncode


def main():
    step('=== 授渔未来 · 每周刷新开始 ===')

    # 0. 同步比对基线：以上次构建产出的内容指纹快照为准
    snap = os.path.join(OUT, 'data_prev.json')
    if os.path.exists(snap):
        shutil.copy(snap, 'work/data_prev.json')
        step('已同步上次构建的内容指纹基线用于差异比对')
    elif os.path.exists('work/data_prev.json'):
        step('沿用 work 目录中的基线快照')

    # 1. 抓取闲鱼官方内容（授渔学堂 + 社区公约）
    run(f'{PY} work/scrape.py', '抓取闲鱼官方文章（CMS 接口）')

    # 2. 拉取运营手册最新版
    step('拉取运营手册最新版')
    os.makedirs('work/manual', exist_ok=True)
    try:
        req = urllib.request.Request(MANUAL_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        with open('work/manual/index.html', 'wb') as f:
            f.write(raw)
        step(f'  手册已下载 {len(raw)//1024} KB')
    except Exception as e:
        step(f'⚠ 手册下载失败（{e}），沿用本地已有版本')

    # 3. 解析手册
    run(f'{PY} work/parse_manual.py', '解析运营手册章节结构')

    # 4. 图片本地化
    run(f'{PY} work/mirror.py', '镜像正文图片到本地')

    # 5. 融合为 data2.json
    run(f'{PY} work/merge.py', '融合官方内容与手册章节')

    # 6. 重建 + 差异比对（打红标、写更新日志）
    run(f'{PY} work/rebuild.py', '重建数据并比对差异（新增/更新标记 + 更新日志）')

    # 7. 构建站点
    run(f'{PY} work/build3.py', '构建静态站点')

    # 7.5 回写新基线：下次刷新要与本次结果比对，而不是与最初基线比对
    try:
        shutil.copy(os.path.join(OUT, 'data_prev.json'), 'work/data_prev.json')
        step('已回写内容指纹基线，供下次刷新比对')
    except Exception as e:
        step(f'⚠ 基线回写失败 {e}')

    # 8. 变更摘要
    try:
        log = json.load(open('work/changelog.json', encoding='utf-8'))
        latest = log['latest']
        step(f"本次核查：新增 {latest['summary']['added']} 条 / 更新 {latest['summary']['updated']} 条")
        for c in latest.get('changes', [])[:20]:
            step(f"   [{c['type']}] {c['module']} / {c['section']} :: {c['title'][:44]}")
    except Exception as e:
        step(f'⚠ 读取更新日志失败 {e}')

    # 9. 提交并推送（SSH 443：本机 github.com:443 不通，ssh.github.com:443 可用）
    if os.path.isdir(os.path.join(OUT, '.git')):
        run('cd output/授渔未来 && git add -A', '暂存变更')
        r = run('cd output/授渔未来 && git commit -q -m "chore: 每周内容核查更新 '
                f'$(date +%Y-%m-%d)"', '提交变更', allow_fail=True)
        if r != 0:
            step('（无内容变化，跳过提交）')
        else:
            run(f'cd output/授渔未来 && git push ssh://git@ssh.github.com:443/{REPO}.git main:main',
                '推送到 GitHub')
    else:
        step('✗ 未找到 git 仓库，跳过推送')
        sys.exit(1)

    # 10. 等待 Pages 重建并验证
    step('等待 GitHub Pages 重建（约 60 秒）…')
    ok = False
    for i in range(10):
        time.sleep(20)
        try:
            req = urllib.request.Request(PAGES, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode('utf-8', 'replace')
            if 'const DATA =' in body and '授渔未来' in body:
                step(f'✓ 线上验证通过（第 {i+1} 次探测，HTTP {r.status}）')
                ok = True
                break
        except Exception as e:
            step(f'  探测 {i+1}: {e}')
    if not ok:
        step('⚠ 线上探测未通过，请手动检查 ' + PAGES)

    step('=== 刷新流程结束 ===')


if __name__ == '__main__':
    main()
