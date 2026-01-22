import pandas as pd
import random
from datetime import datetime
import json # <--- [新增] 導入 json 模組

# 參數
start_date = datetime(2025, 11, 1)
end_date = datetime(2025, 12, 1)
num_articles_per_day = 5
base_link = "https://abmedia.io/test-article-"

authors = ["DW", "Louis Lin", "Neo", "Crumax", "Florence"]
tags_pool = ["人物觀點", "交易市場", "傳統金融", "贊助文章", "AI", "區塊鏈"]
titles_pool = ["市場分析", "深度報導", "專訪特輯", "新聞快訊", "技術解讀"]

dates = pd.date_range(start=start_date, end=end_date, freq='D')

data = []
article_counter = 1
for day in dates:
    for i in range(num_articles_per_day):
        
        # 隨機選擇 1 到 3 個 tags
        num_tags = random.randint(1, 3)
        tags_start_list = random.sample(tags_pool, num_tags)
        tags_end_list = random.sample(tags_pool, num_tags)
        
        # 模擬文章長度
        content_length = random.randint(300, 1500)
        
        article = {
            "title": f"{random.choice(titles_pool)} - {day.strftime('%m%d')} {i+1}",
            "link": f"{base_link}{article_counter}", # 確保連結唯一
            "date": day.strftime("%Y-%m-%d %H:%M:%S"), # 讓日期更接近爬蟲格式
            "author": random.choice(authors),
            "content": "這是一篇測試文章內容。 " * int(content_length / 10), # 模擬不同長度
            "tags_start": tags_start_list,
            "tags_end": tags_end_list,
        }
        data.append(article)
        article_counter += 1

df = pd.DataFrame(data)

# ----------------------------------------------------------------------
# 關鍵修正：將 Tags 欄位轉換為 JSON 字串 (使用雙引號 " )
# ----------------------------------------------------------------------
def list_to_json_string(tag_list):
    # 確保與 io_helper.save_master_csv 中的 json.dumps(ensure_ascii=False) 行為一致
    return json.dumps(tag_list, ensure_ascii=False) if isinstance(tag_list, list) else tag_list

df['tags_start'] = df['tags_start'].apply(list_to_json_string)
df['tags_end'] = df['tags_end'].apply(list_to_json_string)


# 轉存 CSV
# 註：建議使用 utf-8-sig 確保中文顯示正常
df.to_csv("data/master_test.csv", index=False, encoding="utf-8-sig")
print(f"✅ 模擬資料生成完成，共 {len(df)} 筆文章。Tags 現已儲存為 JSON 雙引號字串。")