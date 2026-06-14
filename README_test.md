# openclaw-skills

> 豪的 OpenClaw Skills 備份倉庫

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skills-blue)](https://github.com/openclawchen8-lgtm/openclaw-skills)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

<!-- TOC -->
- [原創技能](#原創技能--original-skills)
- [第三方技能](#第三方技能--third-party-skills)

---

## 目錄結構 | Directory Structure

```
openclaw-skills/
├── agent-browser-clawdbot-local  # 第三方：Headless browser automation CLI optimize
├── clw-github                    # 原創：Interact with GitHub using the `gh` CLI.
├── clw-gold-monitor              # 🥇 原創：台灣銀行黃金存摺價格監控系統。支援買/賣雙價格、價格變動通知、特定價格點位監控與
├── clw-gold-monitor-pro          # 🥇 原創：多金屬價格監控系統 v3。台銀黃金存摺 + 國際金屬現貨（黃金/白銀/鉑金），快
├── clw-ideas2tasks               # 📋 原創：將臨時想法自動分類、拆解為敏捷專案任務。 觸發條件：用戶提到「idea轉task
├── clw-kgi-monitor               # 🎬 原創：凱基股股漲 YouTube 頻道 AI 供應鏈影片監控。 抓取頻道影片，過濾 A
├── clw-md-to-pdf                 # 📄 原創：將 Markdown 檔案轉成 PDF，不需要安裝任何工具（只要有 Chrome
├── clw-sinotrade-scraper         # 📊 原創：永豐投顧台股報告自動抓取系統，每日 08:30 推送新增報告至 Telegram
├── clw-summarize                 # 原創：摘要任意 URL、本地檔案（PDF/圖片/音訊）或 YouTube 影片，支援多
├── clw-twse-monitor              # 原創：台股即時監控與推播通知（v2）。當用戶提及台股監控、股價通知、漲停跌停、董監事持
├── clw-voice-reply               # 🎙️ 原創：語音雙模回覆技能。使用 Edge TTS (免費) 生成語音回覆，使用 Whis
├── clw-whisper                   # 原創：本地語音轉文字，使用 OpenAI Whisper CLI，免 API Key，
├── fbs_bookwriter                # 第三方：FBS 福帮手长文档写作：书/手册/白皮书/长篇报道全流程；Node 脚本驱动 
├── github-issues                 # 原創：GitHub Issue 管理工具。支援 Draft Items → Issue
├── github-projects               # 原創：GitHub Projects (Board) 原生 GraphQL API 管
├── github-skill                  # 第三方：在用户提及 GitHub 仓库、Issue、Pull Request、Actio
├── openclaw-backup               # 第三方：Backup and restore OpenClaw data. Use wh
├── persona-switch                # 第三方：切换 agent 的人设（soul.md）。支持三套预设人设与原有人设之间自由切
├── prompt-injection-filter       # 🔒 原創：純 Python 正則 Prompt 注入過濾器，檢測 ignore previ
├── scrum-task-tracker            # 📋 原創：Scrum 專案管理與任務追蹤標準流程。確保所有專案遵循統一的任務拆分、執行、驗
├── self-improving                # 第三方：Self-reflection + Self-criticism + Self-
├── self-improving-agent          # 第三方：Captures learnings, errors, and correcti
├── workflow-automator            # 第三方：重复操作一键自动化。重复操作太浪费时间？用自然语言构建自动化工作流 This s
```

---

## 原創技能 | Original Skills

| Skill | 名稱 | 說明 |
|-------|------|------|
| `github` | Github | Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and  |
| 🥇 `clw-gold-monitor` | Clw Gold Monitor | 台灣銀行黃金存摺價格監控系統。支援買/賣雙價格、價格變動通知、特定價格點位監控與每日收盤報告。state 檔已廢除，歷史收盤記錄為唯一比較基準。 |
| 🥇 `clw-gold-monitor-pro` | Clw Gold Monitor Pro | 多金屬價格監控系統 v3。台銀黃金存摺 + 國際金屬現貨（黃金/白銀/鉑金），快取比對 + 交叉驗證，Telegram 告警。 |
| 📋 `ideas2tasks` | Ideas2Tasks | 將臨時想法自動分類、拆解為敏捷專案任務。 觸發條件：用戶提到「idea轉task」「ideas2tasks」「想法拆分」「專案規劃」「task管理」, 或要求掃 |
| 🎬 `clw-kgi-monitor` | Clw Kgi Monitor | 凱基股股漲 YouTube 頻道 AI 供應鏈影片監控。 抓取頻道影片，過濾 AI 供應鏈關鍵詞，符合條件即時推 Telegram。 觸發條件：用戶提到「凱基」 |
| 📄 `clw-md-to-pdf` | Clw Md To Pdf | 將 Markdown 檔案轉成 PDF，不需要安裝任何工具（只要有 Chrome 就夠）。使用 pandoc 轉 HTML 後用 Chrome headless |
| 📊 `sinotrade-scraper` | Sinotrade Scraper | 永豐投顧台股報告自動抓取系統，每日 08:30 推送新增報告至 Telegram。 |
| `clw-summarize` | Clw Summarize | 摘要任意 URL、本地檔案（PDF/圖片/音訊）或 YouTube 影片，支援多種 AI 模型。 |
| `clw-twse-monitor` | Clw Twse Monitor | 台股即時監控與推播通知（v2）。當用戶提及台股監控、股價通知、漲停跌停、董監事持股、月營收、注意股票、處置股票、ESG、大盤指數、除權除息、殖利率、持股成本、未 |
| 🎙️ `voice-reply` | Voice Reply | 語音雙模回覆技能。使用 Edge TTS (免費) 生成語音回覆，使用 Whisper 轉錄語音輸入。 |
| `clw-whisper` | Clw Whisper | 本地語音轉文字，使用 OpenAI Whisper CLI，免 API Key，支援多種模型大小。 |
| `clw-github-issues` | Clw Github Issues | GitHub Issue 管理工具。支援 Draft Items → Issues Migration、Issue 批量建立、Board 加入/去重、Body  |
| `clw-github-projects` | Clw Github Projects | GitHub Projects (Board) 原生 GraphQL API 管理工具。紀錄 Draft Item Migration 失敗經驗與已知問題。⚠️ |
| 🔒 `prompt-injection-filter` | Prompt Injection Filter | 純 Python 正則 Prompt 注入過濾器，檢測 ignore previous、role play、jailbreak 等攻擊模式。 |
| 📋 `scrum-task-tracker` | Scrum Task Tracker | Scrum 專案管理與任務追蹤標準流程。確保所有專案遵循統一的任務拆分、執行、驗證和報告規範。 |

---

## 第三方技能 | Third-Party Skills

| Skill | 名稱 | 說明 |
|-------|------|------|
| `agent-browser` | Agent Browser | Headless browser automation CLI optimized for AI agents with accessibility tree  |
| `fbs_bookwriter` | Fbs_Bookwriter | FBS 福帮手长文档写作：书/手册/白皮书/长篇报道全流程；Node 脚本驱动 intake、会话恢复、S/P/C/B 质检与 MD/HTML 交付。用户提及写 |
| `github` | Github | 在用户提及 GitHub 仓库、Issue、Pull Request、Actions、代码管理相关内容与操作时使用此技能。触发关键词包括：创建 issue、新建 |
| `openclaw-backup` | Openclaw Backup | Backup and restore OpenClaw data. Use when user asks to create backups, set up a |
| `persona-switch` | Persona Switch | 切换 agent 的人设（soul.md）。支持三套预设人设与原有人设之间自由切换。 触发词：切换人设、persona-switch、赛博朋友、温柔伴侣、创始人 |
| `Self-Improving + Proactive Agent` | Self Improving + Proactive Agent | Self-reflection + Self-criticism + Self-learning + Self-organizing memory. Agent |
| `self-improvement` | Self Improvement | Captures learnings, errors, and corrections to enable continuous improvement. Us |
| `workflow-automator` | Workflow Automator | 重复操作一键自动化。重复操作太浪费时间？用自然语言构建自动化工作流 This skill should be used when the user asks a |

---

## 安裝方式 | Installation

每個 Skill 都有獨立的 SKILL.md 說明文件。

```bash
# ClawHub
skillhub install <skill-name>

# OpenClaw CLI
openclaw skills install <skill-name>
```

---

*最後更新：2026-05-11*
