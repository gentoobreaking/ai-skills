---
name: write-readme
description: 為 Git repository 產生產品級 README.md。透過「讀規格書＋讀原始碼→規格與實作比對→分階段輸出」的流程，確保 README 內容全部有證據、無幻覺。適用於使用者要求「寫 README」「更新 README」「文件化這個專案」，或 README 與實作明顯脫節時。
---

# Write-README：證據導向的 README 產生器

> 核心原則：**README 是放進 production repository 的正式文件，不是 AI 示範文章。**
> 如果「完整」與「正確」衝突，優先選擇正確；資訊不足就標記不足，不自行填空。

## 輸入

| 項目 | 預設路徑 | 說明 |
|---|---|---|
| 專案根目錄 | `~/Projects/<專案名>/`（或使用者指定） | 含 source code |
| 產品規格書 | `~/tasks/<專案>/spec.md` ＋ `algs/*.md`（若存在） | 可能不存在——不存在時跳過規格分析並聲明 |
| 任務書（佐證） | `~/tasks/<專案>/tasks/*.md` 的執行紀錄/勾選狀態 | 可輔助判斷哪些功能真的完成了 |
| 既有 README | 專案根目錄 `README.md`（若存在） | 僅供比對差異，不直接沿用 |

角色設定：以 **Technical Writer × Software Architect × Product Engineer × DX Engineer**
的四重視角工作。

## 流程（五階段，順序不可顛倒）

### Phase 1 — Product Understanding（先理解，再動筆）

完整閱讀規格書與 source code 後整理：

- 產品做什麼／解決什麼問題／主要使用者／核心情境
- 核心功能、系統邊界、主要輸入輸出、外部依賴
- 技術架構、主要模組、資料流、主要執行流程

規格分析提取：Product Goal / Functional & Non-functional Requirements /
User Stories / Business Rules / API・Config・Deployment・Security・Error handling
requirements / Known limitations。
**不得自行補充規格書沒有的產品行為。**

程式碼分析確認：Entry points、啟動流程、核心模組、API endpoints、CLI commands、
config、環境變數、儲存、外部服務、auth、error handling、logging、背景作業、
tests、build、deployment。

### Phase 2 — Architecture Understanding

從 source code 推導實際架構。涉及「目前實際行為」的內容**一律以 source code 為準**。
Mermaid diagram 只能根據實際 code 推導，不可虛構。

### Phase 3 — Spec vs Implementation 比對

建立五類分類表輸出：

```markdown
| Area | Specification | Implementation | Status |
```

Status 取值：Confirmed / Implemented / Partial / Missing / Inconsistent /
Needs Verification

若 source code 與正式規格明顯不一致：**不要偷偷選邊**，
明確指出 "Documentation and implementation are currently inconsistent" 並說明具體差異。

### Phase 4 — README Information Gaps

列出目前無法可靠完成的資訊（如缺部署文件、未知認證流程、缺 production config）。
這些在 README 中標記 `[NEEDS VERIFICATION]`，不自行填空。

### Phase 5 — Final README

只放經過前四階段確認的內容，依下方結構與風格撰寫。

## 資訊來源優先順序（衝突時）

1. 實際 source code
2. 自動化測試
3. 設定檔與 deployment configuration
4. API schema / interface definition
5. 最新版規格文件
6. 舊規格文件
7. AI 自己推測

## README 結構（依實際情況取捨，非每份都要全）

Product Name → Overview → Features → Architecture → Project Structure →
How It Works → Requirements → Installation → Configuration → Quick Start →
Usage → API → Data Model → Error Handling → Logging and Observability →
Testing → Build → Deployment → Security → Troubleshooting → Limitations →
Development Guide → Contributing → License → Documentation

各節要點：

- **Features**：只列實際存在的功能；未實作的寫進 Limitations，不包裝成特色
- **Configuration**：env vars 用 code formatting、含預設值與範例值；
  secrets 一律 `<your-api-key>` 形式，禁止真實憑證
- **Quick Start**：最短可實際執行的 happy path——讀者照做必須能跑起來
- **Testing**：實際測試指令與類型；Coverage 只有能從實際數據確認時才寫
- **Deployment**：資訊不足就不猜測
- **Security**：只描述實際存在的機制；不宣稱「安全」或符合某標準除非有證據
- **Limitations**：誠實列出已知限制與不支援項

## 寫作風格

- 清楚專業的自然語言、優先短句
- 避免 buzzwords（powerful/seamless/robust）與 marketing language
- 技術名詞保留英文；重要縮寫首次出現給全名
- Markdown headings、適度 tables、command 用 code block
- 可快速掃讀；一個段落不塞過多資訊

## 反幻覺清單（禁止虛構）

API、command、environment variable、deployment 方法、database、authentication、
測試結果、performance numbers、產品功能、external service、architecture——
**任何無法從提供的資料確認的項目，標記 `[NEEDS VERIFICATION]`**。

## 完稿自審

輸出前自查：

- [ ] 新 developer 能只看 README 理解產品？
- [ ] 能依照 README 啟動專案？
- [ ] 所有 command / env vars / API 都真實存在？
- [ ] 與 source code 一致？
- [ ] 沒把 planned feature 寫成 implemented？
- [ ] 沒有無證據的推測？
- [ ] 無重複冗餘？無重要缺失？無誤導描述？
- [ ] 符合實際 repository 結構？

## 輸出格式

按 Phase 1–5 順序輸出（理解摘要 → 架構 → 差異表 → 缺口清單 → 最終 README）。
最終 README 寫入專案根目錄 `README.md`（既有檔案先備份或經使用者同意覆蓋）。
並產生一份繁體中文版本寫入專案根目錄 `README.zh-TW.md`
並產生一份簡體中文版本寫入專案根目錄 `README.zh-CN.md`

## 授權
授權一律使用 本專案採 **Apache License 2.0** 授權。詳見 [`LICENSE`](LICENSE)。
