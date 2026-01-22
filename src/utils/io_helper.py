import os
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any

# 創建用於儲存歷史分析結果的資料夾
# OUTPUT_DIR = "data/analysis_history"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定義 Master CSV 檔案路徑
# MASTER_FILE = "data/raw/abmedia_news_master.csv"


def load_master_csv(project_root=".") -> pd.DataFrame:
    """
    安全地載入 Master CSV 檔案，如果不存在則返回空的 DataFrame。
    """
    master_file = os.path.join(project_root, "data/raw/abmedia_news_master.csv")
    
    if os.path.exists(master_file):
        try:
            df = pd.read_csv(master_file)
            # 確保 date 欄位是 datetime 格式，便於後續分析 agent 處理
            df['date'] = pd.to_datetime(df['date'], errors='coerce') 
            # 處理 tags 欄位，確保它們是 list 類型
            for col in ['tags_start', 'tags_end', 'all_tags']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x, str) and x.startswith('[') else [])

            print(f"  ✓ 成功載入 Master CSV ({len(df)} 筆資料) 進行全面分析。")
            return df
        except Exception as e:
            print(f"❌ 載入 Master CSV 失敗: {e}")
            return pd.DataFrame()
    else:
        print("ℹ️ Master CSV 檔案不存在，將使用當前爬取的數據進行分析。")
        return pd.DataFrame()


def save_daily_csv(df, project_root=".", raw_dir="data/raw"):
    full_raw_dir = os.path.join(project_root, raw_dir)
    os.makedirs(full_raw_dir, exist_ok=True)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    updated_files = []

    for date_str, df_group in df.groupby(df['date'].dt.strftime("%Y%m%d")):
        daily_file = os.path.join(full_raw_dir, f"abmedia_news_{date_str}.csv")

        if os.path.exists(daily_file):
            existing_df = pd.read_csv(daily_file)
            df_group = pd.concat([existing_df, df_group], ignore_index=True).drop_duplicates(subset=["link"])

        # 將 tags 欄位轉換為 JSON 字串存入 CSV
        df_group['tags_start'] = df_group['tags_start'].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)
        df_group['tags_end'] = df_group['tags_end'].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)

        df_group.to_csv(daily_file, index=False, encoding="utf-8-sig")
        updated_files.append(daily_file)

    # 顯示更新結果
    print("\n📁 本次更新的 daily CSV：")
    for file in updated_files:
        count = len(pd.read_csv(file))
        print(f" - {file} ({count} 筆)")
    print()

    return True


def save_master_csv(df, project_root=".", file_path="data/raw/abmedia_news_master.csv"):
    master_path = os.path.join(project_root, file_path)
    os.makedirs(os.path.dirname(master_path), exist_ok=True)

    # 必須將 tags 欄位轉換為 JSON 字串，否則 pandas 無法正確儲存 list
    df['tags_start'] = df['tags_start'].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)
    df['tags_end'] = df['tags_end'].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)

    if os.path.exists(master_path):
        # 載入現有數據
        existing_df = pd.read_csv(master_path)
        # 僅追加新的文章
        df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset=["link"])

    df.to_csv(master_path, index=False, encoding="utf-8-sig")

    # 顯示 master 結果
    print("📚 master CSV 已更新：")
    # 再次載入 master_file 以取得準確的最新總數
    master_count = len(pd.read_csv(master_path))
    print(f" - {master_path}（目前共 {master_count} 筆）\n")

    return True


def save_analysis_json(results: Dict[str, Any], project_root="."):
    """
    將 AnalyzerAgent 的統計結果存為帶有時間戳的 JSON 檔案。
    """
    analysis_dir = os.path.join(project_root, "data/analysis_history")
    os.makedirs(analysis_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{timestamp_str}_analysis_results.json"
    filepath = os.path.join(analysis_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # 序列化結果，使用 default=str 處理 Pandas/Datetime 類型
            json_output = json.dumps(results, ensure_ascii=False, indent=4, default=str)
            f.write(json_output)
        print(f"✓ 分析結果 JSON 已存至: {filepath}\n")
    except Exception as e:
        print(f"❌ 儲存分析結果 JSON 失敗: {e}")