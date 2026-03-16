# 📄 NEW-AGENT_SYSTEM — README.md

## ⭐ 專案概述 (Project Overview)

`NEW-AGENT_SYSTEM` 是一個多代理 (Multi-Agent) 驅動的數據管線系統，用於自動化爬取、清理、分析新聞內容，並依照日期 (日、週、月) 自動產生不同時間尺度的分析報告與圖表，最後透過 Webhook 推送至 n8n。

------------------------------------------------------------------------------

## 📊 成果預覽 (Demo Results)

專案簡報：`docs/python&n8n_多代理自動化新聞分析系統.pdf`

若尚未運行程式，可直接查看以下預先保留的 Demo 檔案，了解系統產出格式：
1. **分析報告**：`data/analysis_history/analysis_result_demo.json`
2. **視覺化圖表**：
   - 月報圖片範例：`data/analysis_charts/monthly/2025-12-01/30d_tags_stacked_top10_demo.png`
   - 週報圖片範例：`data/analysis_charts/weekly/2025-12-01/weekly_top_tags_top10_demo.png`

------------------------------------------------------------------------------

## 📁 專案目錄結構 (Directory Structure)

```text
NEW-AGENT_SYSTEM/
│
├── auto_run_pipeline.py        # 主程式，啟動整個 Agent Pipeline
│
├── src/                        # 核心程式碼
│   ├── agents/                 # Agent 邏輯層
│   │   ├── crawler_agent.py
│   │   ├── cleaner_agent.py
│   │   ├── analyzer_agent.py
│   │   └── reporter_agent.py
│   │
│   ├── pipeline.py             # Pipeline 流程控制
│   │
│   └── utils/                  # 工具模組
│       └── io_helper.py
├── docs/                       # 專案簡報
├── data/                       # 數據儲存區
│   ├── analysis_charts/        # 圖表輸出
│   │   ├── monthly/
│   │   └── weekly/
│   │
│   ├── analysis_history/       # 分析歷史 JSON
│   │
│   └── raw/                    # 原始爬蟲資料
│
├── scripts/                    # 測試腳本
│
├── requirements.txt            # 套件清單
│
└── README.md                   # 專案說明文件
```

------------------------------------------------------------------------------

### 環境一致性 (Reproducibility)
環境隔離：
- **依賴管理**：透過 `pip freeze` 產出 `requirements.txt`，確保所有套件版本與開發環境完全一致。
- **Git 忽略＆保留規則**：
    - 透過 `.gitignore` 精準排除 `__pycache__`、`.DS_Store` 及大量測試用原始數據，保持倉庫輕量化。
    - 為了確保專案在 Clone 後即可直接運行，本專案採用 `.gitkeep` 確保 `data/` 下的所有層級目錄（如 `monthly/`, `weekly/`）在 Git 倉庫中完整保留。


## 🛠 環境設置與安裝 (Setup & Installation)

請確保系統已安裝 **Python 3.8+**

### 1. 進入專案根目錄

```bash
cd NEW-AGENT_SYSTEM
```

---

### 2. 建立虛擬環境（強烈建議）

**使用 Conda:**
```bash
conda create -n news-agent python=3.9
conda activate news-agent
```

**使用 venv:**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

---

### 3. 安裝專案依賴

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

------------------------------------------------------------------------------

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

模擬週一運行 → 輸出週報。

### macOS / Linux

```bash
export TEST_MODE=1 TEST_FILE="data/master_test_weekly.csv" TEST_DATE="2025-11-24" # TEST_DATE 可改為最近的週一日期
python auto_run_pipeline.py
unset TEST_MODE TEST_FILE TEST_DATE
```

### Windows

```bash
$env:TEST_MODE="1"; $env:TEST_FILE="data/master_test_weekly.csv"; $env:TEST_DATE="2025-11-24" # TEST_DATE 可改為最近的週一日期
python auto_run_pipeline.py
Remove-Item Env:TEST_MODE, Env:TEST_FILE, Env:TEST_DATE
```

---

## 🧪 Monthly（月報）測試

模擬每月 1 日 → 輸出月報。

### macOS / Linux

```bash
export TEST_MODE=1 TEST_FILE="data/master_test_monthly.csv" TEST_DATE="2025-11-01" # TEST_DATE 可改為最近月份的一號
python auto_run_pipeline.py
unset TEST_MODE TEST_FILE TEST_DATE
```

### Windows

```bash
$env:TEST_MODE="1"; $env:TEST_FILE="data/master_test_monthly.csv"; $env:TEST_DATE="2025-11-01" # TEST_DATE 可改為最近月份的一號
python auto_run_pipeline.py
Remove-Item Env:TEST_MODE, Env:TEST_FILE, Env:TEST_DATE
```

---

## 🧪 Daily + Weekly + Monthly（混合測試）

模擬 **每月 1 號** 且 **剛好是週一** → 三種報告全部應產生。

### macOS / Linux

```bash
export TEST_MODE=1 TEST_FILE="data/master_test.csv" TEST_DATE="2025-12-01" # TEST_DATE 可改為最近的符合條件的日期
python auto_run_pipeline.py
unset TEST_MODE TEST_FILE TEST_DATE
```

### Windows

```bash
$env:TEST_MODE="1"; $env:TEST_FILE="data/master_test.csv"; $env:TEST_DATE="2025-12-01" # TEST_DATE 可改為最近的符合條件的日期
python auto_run_pipeline.py
Remove-Item Env:TEST_MODE, Env:TEST_FILE, Env:TEST_DATE
```

---