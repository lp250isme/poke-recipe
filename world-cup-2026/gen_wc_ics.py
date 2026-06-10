#!/usr/bin/env python3
# World Cup 2026 -> .ics 產生器（GitHub Actions 定時重跑，淘汰賽占位隨來源更新成真隊）
# 來源: openfootball/worldcup.json (public domain, 免 key)
# 重點: 時間一律存 UTC（日曆 app 自動顯示在地時區）；隊名用 team-map.json（不靠即興翻譯）
# 輸出: public/worldcup2026.ics + public/index.html（給 GitHub Pages serve）

import json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

SRC = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
HERE = os.path.dirname(os.path.abspath(__file__))
MAP = json.load(open(os.path.join(HERE, "team-map.json"), encoding="utf-8"))
TEAMS, ALIASES = MAP["teams"], MAP["aliases"]

ROUND_ZH = {
    "Round of 32": "32強", "Round of 16": "16強", "Quarter-final": "8強",
    "Semi-final": "4強", "Match for third place": "季軍戰", "Final": "決賽",
}

def load_data():
    try:
        with urllib.request.urlopen(SRC, timeout=20) as r:
            return json.load(r)
    except Exception as e:                       # 離線/沙箱時用本地快取（CI 不會走到）
        sys.stderr.write(f"[warn] fetch failed ({e}); fallback /tmp/wc_master.json\n")
        return json.load(open("/tmp/wc_master.json", encoding="utf-8"))

def resolve_team(name):
    """回傳 (顯示字串, 是否為真隊)。占位碼解讀成易懂中文。"""
    n = ALIASES.get(name, name)
    if n in TEAMS:
        t = TEAMS[n]
        return f"{t['emoji']} {t['zh']}", True
    if re.fullmatch(r"[1-9][A-L]", name):              # 2A = A組第2
        return f"{name[1]}組第{name[0]}", False
    if re.fullmatch(r"3[A-L/]+", name):                # 3A/B/C/D/F = 第三名組合
        return f"第三名({name[1:]} 組之一)", False
    if re.fullmatch(r"W\d+", name):
        return f"第{name[1:]}場勝者", False
    if re.fullmatch(r"L\d+", name):
        return f"第{name[1:]}場敗者", False
    return f"{name}(待確認)", False                     # 查無 -> 標記，不靜默吞掉

def to_utc(date_str, time_str):
    """'2026-06-11','13:00 UTC-6' -> datetime(UTC)。逐場依該場偏移換算。"""
    hm, tz = time_str.split()
    off = int(tz.replace("UTC", ""))
    local = datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M")
    return local - timedelta(hours=off)

def uid(m):
    if "num" in m:                                     # 淘汰賽穩定鍵：場次號
        return f"wc2026-m{m['num']}@worldcup"
    rnd = m.get("round", "")
    if rnd == "Final":
        return "wc2026-final@worldcup"
    if rnd == "Match for third place":
        return "wc2026-third@worldcup"
    s = lambda x: re.sub(r"[^A-Za-z0-9]", "", x)       # 小組賽：隊伍固定 -> date+隊名 穩定
    return f"wc2026-{m['date']}-{s(m['team1'])}-{s(m['team2'])}@worldcup"

def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

INDEX_TMPL = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 世界盃賽程（繁中）｜訂閱日曆</title>
<style>body{font-family:-apple-system,system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;max-width:42rem;margin:3rem auto;padding:0 1.2rem;line-height:1.7;color:#1a1a1a}a.btn{display:inline-block;background:#0a7a55;color:#fff;padding:.7rem 1.2rem;border-radius:.6rem;text-decoration:none;font-weight:600}code{background:#f2f2f2;padding:.15rem .4rem;border-radius:.3rem;word-break:break-all}.muted{color:#666;font-size:.9rem}</style>
</head><body>
<h1>⚽ 2026 世界盃賽程（繁中）</h1>
<p>訂閱一次，__N__ 場賽事自動進你的日曆：你的在地時區、繁中隊名 + 國旗，淘汰賽底定後自動更新。</p>
<p><a class="btn" id="sub" href="#">＋ 加入 Apple 行事曆</a></p>
<p class="muted">Google 行事曆：設定 → 新增日曆 → 透過網址 → 貼上：<br><code id="url"></code></p>
<p class="muted">資料：openfootball（public domain）｜最後更新 __NOW__</p>
<script>
var dir=location.pathname.replace(/[^/]*$/,'');
document.getElementById('url').textContent=location.origin+dir+'worldcup2026.ics';
document.getElementById('sub').href='webcal://'+location.host+dir+'worldcup2026.ics';
</script>
</body></html>"""

def build():
    data = load_data()
    matches = data["matches"]
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//kv//WorldCup2026//TW",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:2026 世界盃 (繁中)",
             "X-WR-TIMEZONE:UTC"]
    unresolved = []
    for m in matches:
        t1, ok1 = resolve_team(m["team1"])
        t2, ok2 = resolve_team(m["team2"])
        rnd = m.get("round", "")
        if rnd.startswith("Matchday"):
            grp = (m.get("group", "") or "").replace("Group ", "") + "組"
            summary = f"{t1} vs {t2}（{grp}）"
            for raw, ok in ((m["team1"], ok1), (m["team2"], ok2)):
                if not ok:
                    unresolved.append(raw)
        else:
            summary = f"🏆 {ROUND_ZH.get(rnd, rnd)}：{t1} vs {t2}"
        start = to_utc(m["date"], m["time"])
        end = start + timedelta(hours=2)
        desc = f"{rnd}｜{m.get('ground','')}｜資料: openfootball, 更新 {now}"
        lines += ["BEGIN:VEVENT", f"UID:{uid(m)}", f"DTSTAMP:{now}",
                  f"DTSTART:{start:%Y%m%dT%H%M%S}Z", f"DTEND:{end:%Y%m%dT%H%M%S}Z",
                  f"SUMMARY:{esc(summary)}", f"LOCATION:{esc(m.get('ground',''))}",
                  f"DESCRIPTION:{esc(desc)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    pub = os.path.join(HERE, "public")
    os.makedirs(pub, exist_ok=True)
    open(os.path.join(pub, "worldcup2026.ics"), "w", encoding="utf-8").write("\r\n".join(lines) + "\r\n")
    open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(
        INDEX_TMPL.replace("__N__", str(len(matches))).replace("__NOW__", now))
    return matches, lines, unresolved

if __name__ == "__main__":
    matches, lines, unresolved = build()
    n_ev = sum(1 for l in lines if l == "BEGIN:VEVENT")
    print(f"matches={len(matches)} vevents={n_ev} -> public/worldcup2026.ics + index.html")
    print(f"小組賽未對到隊名(應為空): {sorted(set(unresolved))}")
    if unresolved:
        sys.exit(1)                                    # CI: 有漏譯就讓 build 失敗，不上線錯誤資料
