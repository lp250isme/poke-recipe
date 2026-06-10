#!/usr/bin/env python3
# World Cup 2026 產生器（GitHub Actions 定時重跑，淘汰賽占位隨來源更新成真隊）
# 來源: openfootball/worldcup.json (public domain, 免 key)
# 輸出(public/): worldcup2026.json（雙語, Poke 直寫日曆用）
#               worldcup2026.ics（繁中訂閱）, worldcup2026.en.ics（English 訂閱）, index.html
# 重點: 時間一律 UTC；隊名用 team-map.json（不靠即興翻譯）；中英雙語並行。

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
    """回傳 (emoji, zh, en, is_real)。占位碼解讀成中/英易懂字串。"""
    n = ALIASES.get(name, name)
    if n in TEAMS:
        return TEAMS[n]["emoji"], TEAMS[n]["zh"], name, True   # en 用來源原文（自然英文）
    if re.fullmatch(r"[1-9][A-L]", name):                       # 2A = A組第2 / A2
        return "", f"{name[1]}組第{name[0]}", f"{name[1]}{name[0]}", False
    if re.fullmatch(r"3[A-L/]+", name):
        return "", f"第三名({name[1:]} 組之一)", f"3rd({name[1:]})", False
    if re.fullmatch(r"W\d+", name):
        return "", f"第{name[1:]}場勝者", f"Winner M{name[1:]}", False
    if re.fullmatch(r"L\d+", name):
        return "", f"第{name[1:]}場敗者", f"Loser M{name[1:]}", False
    return "", f"{name}(待確認)", name, False

def disp(emoji, label):
    return (emoji + " " + label).strip()

def to_utc(date_str, time_str):
    hm, tz = time_str.split()
    off = int(tz.replace("UTC", ""))
    return datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M") - timedelta(hours=off)

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

def ics_doc(records, calname, key):
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//kv//WorldCup2026//TW",
           "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{calname}", "X-WR-TIMEZONE:UTC"]
    for r in records:
        out += ["BEGIN:VEVENT", f"UID:{r['uid']}@worldcup", f"DTSTAMP:{r['_now']}",
                f"DTSTART:{r['_start']}", f"DTEND:{r['_end']}",
                f"SUMMARY:{esc(r[key])}", f"LOCATION:{esc(r['location'])}",
                f"DESCRIPTION:{esc(r['round'] + '｜uid:' + r['uid'])}", "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"

INDEX_TMPL = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 世界盃賽程 World Cup 2026</title>
<style>body{font-family:-apple-system,system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;max-width:42rem;margin:3rem auto;padding:0 1.2rem;line-height:1.7;color:#1a1a1a}a.btn{display:inline-block;background:#0a7a55;color:#fff;padding:.6rem 1rem;border-radius:.6rem;text-decoration:none;font-weight:600;margin:.2rem .4rem .2rem 0}code{background:#f2f2f2;padding:.15rem .4rem;border-radius:.3rem;word-break:break-all}.muted{color:#666;font-size:.9rem}</style>
</head><body>
<h1>⚽ 2026 世界盃賽程 · World Cup 2026</h1>
<p>__N__ 場：在地時區、隊名+國旗、淘汰賽自動填空。Local timezone, flag emojis, knockout auto-fills.</p>
<p><a class="btn" id="zh" href="#">＋ 繁中行事曆</a><a class="btn" id="en" href="#">＋ English calendar</a></p>
<p class="muted">Google：設定→新增日曆→透過網址。中文：<code id="zurl"></code><br>English: <code id="eurl"></code></p>
<p class="muted">JSON (bilingual): <code id="jurl"></code>｜openfootball｜__NOW__</p>
<script>
var dir=location.pathname.replace(/[^/]*$/,''),o=location.origin,h=location.host;
zurl.textContent=o+dir+'worldcup2026.ics'; eurl.textContent=o+dir+'worldcup2026.en.ics';
jurl.textContent=o+dir+'worldcup2026.json';
zh.href='webcal://'+h+dir+'worldcup2026.ics'; en.href='webcal://'+h+dir+'worldcup2026.en.ics';
</script>
</body></html>"""

def build():
    matches = load_data()["matches"]
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records, unresolved = [], []
    for m in matches:
        e1, z1, en1, ok1 = resolve_team(m["team1"])
        e2, z2, en2, ok2 = resolve_team(m["team2"])
        rnd = m.get("round", "")
        start = to_utc(m["date"], m["time"]); end = start + timedelta(hours=2)
        if rnd.startswith("Matchday"):
            gl = (m.get("group", "") or "").replace("Group ", "")
            summary_zh = f"{disp(e1,z1)} vs {disp(e2,z2)}（{gl}組）"
            summary_en = f"{disp(e1,en1)} vs {disp(e2,en2)} (Group {gl})"
            for raw, ok in ((m["team1"], ok1), (m["team2"], ok2)):
                if not ok:
                    unresolved.append(raw)
        else:
            summary_zh = f"🏆 {ROUND_ZH.get(rnd, rnd)}：{disp(e1,z1)} vs {disp(e2,z2)}"
            summary_en = f"🏆 {rnd}: {disp(e1,en1)} vs {disp(e2,en2)}"
        records.append({
            "uid": uid(m), "round": ROUND_ZH.get(rnd, rnd), "round_en": rnd,
            "group": ((m.get("group") or "").replace("Group ", "") + "組") if rnd.startswith("Matchday") else "",
            "start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "end_utc": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary_zh": summary_zh, "summary_en": summary_en,
            "teams_zh": [z1, z2], "teams_en": [en1, en2],
            "location": m.get("ground", ""), "placeholder": not (ok1 and ok2),
            "_now": now, "_start": f"{start:%Y%m%dT%H%M%S}Z", "_end": f"{end:%Y%m%dT%H%M%S}Z",
        })
    pub = os.path.join(HERE, "public"); os.makedirs(pub, exist_ok=True)
    open(os.path.join(pub, "worldcup2026.ics"), "w", encoding="utf-8").write(ics_doc(records, "2026 世界盃 (繁中)", "summary_zh"))
    open(os.path.join(pub, "worldcup2026.en.ics"), "w", encoding="utf-8").write(ics_doc(records, "World Cup 2026 (EN)", "summary_en"))
    public_recs = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    json.dump({"updated_utc": now_iso, "count": len(public_recs), "matches": public_recs},
              open(os.path.join(pub, "worldcup2026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(
        INDEX_TMPL.replace("__N__", str(len(matches))).replace("__NOW__", now))
    return matches, records, unresolved

if __name__ == "__main__":
    matches, records, unresolved = build()
    print(f"matches={len(matches)} records={len(records)} -> json + zh.ics + en.ics + index.html")
    print(f"小組賽未對到隊名(應為空): {sorted(set(unresolved))}")
    if unresolved:
        sys.exit(1)
