# 📄 NEW-AGENT_SYSTEM — README.md

## ⭐ 專案概述 (Project Overview)

`NEW-AGENT_SYSTEM` 是一個多代理 (Multi-Agent) 驅動的數據管線系統，用於自動化爬取、清理、分析新聞內容，並依照日期 (日、週、月) 自動產生不同層級的分析報告與圖表，最後透過 Webhook 推送至下游系統（例如 n8n）。

---

## 📁 專案目錄結構 (Directory Structure)

下方為系統結構與用途說明：

| 目錄/檔案 | 說明 | 用途 |
|---------|------|------|
| `NEW-AGENT_SYSTEM/` | 專案根目錄 | 所有指令皆從此執行 |
| ├── `auto_run_pipeline.py` | 主程式 | 啟動整個 Agent Pipeline |
| ├── `src/` | 核心程式碼 | 包含所有 Agent 與 Pipeline 邏輯 |
| │   ├── `agents/` | Agent 邏輯層 | `crawler_agent`、`cleaner_agent`、`analyzer_agent`、`writer_agent`、`reporter_agent` 等 |
| │   ├── `pipeline.py` | Pipeline 流程控制 | 負責協調各 Agent 執行順序 |
| │   └── `utils/` | 工具模組 | `io_helper.py` 等 I/O 輔助功能 |
| ├── `data/` | 數據儲存區 | 運行後生成的所有資料 |
| │   ├── `analysis_charts/` | 圖表輸出 | `monthly/` 與 `weekly/` 報表圖 |
| │   ├── `analysis_history/` | 分析歷史 | Analyzer 輸出的 `.json` 分析記錄 |
| │   └── `raw/` | 原始資料 | 每日爬取與 master.csv 儲存地 |
| ├── `scripts/` | 測試腳本 | 用於產生測試資料 |
| ├── `requirements.txt` | 套件清單 | 系統必要第三方套件 |
| └── `README.md` | 專案說明文件 | **你正在看的這份檔案** |

---

## 🛠 環境設置與安裝 (Setup & Installation)

請確保系統已安裝 **Python 3.8+**

### 1. 進入專案根目錄

```bash
cd NEW-AGENT_SYSTEM
```

---

### 2. 建立虛擬環境（強烈建議）

```bash
python -m venv venv
```

---

### 3. 啟動虛擬環境

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
.\venv\Scripts\activate
```

---

### 4. 安裝專案依賴

```bash
pip install -r requirements.txt
```


## ▶ 運行專案 (Running the Pipeline)

所有指令請在專案根目錄執行：

```bash
python auto_run_pipeline.py
```

程式會依照「今日日期」自動判斷是否產生：

- 日報 Daily update  
- 週報 Weekly Report（週一）  
- 月報 Monthly Report（每月 1 日）  

---

## 🧪 測試模式（Test Mode）

本專案支援以 **環境變數** 進入測試模式，用來指定：

- 特定輸入 CSV 檔案
- 模擬程式執行日期（用於觸發週報/月報）
- 跳過爬蟲階段，加速測試

### Test Mode 欄位說明

| 變數 | 作用 |
|------|------|
| `TEST_MODE=1` | 開啟測試模式 |
| `TEST_FILE` | 指定 master CSV |
| `TEST_DATE` | 模擬日期（決定要產生日/週/月報） |

---

## 🧪 Weekly（週報）測試

模擬週一運行 → 應輸出週報。

### macOS / Linux

```bash
export TEST_MODE=1
export TEST_FILE="data/master_test_weekly.csv"
export TEST_DATE="2025-11-24"
python auto_run_pipeline.py
```

### Windows

```bash
set TEST_MODE=1
set TEST_FILE=data/master_test_weekly.csv
set TEST_DATE=2025-11-24
python auto_run_pipeline.py
```

---

## 🧪 Monthly（月報）測試

模擬每月 1 日 → 輸出月報。

### macOS / Linux

```bash
export TEST_MODE=1
export TEST_FILE="data/master_test_monthly.csv"
export TEST_DATE="2025-11-01"
python auto_run_pipeline.py
```

### Windows

```bash
set TEST_MODE=1
set TEST_FILE=data/master_test_monthly.csv
set TEST_DATE=2025-11-01
python auto_run_pipeline.py
```

---

## 🧪 Daily + Weekly + Monthly（混合測試）

模擬：  
**每月 1 號**  
且  
**剛好是週一** → 三種報告全部應產生。

### macOS / Linux

```bash
export TEST_MODE=1
export TEST_FILE="data/master_test.csv"
export TEST_DATE="2025-12-01"
python auto_run_pipeline.py
```

### Windows

```bash
set TEST_MODE=1
set TEST_FILE=data/master_test.csv
set TEST_DATE=2025-12-01
python auto_run_pipeline.py
```

---

## 測試模式運行結束後請記得恢復環境變數，以免無法觸發正式環境的爬蟲抓取：

```bash
unset TEST_MODE
unset TEST_FILE
unset TEST_DATE
```

---

### 當前資料夾已存在：
1. Daily + Weekly + Monthly（混合測試）的檔案（分析結果、圖表）
2. 12/4 當日實際爬取的檔案 （CSV、分析結果）

若想要實際操作，並更直觀地看到檔案確實會被存取到預定位置，可以前往：
1. raw
2. analysis_history
3. analysis_charts 內的 weekly、monthly
等資料夾內把所有檔案清空，再開始運行測試。
