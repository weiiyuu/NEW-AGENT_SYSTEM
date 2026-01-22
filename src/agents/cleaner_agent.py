# src/agents/cleaner_agent.py
import pandas as pd
import re

class CleanerAgent:
    def __init__(self):
        pass

    def clean_text(self, text):
        if pd.isna(text):
            return ""
        # 最小改動：保留換行，每行去掉多餘空白
        lines = text.split("\n")
        cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        text = "\n".join(cleaned_lines)
        return text

    def run(self, df):
        """
        清理資料：
        1. 去重
        2. 文字標準化
        3. 可擴充：缺值處理、過濾無效文章
        """
        if df.empty:
            print("CleanerAgent: 輸入資料為空")
            return df

        # 1️⃣ 去重
        df = df.drop_duplicates(subset=["link"]).copy()

        # 2️⃣ 文字清理
        for col in ["title", "content", "author"]:
            df[col] = df[col].apply(self.clean_text)

        print(f"CleanerAgent: 清理完成，共 {len(df)} 篇文章")
        return df
