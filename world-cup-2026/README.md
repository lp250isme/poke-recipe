# World Cup 2026 賽程日曆（繁中）

自動更新的 2026 世界盃 .ics 訂閱：你的在地時區、繁中隊名 + 國旗 emoji，淘汰賽底定後自動填空。
資料來源 [openfootball](https://github.com/openfootball/worldcup.json)（public domain，免 key）。建置與部署見上層 [README](../README.md)。

## 檔案

| 檔案 | 用途 |
|------|------|
| `gen_wc_ics.py` | 爬取 + 轉換 → `public/worldcup2026.ics` + `public/index.html` |
| `team-map.json` | 隊名英→繁中 + 國旗 emoji（對 live 48 隊核對，0 漏） |
| `recipe.md` | Poke recipe 內容（訂閱引導 + 賽前提醒 + 問答） |

## 訂閱（部署後）

網址：`https://<你的GH帳號>.github.io/poke-recipe/world-cup-2026/worldcup2026.ics`

- **Apple（iPhone/Mac）**：開訂閱頁 `…/poke-recipe/world-cup-2026/` 點「加入 Apple 行事曆」。
- **Google 行事曆**：設定 → 新增日曆 → 透過網址 → 貼上 .ics 網址。
- **Outlook**：新增行事曆 → 從網際網路訂閱 → 貼上 .ics 網址。

訂一次即可，feed 在伺服器端更新，日曆自動同步。

## 本機測試

```bash
python3 gen_wc_ics.py   # 產出 public/；末行「未對到隊名」清單應為空，否則 exit 1
```
