#!/usr/bin/env python3
# World Cup 2026 產生器（GitHub Actions 定時重跑，淘汰賽占位隨來源更新成真隊）
# 來源: openfootball/worldcup.json (public domain, 免 key)
# 輸出: public/worldcup2026.ics（訂閱用）+ public/worldcup2026.json（Poke 直接寫日曆用，已預處理）
#       + public/index.html
# 重點: 時間一律 UTC；隊名用 team-map.json（不靠即興翻譯）。Poke 端只建事件、不重算。

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
    except Exception as e:
        sys.stderr.write(f"[warn] fetch failed ({e}); fallback /tmp/wc_master.json\n")
        return json.load(open("/tmp/wc_master.json", encoding="utf-8"))

def resolve_team(name):
    """回傳 (emoji, zh, is_real)。占位碼解讀成易懂中文（emoji 留空）。"""
    n = ALIASES.get(name, name)
    if n in TEAMS:
        t = TEAMS[n]
        return t["emoji"], t["zh"], True
    if re.fullmatch(r"[1-9][A-L]", name):
        return "", f"{name[1]}組第{name[0]}", False
    if re.fullmatch(r"3[A-L/]+", name):
        return "", f"第三名({name[1:]} 組之一)", False
    if re.fullmatch(r"W\d+", name):
        return "", f"第{name[1:]}場勝者", False
    if re.fullmatch(r"L\d+", name):
        return "", f"第{name[1:]}場敗者", False
    return "", f"{name}(待確認)", False

def disp(emoji, zh):
    return (emoji + " " + zh).strip()

def to_utc(date_str, time_str):
    hm, tz = time_str.split()
    off = int(tz.replace("UTC", ""))
    local = datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M")
    return local - timedelta(hours=off)

def uid(m):
    if "num" in m:
        return f"wc2026-m{m['num']}"
    rnd = m.get("round", "")
    if rnd == "Final":
        return "wc2026-final"
    if rnd == "Match for third place":
        return "wc2026-third"
    s = lambda x: re.sub(r"[^A-Za-z0-9]", "", x)
    return f"wc2026-{m['date']}-{s(m['team1'])}-{s(m['team2'])}"

def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

INDEX_TMPL = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 世界盃賽程（繁中）</title>
<style>body{font-family:-apple-system,system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;max-width:42rem;margin:3rem auto;padding:0 1.2rem;line-height:1.7;color:#1a1a1a}a.btn{display:inline-block;background:#0a7a55;color:#fff;padding:.7rem 1.2rem;border-radius:.6rem;text-decoration:none;font-weight:600}code{background:#f2f2f2;padding:.15rem .4rem;border-radius:.3rem;word-break:break-all}.muted{color:#666;font-size:.9rem}</style>
</head><body>
<h1>⚽ 2026 世界盃賽程（繁中）</h1>
<p>__N__ 場：在地時區、繁中隊名 + 國旗、淘汰賽自動填空。</p>
<p><a class="btn" id="sub" href="#">＋ 訂閱到行事曆</a></p>
<p class="muted">直接訂閱網址（Google：設定 → 新增日曆 → 透過網址）：<br><code id="url"></code></p>
<p class="muted">給程式用的 JSON：<code id="jurl"></code>｜資料：openfootball｜更新 __NOW__</p>
<script>
var dir=location.pathname.replace(/[^/]*$/,'');
document.getElementById('url').textContent=location.origin+dir+'worldcup2026.ics';
document.getElementById('jurl').textContent=location.origin+dir+'worldcup2026.json';
document.getElementById('sub').href='webcal://'+location.host+dir+'worldcup2026.ics';
</script>
</body></html>"""

def build():
    data = load_data()
    matches = data["matches"]
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//kv//WorldCup2026//TW",
           "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:2026 世界盃 (繁中)",
           "X-WR-TIMEZONE:UTC"]
    records, unresolved = [], []
    for m in matches:
        e1, z1, ok1 = resolve_team(m["team1"])
        e2, z2, ok2 = resolve_team(m["team2"])
        rnd = m.get("round", "")
        grp = ""
        if rnd.startswith("Matchday"):
            grp = (m.get("group", "") or "").replace("Group ", "") + "組"
            summary = f"{disp(e1,z1)} vs {disp(e2,z2)}（{grp}）"
            for raw, ok in ((m["team1"], ok1), (m["team2"], ok2)):
                if not ok:
                    unresolved.append(raw)
        else:
            summary = f"🏆 {ROUND_ZH.get(rnd, rnd)}：{disp(e1,z1)} vs {disp(e2,z2)}"
        start = to_utc(m["date"], m["time"])
        end = start + timedelta(hours=2)
        u = uid(m)
        ics += ["BEGIN:VEVENT", f"UID:{u}@worldcup", f"DTSTAMP:{now}",
                f"DTSTART:{start:%Y%m%dT%H%M%S}Z", f"DTEND:{end:%Y%m%dT%H%M%S}Z",
                f"SUMMARY:{esc(summary)}", f"LOCATION:{esc(m.get('ground',''))}",
                f"DESCRIPTION:{esc(rnd + '｜uid:' + u)}", "END:VEVENT"]
        records.append({
            "uid": u, "round": ROUND_ZH.get(rnd, rnd), "group": grp,
            "start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_utc": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": summary, "location": m.get("ground", ""),
            "teams_zh": [z1, z2], "placeholder": not (ok1 and ok2),
        })
    ics.append("END:VCALENDAR")
    pub = os.path.join(HERE, "public")
    os.makedirs(pub, exist_ok=True)
    open(os.path.join(pub, "worldcup2026.ics"), "w", encoding="utf-8").write("\r\n".join(ics) + "\r\n")
    json.dump({"updated_utc": now_iso, "count": len(records), "matches": records},
              open(os.path.join(pub, "worldcup2026.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(
        INDEX_TMPL.replace("__N__", str(len(matches))).replace("__NOW__", now))
    return matches, records, unresolved

if __name__ == "__main__":
    matches, records, unresolved = build()
    print(f"matches={len(matches)} records={len(records)} -> public/{{ics,json,index.html}}")
    print(f"小組賽未對到隊名(應為空): {sorted(set(unresolved))}")
    if unresolved:
        sys.exit(1)
