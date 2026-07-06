# COROS Chatbox

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-f97316?logo=python&style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&style=flat-square)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4-4fc08d?logo=vuedotjs&style=flat-square)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Vite-5-646cff?logo=vite&style=flat-square)](https://vitejs.dev)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.5-ff6384?logo=chartdotjs&style=flat-square)](https://www.chartjs.org)
[![License](https://img.shields.io/badge/License-MIT-3da639?style=flat-square)](LICENSE)

</div>

## 项目简介

COROS Chatbox 是一個全端應用程式，連接 COROS 運動手錶的訓練中心 API，自動獲取你的跑步、健康、睡眠、HRV 和訓練負荷數據，並透過 AI 聊天介面讓你用自然語言查詢和分析。

- **目標用戶**：COROS 手錶用家、跑步愛好者、想用數據化方式追蹤訓練進度的運動員
- **技術棧**：Python FastAPI 後端 + Vue 3 前端 + DeepSeek API (LLM) + Chart.js / Mermaid 圖表

## 功能特性

- 🔄 **COROS 數據同步** — 自動獲取跑步記錄、健康數據、睡眠、HRV、恢復狀態、訓練負荷、體能評估，支援智能 token 快取避免重複登入
- 📊 **每公里分段配速** — 為每項跑步活動自動提取公里分段，包含配速、心率、步頻、海拔和功率
- 💬 **AI 聊天介面** — 用自然語言查詢你的訓練數據，支援多輪對話、URL 抓取分析
- 📁 **GPX / TCX / FIT 上傳分析** — 上傳活動檔案，自動解析距離、海拔、心率、步頻並生成圖表
- 📈 **三層圖表系統**
  - 上傳檔案圖表：海拔、心率、步頻的 Chart.js 折線圖
  - 摘要儀表板：月跑量柱狀圖、心率趨勢線、訓練負荷雙線圖
  - Mermaid 圖表：AI 回覆中內嵌 xychart-beta 互動圖表
- 🎯 **教練模式** — 毒舌但精準的「刻薄體育教練」人格，表現差時會嘲諷你，但分析從不出錯
- 🧠 **模式自動切換** — 系統自動判斷查詢是「單純取數」還是「深度分析」，路由到對應的 LLM 模型
- 📄 **匯出報表** — 選取聊天記錄中的訊息，匯出為 HTML 或 PDF（支援深色/淺色/橙色主題）
- 🌏 **預設繁體中文** — LLM 提示詞強制使用繁體中文回覆

## 快速開始

### 環境要求

- Python 3.12+
- Node.js 18+
- COROS 手錶帳號（電郵、密碼、地區）
- DeepSeek API 金鑰（或任何 OpenAI 兼容端點）

### 安裝步驟

```bash
# 1. 安裝後端依賴
pip install -r coros-chatbox/backend/requirements.txt

# 2. 安裝前端依賴
cd coros-chatbox/frontend
npm install
cd ../..

# 3. 設定環境變數（見下方配置說明）
# 編輯 .env 檔案
```

### 執行

```bash
# 方式一：一鍵啟動 (Windows)
cd coros-chatbox
start.bat

# 方式二：分別啟動
# 終端機 1：後端 (http://localhost:8000)
cd coros-chatbox/backend
python main.py

# 終端機 2：前端 (http://localhost:5175)
cd coros-chatbox/frontend
npm run dev
```

打開瀏覽器前往 **http://localhost:5175**。

### 刷新數據

```bash
python refresh_data.py
```

或在聊天介面按 **「Refresh COROS」** 按鈕。

## 配置說明

在專案根目錄建立 `.env` 檔案：

```env
# COROS 帳號（必填）
COROS_EMAIL=your.email@example.com
COROS_PASSWORD=your_password
COROS_REGION=asia

# LLM API（必填）
DEEPSEEK_API_KEY=sk-your-key-here
```

| 變數 | 必填 | 說明 | 預設值 |
|------|------|------|--------|
| `COROS_EMAIL` | ✅ | COROS 帳號電郵 | — |
| `COROS_PASSWORD` | ✅ | COROS 帳號密碼 | — |
| `COROS_REGION` | ✅ | 伺服器地區：`us` / `asia` / `eu` | `us` |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API 金鑰（或其他 OpenAI 兼容端點） | — |
| `DEEPSEEK_BASE_URL` | ❌ | 自訂 LLM API 地址 | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | ❌ | 自訂模型名稱（data 模式） | `deepseek-v4-flash` |
| `DEEPSEEK_MODEL_PRO` | ❌ | 自訂模型名稱（coach 模式） | `deepseek-v4-pro` |

## API 文件

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/api/health` | 健康檢查，回傳可用數據檔案列表 |
| `POST` | `/api/refresh` | 執行 `refresh_data.py` 刷新 COROS 數據 |
| `POST` | `/api/upload` | 上傳 GPX/TCX/FIT/圖片檔案 |
| `GET` | `/api/uploads/{file_id}` | 取得上傳檔案資訊或圖片 |
| `GET` | `/api/chart/gpx/{file_id}` | 計算 GPX 時間序列數據（海拔、心率、步頻、配速） |
| `GET` | `/api/chart/tcx/{file_id}` | 計算 TCX 時間序列數據 |
| `GET` | `/api/chart/fit/{file_id}` | 計算 FIT 時間序列數據 |
| `GET` | `/api/chart/coros-summary` | 彙總儀表板：月跑量、心率趨勢、訓練負荷 |
| `POST` | `/api/chat` | 發送聊天訊息（支援檔案 ID、session ID、模式選擇） |

## 常見問題

### Q: 為什麼刷新後看不到最新數據？

檢查 `.env` 中的 `COROS_EMAIL` / `COROS_PASSWORD` 是否正確。如果 token 快取過期，刪除 `~/.coros_token_cache.json` 再重試。

### Q: 如何更換 LLM 提供者？

設定 `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_API_KEY` 指向你的端點（例如 OpenAI、Azure OpenAI、Groq 等），只要兼容 OpenAI chat completions 格式即可。

### Q: 支援哪些 COROS 地區？

美國 (`us`)、亞洲 (`asia`)、歐洲 (`eu`)。系統會自動探測可用的 API 主機。

### Q: Chart 圖表沒有顯示？

確認前端開發伺服器執行在 port 5175，且後端在 port 8000。前端 `vite.config.js` 已設定 proxy 轉發 `/api` 請求到後端。

## 貢獻指南

1. Fork 本專案
2. 建立功能分支：`git checkout -b feat/your-feature`
3. 提交變更：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feat/your-feature`
5. 建立 Pull Request

程式碼風格請遵循現有慣例，不要在 PR 中包含 `.env` 或任何憑證檔案。

## 專案結構

```
project3/
├── .env                          # 環境變數（憑證）
├── .gitignore
├── refresh_data.py               # COROS API 數據抓取
├── analysis.py                   # 2026 YTD 分析報表
├── opencode.json                 # opencode agent 設定
├── AGENTS.md                     # agent 說明文件
│
├── coros-chatbox/
│   ├── start.bat                 # 一鍵啟動 (Windows)
│   ├── backend/
│   │   ├── main.py               # FastAPI 伺服器（聊天、上傳、圖表）
│   │   ├── requirements.txt      # Python 依賴
│   │   ├── data/                 # JSON 數據快取
│   │   └── uploads/              # 上傳的 GPX/TCX/FIT 檔案
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js        # Vite 設定（port 5175）
│       └── src/
│           ├── main.js           # Vue 3 入口
│           └── App.vue           # 聊天 UI 主元件
│
└── .opencode/
    └── agents/
        ├── coros_data.md         # 數據查詢 agent
        └── coros_coach.md        # 教練分析 agent
```

## 使用範例

| 問題 | 功能 |
|------|------|
| 「顯示今個月的跑量」 | 彙總當前月份的跑步距離 |
| 「比較上星期同今個星期的配速」 | 計算兩段時間的平均配速 |
| 「分析我的恢復狀態同 HRV 趨勢」 | 提取恢復百分比、HRV 基線和趨勢 |
| 「教練模式：診斷我的訓練負荷」 | 深度分析負荷比、疲勞程度和建議 |
| 「我現在的 VO2max 同體能水平係幾多？」 | 回傳 COROS 體能評估數據 |
| 上傳 GPX 檔案後問：「繪製我的心率和海拔圖表」 | 自動渲染 Chart.js 圖表 |

## 授權條款

本專案採用 **MIT License**。

---

*Developed for Gary LAM — 香港跑手，49歲，VO2max 51，全馬 3:58。*
