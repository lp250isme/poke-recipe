# 鐵則（Iron Rules）— Poke 整合開發

> 本 repo 任何 Poke MCP / 整合相關工作，**一律嚴格參考官方文件，不得憑記憶或臆測**；與官方衝突時以官方為準。
> - **MCP Servers（本鐵則主依據）**：https://poke.com/docs/mcp-servers
> - Creating Recipes：https://poke.com/docs/creating-recipes
> - Managing Integrations：https://poke.com/docs/managing-integrations

## MCP Server 硬性規則（摘自 poke.com/docs/mcp-servers，以官方為準）

1. **連線方式**
   - Web：`poke.com/integrations/new` → 填 Name + MCP Server URL（+ 選填 API Key）→ Create Integration
   - CLI remote：`npx poke@latest mcp add <https-url> -n "Name" [-k <api-key>]`
   - CLI local（tunnel）：`npx poke@latest tunnel http://localhost:PORT/mcp -n "Name" [--client-id .. --client-secret ..]`
2. **傳輸**：遠端 MCP 須為 HTTPS 端點（SSE / HTTP）。本機僅能靠 tunnel，且 tunnel 只轉發 port、不代管 server，機器關了就斷 → **不適合對外散播的 recipe**。
3. **認證**：API Key（連線時帶入）；或 OAuth（DCR 自動；否則用 `--client-id` / `--client-secret`，或 hosted server 的 Kitchen template）。設定後每次請求帶 `Authorization: Bearer {access_token}`。
4. **Poke 送給 server 的 Header（每次請求）**
   - `Authorization: Bearer {access_token}`（若有設定認證）
   - `X-Poke-User-Id: {UUID}` — Poke 使用者唯一識別，用於 per-user 限流 / 資料隔離 / 稽核
5. **Server 實作**：須符合 MCP 規範；對外 expose **tools**（name + description + input schema）。首次連線/重新認證時自動同步 tools；整合頁可手動 re-sync。
6. **SDK**：MCP TypeScript SDK 或 MCP Python SDK。

## 套用到本專案
- 若把 World Cup recipe 改為「Poke 透過自建 MCP 取賽程／查詢」，該 MCP server **必須符合上述全部**，且需**常駐 HTTPS 主機**（GitHub Pages 靜態站無法當 MCP 端點；候選：Cloudflare Workers / Vercel / VPS）。
- 寫日曆事件仍走 Poke 的原生日曆整合（Google / Outlook）；MCP 負責的是「資料/工具」而非代寫他人日曆。
- 任何 recipe 的 `inputContext` 引用的端點、指令、欄位，須與官方 doc 對得上，對不上就標「待確認」、不杜撰。
