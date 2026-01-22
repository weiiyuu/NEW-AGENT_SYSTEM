import os
from datetime import datetime
import pandas as pd
import ast
# 確保這些 Agent 類別能在 SRC_PATH 下找到
# 這裡假設您的 ReporterAgent 已經在 agents/reporter_agent.py 中
from agents.crawler_agent import CrawlerAgent
from agents.cleaner_agent import CleanerAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.reporter_agent import ReporterAgent
# 導入 load_master_csv, save_analysis_json 等 I/O 工具
from utils.io_helper import save_daily_csv, save_master_csv, save_analysis_json, load_master_csv

# 更新函式簽名，用 chart_output_configs 取代 chart_output_dir
def run_pipeline(target_count=3, chart_output_configs=None, report_types_to_run=None, project_root="."):
# -----------------------------------------------------------
    """
    多代理 pipeline：
    1. 爬蟲
    2. 清理資料
    3. 存檔 (更新 Master 檔)
    4. 統計分析 (基於 Master 檔)
    5. 輸出 JSON
    :param target_count: 爬蟲目標文章數
    :param chart_output_configs: 圖表輸出目錄配置清單 (由 auto_run_pipline.py 傳入，包含報告類型和路徑)
    :param report_types_to_run: 今日需要運行的報告類型清單 (例如: ['Daily Update', 'Weekly Report'])
    """

    # ------------------ 🔧 測試模式開關 ------------------
    TEST_MODE = os.environ.get("TEST_MODE") == "1"
    TEST_FILE = os.environ.get("TEST_FILE")  # e.g. data/master_test_weekly.csv

    if TEST_MODE:
        print("🧪 TEST_MODE 開啟：跳過爬蟲、清理、寫入檔案，直接使用測試資料。")
        if not TEST_FILE:
            raise ValueError("❌ TEST_MODE 啟動但未指定 TEST_FILE")

        # 讀取測試資料
        master_df = pd.read_csv(TEST_FILE)
        master_df['date'] = pd.to_datetime(master_df['date'])

        # 修正 tags 型態（因為 test csv 是 JSON 字串）
        master_df['tags_start'] = master_df['tags_start'].apply(ast.literal_eval)
        master_df['tags_end'] = master_df['tags_end'].apply(ast.literal_eval)

        raw_df = None
        cleaned_df = None

    else:
        # ------------------ 1️⃣ 爬蟲 ------------------
        print(f"---- CrawlerAgent 開始進行爬蟲爬取新聞資料 ----")
        crawler = CrawlerAgent(target_count=target_count)
        raw_df = crawler.run()  
        print(f"運行成功 爬蟲結束")
        print()

        if raw_df.empty:
            print("❌ 爬蟲未獲取到數據，流程終止。")
            return {"new_articles": [], "report_charts": {}}

        # ------------------ 2️⃣ 清理 ------------------
        print("------- CleanerAgent 開始進行資料清洗 -------\n")
        cleaner = CleanerAgent()
        cleaned_df = cleaner.run(raw_df)
        print("運行成功 資料清洗結束")

        # ------------------ 3️⃣ 存檔 ------------------
        save_daily_csv(cleaned_df, project_root=project_root)
        save_master_csv(cleaned_df, project_root=project_root) 
        print("新聞原始資料 (CSV) 存檔成功 !\n")

        # 取得 master_df
        master_df = load_master_csv(project_root=project_root)

    # ------------------ 4️⃣ 統計分析 ------------------
    print("------ AnalyzerAgent 開始進行資料分析 ------\n")
    df_for_analysis = master_df if master_df is not None and not master_df.empty else cleaned_df
    
    analyzer = AnalyzerAgent(df=df_for_analysis) 
    analysis_results = analyzer.run(df_for_analysis)
    print("運行成功 分析結束\n")
    
    save_analysis_json(analysis_results, project_root=project_root)

    # ------------------ 5️⃣ Reporter 生成圖表 (條件式執行) ------------------
    print("------ ReporterAgent 開始進行圖表繪製 ------\n")
    # 檢查是否需要生成週報或月報的圖表
    report_charts = {}
    should_generate_charts = False
    if report_types_to_run:
        should_generate_charts = any(tag in report_types_to_run for tag in ["Weekly Report", "Monthly Report"])

    # -----------------------------------------------------------
    # 根據 should_generate_charts 旗標及是否有配置來判斷是否執行 ReporterAgent
    if should_generate_charts and chart_output_configs and any(cfg['dir'] for cfg in chart_output_configs): 
        print("✅ 檢測到週報或月報需求，開始生成圖表...")
        
        # 判斷是否有模擬日期
        test_date_str = os.environ.get("TEST_DATE")
        today_for_reporter = None
        if test_date_str:
            try:
                today_for_reporter = datetime.strptime(test_date_str, "%Y-%m-%d")
                print(f"ℹ️ 使用模擬日期生成圖表: {today_for_reporter.date()}")
            except ValueError:
                print(f"⚠️ TEST_DATE 格式錯誤 ({test_date_str})，使用今天日期")
                today_for_reporter = None
        
        # 將 analysis_results, today, 和 chart_output_configs 傳入 ReporterAgent
        reporter = ReporterAgent(analysis_results, today=today_for_reporter, output_configs=chart_output_configs)
        report_charts = reporter.generate_all_reports()  # dict 包含 weekly/monthly/overall 等圖表
        print("圖表生成完成\n")
    else:
        print("ℹ️ 今日僅需每日更新 (Daily Update) 或無圖表輸出路徑配置，跳過圖表生成。")

    # ------------------ 6️⃣ 準備返回值 ------------------
    if cleaned_df is not None:
        cleaned_df['date'] = cleaned_df['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        new_articles_list = cleaned_df.to_dict('records')
    else:
        new_articles_list = []

    return {
        "new_articles": new_articles_list,
        "report_charts": report_charts
    }


if __name__ == "__main__":
    # 在 __main__ 執行時，預設只運行 daily (無圖表輸出)
    output = run_pipeline(target_count=3, chart_output_configs=[], report_types_to_run=["Daily Update"]) 
    print("Pipeline 執行完成")
