import sys
import os
import json
import requests
import glob
import pandas as pd
from datetime import date, datetime

# -------------------------------
# 讓 Python 可以找到 src
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
sys.path.append(SRC_PATH)
# -------------------------------

# 由於 run_pipeline 簽名已修改，這裡需要確保它能正確被引用
from pipeline import run_pipeline

# 1️⃣ 參數設定
TARGET_COUNT = 50 # 每次抓幾篇文章
N8N_WEBHOOK = "https://alexchang0531-n8n-free.hf.space/webhook-test/news-pipeline"
ANALYSIS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/analysis_history")


def get_execution_date():
    """
    處理測試日期環境變數，返回用於執行的日期物件 (date)。
    此函式用於統一獲取執行日期，避免重複的日期判斷邏輯。
    """
    test_date_str = os.environ.get("TEST_DATE")
    if test_date_str:
        try:
            today = datetime.strptime(test_date_str, "%Y-%m-%d").date()
            print(f"ℹ️ 測試模式：使用模擬日期 {today} 進行報告類型判斷。")
            return today
        except ValueError:
            print(f"⚠️ TEST_DATE 環境變數格式錯誤 ({test_date_str})，使用當前實際日期。")
            return date.today()
    else:
        return date.today()


def get_current_report_type(today: date):
    """
    根據傳入的日期判斷應發送哪幾種報告類型，返回一個列表 (使用完整的報告名稱標籤)。
    修正: 每天都必須執行 'Daily Update'，並偵測週一和每月一號。
    """
    force_daily_test = os.environ.get("FORCE_DAILY_TEST") == "true"
    reports_to_run = []

    # 每月 1 號
    if today.day == 1:
        reports_to_run.append("Monthly Report")
    # 每週一
    if today.weekday() == 0:
        reports_to_run.append("Weekly Report")
    # 每日更新 (無條件執行，且是必須的)
    reports_to_run.append("Daily Update")

    if force_daily_test:
        print("🚨 測試模式啟用: 已檢查 FORCE_DAILY_TEST 旗標。")
    # 這裡移除 force_daily_test 相關邏輯，保持報告類型判斷單純 (已包含在 reports_to_run)
    return reports_to_run


# 2.5 獲取今日日期並定義圖表儲存路徑
today_date = get_execution_date()
reports_to_run = get_current_report_type(today_date)

# 根據運行報告類型，創建分層的圖表輸出路徑
CHARTS_BASE_DIR = os.path.join(PROJECT_ROOT, "data/analysis_charts")
date_str = today_date.strftime("%Y-%m-%d")

chart_output_configs = []
is_monthly = "Monthly Report" in reports_to_run
is_weekly = "Weekly Report" in reports_to_run

if is_monthly:
    # 月報圖表 (使用 monthly/YYYY-MM-DD 作為根目錄)
    monthly_dir = os.path.join(CHARTS_BASE_DIR, "monthly", date_str)
    chart_output_configs.append({"report_tag": "Monthly Report", "dir": monthly_dir})

if is_weekly:
    # 週報圖表 (使用 weekly/YYYY-MM-DD 作為根目錄)
    weekly_dir = os.path.join(CHARTS_BASE_DIR, "weekly", date_str)
    chart_output_configs.append({"report_tag": "Weekly Report", "dir": weekly_dir})

# 如果只有 Daily Update (即 Mon/1st 都不滿足)，圖表配置為空，ReporterAgent 將不會生成圖表
if not chart_output_configs:
    # 為了保持結構一致，對於 Daily Update 且不生成圖表的情況，也加入一個配置項 (dir=None)
    chart_output_configs.append({"report_tag": "Daily Update", "dir": None})

print(f"📁 今日需生成圖表至 {len([cfg for cfg in chart_output_configs if cfg['dir']])} 個獨立根目錄：")
for item in chart_output_configs:
    if item['dir']:
        print(f"   - [{item['report_tag']}]: {item['dir']}")


# 2️⃣ 執行 pipeline
print("\n🚀 開始執行完整 pipeline\n")
# 傳遞新的圖表輸出路徑配置清單，並要求 pipeline 在此路徑下建立資料夾並儲存圖表
# 傳遞今日的報告類型清單給 pipeline，以控制圖表生成
pipeline_output = run_pipeline(
    target_count=TARGET_COUNT, 
    chart_output_configs=chart_output_configs, # <--- 傳遞配置清單
    report_types_to_run=reports_to_run, # 新增參數，用於控制 pipeline 內的圖表生成
    project_root=PROJECT_ROOT,
)
new_articles = pipeline_output["new_articles"] # 本日文章
report_charts = pipeline_output["report_charts"] # 圖表已在 pipeline 內本地存檔
print("---------------------------------------------------------------------")
print("Pipeline 執行完成！新聞內容(csv)、分析結果(Json)、分析圖表已存檔治本地資料夾。")


# 3️⃣ 載入最新的分析 JSON
if not os.path.exists(ANALYSIS_OUTPUT_DIR):
    print(f"❌ 分析結果目錄不存在: {ANALYSIS_OUTPUT_DIR}")
    sys.exit(1)
list_of_files = glob.glob(os.path.join(ANALYSIS_OUTPUT_DIR, '*.json'))
if not list_of_files:
    print("❌ 找不到分析結果 JSON 檔案，停止推送。")
    sys.exit(1)

latest_file = max(list_of_files, key=os.path.getctime)
latest_filename = os.path.basename(latest_file)

analysis_payload = {}
try:
    with open(latest_file, 'r', encoding='utf-8') as f:
        analysis_payload = json.load(f)
    print(f"\n✓ 載入完整的分析報告 JSON ({latest_filename})")
except Exception as e:
    print(f"❌ 載入分析 JSON 失敗: {e}")
    sys.exit(1)


# 4️⃣ 構造單一、非冗餘 Payload
reports_to_send = reports_to_run

if not reports_to_send:
    print("❌ reports_to_send 列表為空，流程異常終止。")
    sys.exit(1)

# 判斷是否包含需要完整分析 JSON 的報告類型 (Weekly/Monthly)
should_include_analysis_json = any(tag in reports_to_send for tag in ["Weekly Report", "Monthly Report"])

print(f"📤 今日需推送 {len(reports_to_send)} 種報告，將打包在單一 Webhook 中: {', '.join(reports_to_send)}...")

final_payload = {
    "report_tags": reports_to_send,
    "todays_news_data": new_articles,
    # 移除 "report_charts" 欄位，因為 n8n 只需要純文字分析結果
}

# 根據用戶要求，僅在需要週報或月報時才加入完整的 JSON 分析結果
if should_include_analysis_json:
    print("ℹ️ 檢測到週報或月報需求，將包含 'realtime_analysis_json'。\n")
    final_payload["realtime_analysis_json"] = analysis_payload
else:
    # 由於 Daily Update 只需要文章列表和簡單總結，不包含完整的 analysis_payload
    print("ℹ️ 僅需每日更新，將不包含 'realtime_analysis_json' 以減少 Payload 大小。\n")


# 5️⃣ 發送單一 Webhook
try:
    print(f"📦 發送包含 {len(reports_to_send)} 個報告指令的單一 Payload...")
    res = requests.post(N8N_WEBHOOK, json=final_payload)

    if res.status_code == 200:
        print(f"✅ 推送成功！單一 Payload 已一次性送到 n8n。")
    else:
        print(f"⚠️ 推送失敗，HTTP {res.status_code}")
        print(res.text)

except Exception as e:
    print(f"❌ 推送單一 Webhook 過程發生錯誤:", e)

print("\n--- 所有報告推送完成 ---")