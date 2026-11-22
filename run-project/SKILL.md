---
name: run-project
description: 執行指定專案的所有未完成任務。當使用者說「執行 <專案名> 專案」、「繼續 <專案名> 的任務」或要求持續完成任務書時使用。掃描 ~/tasks/<專案名>/tasks/ 的未完成任務，逐一實作、每個任務 commit 一次，全部完成後以語音通知。
---

# Run Project（執行專案任務）

## 路徑慣例

- 專案程式碼：`~/Projects/<專案名>/`
- 專案任務書：`~/tasks/<專案名>/tasks/T*.md`

## 流程

### 1. 找出未完成任務
掃描 `~/tasks/<專案名>/tasks/*.md` 的 frontmatter：
- 未完成：`status: pending` 或 `status: in-progress`
- 跳過：`status: done` 及其他狀態
- 排序：priority（high → medium → low）→ 任務編號遞增
- 注意 `depends_on`：依賴尚未 done 的任務先跳過

### 2. 逐任務執行（一次一個，請勿使用subagent執行。）
1. `read` 任務書全文，理解「目標」與「驗收標準」
2. 在 `~/Projects/<專案名>/` 實作，跑測試直到驗收標準全數滿足
3. commit（在 code path）：
   ```bash
   git add -A && git commit -m "T0XX: <任務標題>"
   ```
4. 更新任務書 frontmatter：`status: done`、`updated: <今天日期>`
5. 簡短回報該任務成果，接著下一個任務

### 3. 收尾
所有任務完成後，呼叫 tasks-finish-notify 發 Telegram

並用 bash 執行：
```bash
say "任務都完成了"
```

## 異常通報（語音通知）
遇到以下狀況時，除了處理，必須先用 呼叫 tasks-finish-notify 發 Telegram 及 bash 語音 告知使用者：

1. **檔案權限受阻**（如讀寫出現 `Operation not permitted`、無法存取 `~/tasks/`）：
   ```bash
   say "目前需要終端機授權"
   ```
   然後停止執行，等使用者授權「完整磁碟存取」後再繼續。

2. **Provider 連續失敗／長跑斷線**（如連續多次 `Provider finish_reason: network_error`、API 逾時、context 超限）：
   ```bash
   say "session長跑中斷線"
   ```
   然後把目前任務的進度註記在任務書（保持 in-progress），方便 `/resume` 或 fork 後接續。

## 紀律
- 一個任務一個 commit，不混雜
- 任務書的驗收標準是唯一完成依據，不得自行放水
- 中途遇到無法解決的阻塞：將該任務註記原因留在 in-progress，跳下一個，最後彙報
