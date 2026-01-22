import json
import os
import random
from collections import defaultdict
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from wordcloud import WordCloud

# 設置 Matplotlib 繪圖的中文支持和美觀樣式
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False 
sns.set_style("whitegrid", {"font.sans-serif":['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']})

class ReporterAgent:
    """
    負責載入分析 JSON 資料，並使用 Matplotlib/Seaborn 生成報告所需的各種圖表。
    """

    # -----------------------------------------------------------
    # 更新函式簽名，用 output_configs 取代 output_dir
    def __init__(self, analysis_results: dict, today: datetime = None, output_configs: list = None):
        """
        初始化並載入數據。
        """
        
        if not analysis_results or not analysis_results.get("content_insights"):
            print("❌ 傳入的分析結果無效或為空。圖表生成將被跳過。")
            self.data = None
            self.daily_data_7d = pd.DataFrame()
            self.daily_data_30d = pd.DataFrame()
            self.word_counts_df = pd.DataFrame()
            return
            
        self.data = analysis_results
        self.today = today
        # self.output_dir = output_dir # 移除
        
        # 根據配置清單，建立報告類型到根目錄路徑的映射
        self.output_configs = output_configs if output_configs is not None else []
        self.output_map = {item['report_tag']: item['dir'] for item in self.output_configs if item['dir']}
        
        print(f"載入分析結果成功，圖表儲存目錄配置已建立。")
        
        # 數據準備
        self.daily_data_7d = self._prepare_daily_data('last_7_days')
        self.daily_data_30d = self._prepare_daily_data('last_30_days')
        self.word_counts_df = self._simulate_word_counts()
        

    def _prepare_daily_data(self, period_key):
        """將 daily_breakdown 轉換為 Pandas DataFrame，並展開 tags_count/author_counts 以便繪圖。"""
        if self.data is None:
            return pd.DataFrame()
        try:
            breakdown = self.data['period_insights'][period_key]['daily_breakdown']
            df = pd.DataFrame.from_dict(breakdown, orient='index')
            df.index = pd.to_datetime(df.index)
            # 確保 tags_count 和 author_counts 是可處理的
            if 'tags_count' in df.columns:
                 df['tags_count'] = df['tags_count'].apply(lambda x: x if isinstance(x, dict) else {})
            if 'author_counts' in df.columns:
                 df['author_counts'] = df['author_counts'].fillna('{}') # 處理 NaN
                 df['author_counts'] = df['author_counts'].apply(lambda x: x if isinstance(x, dict) else json.loads(x) if isinstance(x, str) else {})
            return df.sort_index()
        except KeyError as e:
            print(f"⚠️ 數據準備錯誤: 找不到鍵 {e}，返回空 DataFrame。")
            return pd.DataFrame()

    def _simulate_word_counts(self):
        # 保持不變，因為這部分邏輯沒有問題
        if self.data is None: return pd.DataFrame()
        try:
            stats = self.data['content_insights']['content_length_stats']
            avg, std = stats.get('average', 500), 50
            min_len, max_len = stats.get('min', 100), stats.get('max', 2000)
            total_posts = self.data['period_insights']['last_30_days'].get('total_post_count', 100)
            
            word_counts = np.random.normal(avg, std, total_posts)
            word_counts = np.clip(word_counts, min_len, max_len).astype(int)

            dates_30d = self.daily_data_30d.index.tolist()
            temp_list = []
            word_counts_list = word_counts.tolist()
            
            for date in dates_30d:
                if date in self.daily_data_30d.index:
                    post_count = self.daily_data_30d.loc[date, 'post_count']
                else: continue
                
                daily_counts = random.sample(word_counts_list, min(post_count, len(word_counts_list)))
                word_counts_list = [c for c in word_counts_list if c not in daily_counts]

                for count in daily_counts:
                    temp_list.append({'date': date, 'content_length': count})

            return pd.DataFrame(temp_list)
        except KeyError as e:
            print(f"⚠️ 模擬字數數據失敗: 找不到鍵 {e}，返回空 DataFrame。")
            return pd.DataFrame()


    # -----------------------------------------------------------
    # _save_plot：根據 subdir 判斷報告類型，從 output_map 獲取根目錄
    def _save_plot(self, fig, filename, subdir=""):
        """儲存圖表到指定的輸出目錄，可選子目錄。"""
        
        # 1. 判斷報告類型標籤
        report_tag = ""
        if subdir == "weekly":
            report_tag = "Weekly Report"
        elif subdir == "monthly" or subdir == "overall": # Monthly Report 包含 monthly 和 overall 圖表
            report_tag = "Monthly Report"
            
        # 2. 查找儲存根目錄
        final_dir = self.output_map.get(report_tag)
        
        if not final_dir:
            # 這是預期的行為，如果 ReporterAgent 只被要求生成週報，則月報相關圖表會跳過儲存
            # print(f"⚠️ 找不到 {report_tag} 的圖表儲存路徑，跳過儲存 {filename}。")
            plt.close(fig)
            return None
        
        # 3. 如果是 overall 圖表，則在月報路徑下創建 overall 子目錄
        if subdir == "overall":
            final_dir = os.path.join(final_dir, subdir)
            
        # 4. 儲存檔案
        os.makedirs(final_dir, exist_ok=True) # 確保目錄存在
        filepath = os.path.join(final_dir, filename)
        fig.savefig(filepath, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return filepath

    # --- 完整的繪圖功能實現 ---

    # 每日文章數折線圖 (最近 7 天 / 30 天)
    def plot_daily_post_count(self, period='30d'):
        # 根據週期選擇數據
        if period == '7d':
            df_to_plot = self.daily_data_7d
        else: # 默認為 '30d'
            df_to_plot = self.daily_data_30d
        
        if df_to_plot.empty: return None

        filename = f"daily_post_count_{period}.png"
        title = f"近{period.strip('d')}天 每日發文數量趨勢"
        
        fig, ax = plt.subplots(figsize=(10, 5))
        # 繪製每日文章數折線圖
        sns.lineplot(data=df_to_plot, x=df_to_plot.index, y='post_count', marker='o', ax=ax, color='teal', label='每日文章數')

        # 僅在 30d 圖上疊加 7 天移動平均線以提供趨勢平滑視圖
        if period == '30d' and not df_to_plot.empty:
            # 計算 7 天移動平均線 (7-day Rolling Average)
            df_to_plot['rolling_avg_7d'] = df_to_plot['post_count'].rolling(window=7, min_periods=1).mean()
            sns.lineplot(data=df_to_plot, x=df_to_plot.index, y='rolling_avg_7d', ax=ax, color='red', linestyle='--', label='7天移動平均線')
            ax.legend(loc='upper right')

        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期')
        ax.set_ylabel('文章數量')
        
        # 調整日期顯示格式
        if period == '30d':
             # 30天圖表只顯示每週的日期，避免擁擠
             ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        # 7天圖表顯示所有日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 使用 subdir 告訴 _save_plot 這是 monthly 還是 weekly 報告
        return self._save_plot(fig, filename, subdir="monthly" if period == '30d' else "weekly") 

    # 熱門 Tags 長條圖 (一週)
    def plot_top_tags(self, limit=10):
        try:
            tag_counts = self.data['period_insights']['last_7_days']['tag_counts']
            if not tag_counts: return None
            
            df_tags = pd.DataFrame(list(tag_counts.items()), columns=['Tag', 'Count']).nlargest(limit, 'Count')

            filename = "weekly_top_tags_top10.png"
            title = f"近7日熱門標籤 Top {limit}"

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Count', y='Tag', data=df_tags, ax=ax, palette='viridis', hue='Tag', legend=False)
            ax.set_title(title, fontsize=16)
            ax.set_xlabel('文章數')
            ax.set_ylabel('標籤')
            plt.tight_layout()

            return self._save_plot(fig, filename, subdir="weekly")
        except Exception:
            return None

    # 熱門作者長條圖 (一週 / 月度貢獻度)
    def plot_top_authors(self, period='7d', limit=10):
        try:
            author_counts = self.data['period_insights'][f'last_{period.split("d")[0]}_days']['author_counts']
            if not author_counts: return None
            
            df_authors = pd.DataFrame(list(author_counts.items()), columns=['Author', 'Count']).nlargest(limit, 'Count')

            filename = f"{period}_top_authors_top{limit}.png"
            title = f"近{period} 高貢獻度作者 Top {limit}"

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Count', y='Author', data=df_authors, ax=ax, palette='rocket', hue='Author', legend=False)
            ax.set_title(title, fontsize=16)
            ax.set_xlabel('文章數')
            ax.set_ylabel('作者')
            plt.tight_layout()

            subdir = "monthly" if period == '30d' else "weekly"
            return self._save_plot(fig, filename, subdir=subdir)
        except Exception:
            return None

    # 每日 Tags 堆疊長條圖 (一週 / 30天)
    def plot_daily_tags_stacked_bar(self, period='7d', top_n=5):
        df_to_plot = self.daily_data_7d if period == '7d' else self.daily_data_30d
        if df_to_plot.empty: return None

        tags_series = df_to_plot['tags_count']
        tags_exploded = pd.DataFrame([
            {**{'date': idx}, **item} for idx, row in tags_series.items() for item in [row] if row
        ])

        if tags_exploded.empty: return None

        df_daily_tags = tags_exploded.set_index('date').apply(pd.Series).fillna(0)
        
        # 找出 Top N tags
        all_tags_sum = df_daily_tags.sum().sort_values(ascending=False)
        top_tags = all_tags_sum.index[:top_n].tolist()
        
        # 選擇 Top N tags，並將其他 tags 合併為 'Other'
        df_plot = df_daily_tags[top_tags].copy()
        df_plot['其他'] = df_daily_tags.drop(columns=top_tags, errors='ignore').sum(axis=1)
        
        # 確保日期格式
        df_plot.index = df_plot.index.strftime('%m/%d')
        df_plot.index.name = '日期'

        filename = f"{period}_tags_stacked_top{top_n}.png"
        title = f"近{period.strip('d')}天 Top {top_n} 標籤每日堆疊圖"
        
        fig, ax = plt.subplots(figsize=(12, 6))
        df_plot.plot(kind='bar', stacked=True, ax=ax, colormap='Spectral')
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期')
        ax.set_ylabel('文章數量')
        plt.xticks(rotation=45)
        ax.legend(title='標籤', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        subdir = "monthly" if period == '30d' else "weekly"
        return self._save_plot(fig, filename, subdir=subdir)

    # 作者 × 日期熱力圖 (一週)
    def plot_weekly_author_heatmap(self, top_n=5):
        try:
            if self.daily_data_7d.empty: return None
            
            author_data = []
            for date, row in self.daily_data_7d.iterrows():
                if isinstance(row['author_counts'], dict):
                    for author, count in row['author_counts'].items():
                        author_data.append({'Date': date.strftime('%m/%d'), 'Author': author, 'Count': count})
            
            df_author = pd.DataFrame(author_data)
            if df_author.empty: return None
            
            top_authors = df_author.groupby('Author')['Count'].sum().nlargest(top_n).index.tolist()
            df_pivot = df_author[df_author['Author'].isin(top_authors)].pivot_table(
                index='Author', columns='Date', values='Count', fill_value=0
            )

            filename = "weekly_author_heatmap.png"
            title = f"近7日 Top {top_n} 作者發文熱力圖"

            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(df_pivot, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5, cbar_kws={'label': '文章數'})
            ax.set_title(title, fontsize=16)
            ax.set_xlabel('日期')
            ax.set_ylabel('作者')
            plt.tight_layout()
            
            return self._save_plot(fig, filename, subdir="weekly")
        except Exception:
            return None
    
    # Tags 一週走勢折線圖 (Top 5 tag)
    def plot_weekly_tag_trend(self, top_n=5):
        if self.daily_data_7d.empty: return None

        tags_series = self.daily_data_7d['tags_count']
        
        tags_exploded = pd.DataFrame([
            {**{'date': idx}, **item} for idx, row in tags_series.items() for item in [row] if row
        ])
        
        if tags_exploded.empty: return None

        df_daily_tags = tags_exploded.set_index('date').apply(pd.Series).fillna(0)
        
        all_tags_sum = df_daily_tags.sum().sort_values(ascending=False)
        top_tags = all_tags_sum.index[:top_n].tolist()
        
        df_plot = df_daily_tags[top_tags].copy()
        df_plot.index.name = 'Date'
        df_plot = df_plot.melt(ignore_index=False, var_name='Tag', value_name='Count').reset_index()

        filename = "weekly_tag_trend_top5.png"
        title = f"近7日 Top {top_n} 標籤趨勢"

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(data=df_plot, x='Date', y='Count', hue='Tag', marker='o', ax=ax)
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期')
        ax.set_ylabel('文章數')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.legend(title='標籤', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return self._save_plot(fig, filename, subdir="weekly")

    # 字數分布 Histogram (一週 / 全期間)
    def plot_word_count_histogram(self, period='7d'):
        if self.word_counts_df.empty: return None
        
        df_to_plot = self.word_counts_df
        
        if period == '7d':
            latest_date = self.word_counts_df['date'].max()
            start_date = latest_date - pd.Timedelta(days=6)
            df_to_plot = self.word_counts_df[self.word_counts_df['date'] >= start_date]
            subdir = "weekly"
        elif period == '30d':
            # 確保 30d 使用整個 word_counts_df
            subdir = "monthly"
        else:
             # overall 圖表 (如果未來有加入)
            return None # 暫時不處理 all_time
        
        if df_to_plot.empty: return None

        filename = f"{period}_word_count_histogram.png"
        title = f"近{period.strip('d')}天 文章字數分佈直方圖"

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(df_to_plot['content_length'], bins=20, kde=True, ax=ax, color='purple')
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('文章字數')
        ax.set_ylabel('文章數量')
        plt.tight_layout()
        
        return self._save_plot(fig, filename, subdir=subdir)

    # 月度 Tags 趨勢 (多折線圖)
    def plot_monthly_tag_trend(self, period='30d', top_n=20):
        df_to_plot = self.daily_data_30d # 僅保留 30d 趨勢圖
        if df_to_plot.empty: return None

        tags_series = df_to_plot['tags_count']
        tags_exploded = pd.DataFrame([
            {**{'date': idx}, **item} for idx, row in tags_series.items() for item in [row] if row
        ])
        if tags_exploded.empty: return None

        df_daily_tags = tags_exploded.set_index('date').apply(pd.Series).fillna(0)
        
        all_tags_sum = df_daily_tags.sum().sort_values(ascending=False)
        top_tags = all_tags_sum.index[:top_n].tolist()
        
        df_plot = df_daily_tags[top_tags].copy()
        df_plot.index.name = 'Date'
        df_plot = df_plot.melt(ignore_index=False, var_name='Tag', value_name='Count').reset_index()

        filename = f"{period}_tags_trend_top{top_n}.png"
        title = f"{period.strip('d')} 天 Top {top_n} 標籤趨勢"

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=df_plot, x='Date', y='Count', hue='Tag', ax=ax, legend=False)
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期')
        ax.set_ylabel('文章數')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        
        # 標籤顯示 Top 5
        top_tags_legend = top_tags[:5] 
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[:5], top_tags_legend, title='Top 5 標籤', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()
        
        return self._save_plot(fig, filename, subdir="monthly")

    # Tags 月度熱力圖 (30 天)
    def plot_monthly_tag_heatmap(self, top_n=10):
        if self.daily_data_30d.empty: return None

        tags_series = self.daily_data_30d['tags_count']
        tags_exploded = pd.DataFrame([
            {**{'date': idx}, **item} for idx, row in tags_series.items() for item in [row] if row
        ])
        if tags_exploded.empty: return None

        df_daily_tags = tags_exploded.set_index('date').apply(pd.Series).fillna(0)
        
        all_tags_sum = df_daily_tags.sum().sort_values(ascending=False)
        top_tags = all_tags_sum.index[:top_n].tolist()
        
        df_pivot = df_daily_tags[top_tags].copy().transpose()
        df_pivot.columns = df_pivot.columns.strftime('%m/%d')
        

        filename = "monthly_tag_heatmap.png"
        title = f"近30日 Top {top_n} 標籤發文熱力圖"

        fig, ax = plt.subplots(figsize=(15, 10))
        sns.heatmap(df_pivot, annot=True, fmt='g', cmap='YlOrRd', linewidths=.5, cbar_kws={'label': '文章數'})
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期')
        ax.set_ylabel('標籤')
        plt.tight_layout()
        
        return self._save_plot(fig, filename, subdir="monthly")

    # 全期間月度文章數量折線圖
    def plot_overall_monthly_post_count(self):
        try:
            monthly_breakdown = self.data['period_insights']['all_time']['monthly_breakdown']
            if not monthly_breakdown: return None
            
            df_monthly = pd.DataFrame.from_dict(monthly_breakdown, orient='index')
            df_monthly.index = pd.to_datetime(df_monthly.index, format='%Y-%m')

            filename = "overall_monthly_post_count.png"
            title = "全期間每月文章數量趨勢"
            
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=df_monthly, x=df_monthly.index, y='total_post_count', marker='o', ax=ax, color='navy')
            ax.set_title(title, fontsize=16)
            ax.set_xlabel('月份')
            ax.set_ylabel('文章數量')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return self._save_plot(fig, filename, subdir="overall") # subdir="overall"
        except Exception:
            return None

    # 全期間熱門 Tags 圖 (Word Cloud)
    def plot_overall_wordcloud(self):
        try:
            all_tag_counts = self.data['content_insights']['all_tag_counts']
            if not all_tag_counts: return None

            text = " ".join([tag] * count for tag, count in all_tag_counts.items())
            
            filename = "overall_word_cloud.png"
            title = "全期間熱門主題詞雲"

            wordcloud = WordCloud(
                width=800, height=400, background_color='white', font_path=plt.rcParams['font.sans-serif'][0]
            ).generate(text)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.set_title(title, fontsize=16)
            ax.axis('off')
            plt.tight_layout()

            return self._save_plot(fig, filename, subdir="overall") # subdir="overall"
        except Exception:
            return None


    # --- 主要報告生成器 ---

    def generate_all_reports(self):
        """主函數：執行所有圖表生成並返回檔案路徑字典。"""
        
        # 檢查是否有分析數據或輸出配置
        if self.data is None or not self.output_map:
            return {"weekly": {}, "monthly": {}, "overall": {}}
            
        # 根據 output_map 判斷要運行哪種報告
        run_weekly = "Weekly Report" in self.output_map
        run_monthly = "Monthly Report" in self.output_map

        print("\n1. Weekly 圖表生成 (7天數據)")
        weekly_files = {}
        if run_weekly:
            weekly_files["daily_post_count"] = self.plot_daily_post_count('7d') 
            weekly_files["top_tags"] = self.plot_top_tags(limit=10)
            weekly_files["top_authors"] = self.plot_top_authors('7d', limit=5)
            weekly_files["daily_tags_stacked_bar"] = self.plot_daily_tags_stacked_bar('7d', top_n=5)
            weekly_files["author_heatmap"] = self.plot_weekly_author_heatmap(top_n=5)
            weekly_files["tag_trend"] = self.plot_weekly_tag_trend(top_n=5)
            weekly_files["word_count_histogram"] = self.plot_word_count_histogram('7d')
        else:
            print("ℹ️ 未配置週報輸出路徑，跳過週報圖表生成。")
        
        print("2. Monthly/Overall 圖表生成 (30天/全期間數據)")
        monthly_files = {}
        overall_files = {}
        if run_monthly:
            monthly_files["daily_post_count"] = self.plot_daily_post_count('30d') 
            monthly_files["tag_trend"] = self.plot_monthly_tag_trend('30d', top_n=10)
            monthly_files["top_authors"] = self.plot_top_authors('30d', limit=10)
            monthly_files["daily_tags_stacked_bar"] = self.plot_daily_tags_stacked_bar('30d', top_n=10)
            monthly_files["tag_heatmap"] = self.plot_monthly_tag_heatmap(top_n=10)
            monthly_files["word_count_histogram"] = self.plot_word_count_histogram('30d') 
            
            # Overall charts are part of the Monthly Report package
            overall_files["overall_monthly_post_count"] = self.plot_overall_monthly_post_count()
            overall_files["overall_word_cloud"] = self.plot_overall_wordcloud()
        else:
            print("ℹ️ 未配置月報輸出路徑，跳過月報/總體圖表生成。")

        
        report_charts = {
            "weekly": {k: v for k, v in weekly_files.items() if v},
            "monthly": {k: v for k, v in monthly_files.items() if v},
            "overall": {k: v for k, v in overall_files.items() if v}, # 新增 overall 輸出
        }
        
        total_count = sum(len(d) for d in report_charts.values())
        print(f"--------------- 所有圖表生成完成 ---------------")
        print(f"總共生成 {total_count} 個圖表檔案，儲存於配置的目錄中。")
        
        return report_charts