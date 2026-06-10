#!/usr/bin/env python3
# Monorepo 建置：跑每個 recipe 的產生器，彙整輸出到 dist/<recipe>/ 給 GitHub Pages。
# 新增 recipe：建資料夾 + 在 RECIPES 註冊 {dir, entry, title}。entry 須把產出寫到 <dir>/public/。
import os, sys, shutil, subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))

RECIPES = [
    {"dir": "world-cup-2026", "entry": "gen_wc_ics.py", "title": "⚽ 2026 世界盃賽程（繁中）"},
]

def main():
    dist = os.path.join(ROOT, "dist")
    if os.path.isdir(dist):
        shutil.rmtree(dist)
    os.makedirs(dist)
    built = []
    for r in RECIPES:
        rdir = os.path.join(ROOT, r["dir"])
        print(f"[build] {r['dir']} -> {r['entry']}")
        subprocess.run([sys.executable, os.path.join(rdir, r["entry"])], check=True)
        src = os.path.join(rdir, "public")
        if not os.path.isdir(src):
            sys.exit(f"[error] {r['dir']} 未產生 public/")
        shutil.copytree(src, os.path.join(dist, r["dir"]))
        built.append(r)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    items = "".join('<li><a href="%s/">%s</a></li>' % (r["dir"], r["title"]) for r in built)
    html = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>Poke Recipes</title>'
            '<style>body{font-family:system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;'
            'max-width:40rem;margin:3rem auto;padding:0 1rem;line-height:1.9}</style>'
            '<h1>Poke Recipes</h1><ul>' + items + '</ul>'
            '<p style="color:#888;font-size:.9rem">更新 ' + now + '</p></html>')
    open(os.path.join(dist, "index.html"), "w", encoding="utf-8").write(html)
    print(f"[done] {len(built)} recipe(s) -> dist/")

if __name__ == "__main__":
    main()
