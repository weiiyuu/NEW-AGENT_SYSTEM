# scripts/generate_test_data_monthly.py
import pandas as pd
import random
from datetime import datetime, timedelta
import json

# ---------- 參數 ----------
end_date = datetime(2025, 11, 1)  # 月報日期
start_date = end_date - timedelta(days=29)  # 過去 30 天
num_articles_per_day = 5
base_link = "https://abmedia.io/test-article-"
authors = ["DW", "Louis Lin", "Neo", "Crumax", "Florence"]
tags_pool = ["人物觀點", "交易市場", "傳統金融", "贊助文章", "AI", "區塊鏈"]
titles_pool = ["市場分析", "深度報導", "專訪特輯", "新聞快訊", "技術解讀"]

# ---------- 生成資料 ----------
dates = pd.date_range(start=start_date, end=end_date, freq='D')
data = []
article_counter = 1

for day in dates:
    for i in range(num_articles_per_day):
        num_tags = random.randint(1, 3)
        tags_start_list = random.sample(tags_pool, num_tags)
        tags_end_list = random.sample(tags_pool, num_tags)
        content_length = random.randint(300, 1500)

        article = {
            "title": f"{random.choice(titles_pool)} - {day.strftime('%m%d')} {i+1}",
            "link": f"{base_link}{article_counter}",
            "date": day.strftime("%Y-%m-%d %H:%M:%S"),
            "author": random.choice(authors),
            "content": "這是一篇測試文章內容。 " * int(content_length / 10),
            "tags_start": tags_start_list,
            "tags_end": tags_end_list,
        }
        data.append(article)
        article_counter += 1

df = pd.DataFrame(data)

# ---------- 轉成 JSON 字串 ----------
def list_to_json_string(tag_list):
    return json.dumps(tag_list, ensure_ascii=False) if isinstance(tag_list, list) else tag_list

df['tags_start'] = df['tags_start'].apply(list_to_json_string)
df['tags_end'] = df['tags_end'].apply(list_to_json_string)

# ---------- 存檔 ----------
df.to_csv("data/master_test_monthly.csv", index=False, encoding="utf-8-sig")
print(f"✅ Monthly 模擬資料生成完成，共 {len(df)} 筆文章")
