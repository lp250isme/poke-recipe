# Poke Recipes

我的 Poke recipe 集合（monorepo）。每個 recipe 一個子資料夾；GitHub Actions 把各自輸出彙整到 GitHub Pages，每個 recipe 走一個子路徑，用來提供可訂閱的 .ics / 靜態頁。

## 結構

| 路徑 | 說明 |
|------|------|
| `build_all.py` | 跑每個 recipe 的產生器 → 彙整到 `dist/<recipe>/` + 首頁列表 |
| `.github/workflows/build-ics.yml` | 每 6h 重建 + 部署 Pages |
| `world-cup-2026/` | 2026 世界盃賽程訂閱（見子資料夾 README） |

## 部署（一次性）

```bash
cd ~/projects/poke-recipe
git init -b main && git add . && git commit -m "feat: poke recipes monorepo"
gh repo create poke-recipe --public --source=. --push
```
然後 repo → Settings → Pages → Source 選「GitHub Actions」。

- 首頁：`https://<你的GH帳號>.github.io/poke-recipe/`
- 各 recipe：`https://<你的GH帳號>.github.io/poke-recipe/<recipe>/`

## 新增一個 recipe

1. 建資料夾 `your-recipe/`，放一支產生器，把產出寫到 `your-recipe/public/`。
2. 在 `build_all.py` 的 `RECIPES` 註冊 `{dir, entry, title}`。
3. push → Actions 自動建置 + 部署到 `…/poke-recipe/your-recipe/`。

## 本機測試

```bash
python3 build_all.py   # 產出 dist/；各 recipe 產生器有自檢，失敗會 exit 1
```
