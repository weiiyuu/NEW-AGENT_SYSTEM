import pandas as pd
from typing import Dict, Any
from datetime import timedelta, datetime

class AnalyzerAgent:
    """
    根據完整的 Master DataFrame 進行全面統計分析，
    輸出結構化 JSON 報告供下游 n8n/AI Agent 使用。
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = {}

    def _preprocess_data(self):
        """
        為分析準備數據：確保日期格式正確、計算內容長度、合併標籤。
        """
        if self.df.empty:
            print("AnalyzerAgent 警告: 輸入數據為空，無法進行分析。")
            return

        # 1. 確保 'date' 欄位為 datetime 物件
        self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
        self.df.dropna(subset=['date'], inplace=True)

        # 2. 計算內容長度
        self.df['content_length'] = self.df['content'].apply(lambda x: len(str(x)))

        # 3. 合併標籤
        def combine_tags(row):
            all_tags = set(row['tags_start'] or [])
            all_tags.update(row['tags_end'] or [])
            return list(all_tags)

        self.df['all_tags'] = self.df.apply(combine_tags, axis=1)

        print(f"AnalyzerAgent: 數據預處理完成 ({len(self.df)} 筆有效數據)")


    def analyze_time_series(self) -> Dict[str, Any]:
        """ 分析發文量的時間分佈。 """
        if self.df.empty: return {}

        time_data = {}

        # 月度發文量 (修正: 使用 'ME' 避免 FutureWarning)
        monthly_counts = self.df.set_index('date').resample('ME').size()
        monthly_counts.index = monthly_counts.index.strftime('%Y-%m-%d')
        time_data['monthly_post_count'] = monthly_counts.rename("count").to_dict()

        # 週日發文量
        weekday_counts = self.df['date'].dt.day_name().value_counts().to_dict()
        time_data['weekday_post_count'] = weekday_counts

        return time_data


    def analyze_tags_and_content(self) -> Dict[str, Any]:
        """ 分析內容熱點和深度。 """
        if self.df.empty: return {}

        content_data = {}

        # 內容長度統計
        content_data['content_length_stats'] = {
            'average': self.df['content_length'].mean(),
            'median': self.df['content_length'].median(),
            'min': self.df['content_length'].min(),
            'max': self.df['content_length'].max(),
        }

        all_tags = self.df['all_tags'].explode().dropna()

        # 頂級標籤 (Top 10)
        content_data['top_tags'] = all_tags.value_counts().head(10).to_dict()

        # ⭐ 新增: 全期間標籤計數 (用於 WordCloud)
        content_data['all_tag_counts'] = all_tags.value_counts().to_dict()

        return content_data


    def analyze_author_insights(self) -> Dict[str, Any]:
        """ 分析作者的貢獻與風格。 """
        if self.df.empty: return {}

        author_data = {}

        # 貢獻度最高的作者 (Top 5)
        author_data['top_authors_by_post_count'] = self.df['author'].value_counts().head(5).to_dict()

        # 平均文章長度最高的作者 (至少發文 3 篇)
        author_data['top_authors_by_avg_content_length'] = (
            self.df.groupby('author')['content_length']
            .agg(['count', 'mean'])
            .rename(columns={'mean': 'avg_length'})
            .query('count >= 3')
            .sort_values('avg_length', ascending=False)
            .head(5)['avg_length']
            .to_dict()
        )

        return author_data


    def analyze_period_insights(self) -> Dict[str, Any]:
        """ 最近 7/30 天分析 及 全期間月度發文量 (all_time) """
        if self.df.empty: return {}

        period_data = {}

        if self.df['date'].max() is pd.NaT:
            return {}

        latest_date = self.df['date'].max()

        def get_period_stats(days: int):
            start_date = latest_date - timedelta(days=days)
            df_period = self.df[self.df['date'] > start_date].copy()

            if df_period.empty:
                return {
                    'total_post_count': 0,
                    # 修正: ReporterAgent 期待這些鍵名
                    'tag_counts': {},
                    'author_counts': {},
                    'daily_breakdown': {}
                }

            period_tags = df_period['all_tags'].explode().dropna()
            
            # 修正: 返回全部計數
            total_tag_counts = period_tags.value_counts().to_dict()
            total_author_counts = df_period['author'].value_counts().to_dict()

            daily_breakdown = {}

            for day_str, df_day in df_period.groupby(df_period['date'].dt.strftime('%Y-%m-%d')):
                daily_tags = df_day['all_tags'].explode().dropna()
                daily_breakdown[day_str] = {
                    'post_count': len(df_day),
                    # 修正: 統一鍵名為 tags_count
                    'tags_count': daily_tags.value_counts().to_dict(),
                    # 修正: 統一鍵名為 author_counts
                    'author_counts': df_day['author'].value_counts().to_dict(),
                }

            return {
                'total_post_count': len(df_period),
                # 修正: 統一鍵名為 tag_counts (供 ReporterAgent 讀取)
                'tag_counts': total_tag_counts,
                # 修正: 統一鍵名為 author_counts (供 ReporterAgent 讀取)
                'author_counts': total_author_counts,
                'daily_breakdown': daily_breakdown
            }

        period_data['last_7_days'] = get_period_stats(7)
        period_data['last_30_days'] = get_period_stats(30)
        
        # --- 新增處理 'all_time' 數據的邏輯 ---

        # 1. 計算月度發文統計（全期間） (修正: 使用 'ME' 避免 FutureWarning)
        monthly_df_agg = self.df.set_index('date').resample('ME').agg(
            # 修正: 使用健壯的 lambda 函數處理 all_tags
            tags_list=('all_tags', lambda x: [tag for sublist in x if isinstance(sublist, list) for tag in sublist]),
            authors_list=('author', lambda x: x.tolist())
        )
        
        # 修正: 安全地計算文章總數，避免 KeyError: ['id']
        monthly_post_counts = self.df.set_index('date').resample('ME').size().rename('total_post_count')
        
        monthly_df = monthly_df_agg.join(monthly_post_counts).dropna(subset=['total_post_count']).astype({'total_post_count': int})

        monthly_breakdown = {}
        for idx, row in monthly_df.iterrows():
            date_key = idx.strftime('%Y-%m') # 月度 key
            monthly_breakdown[date_key] = {
                'total_post_count': row['total_post_count'],
                'tags_count': pd.Series(row['tags_list']).value_counts().to_dict(), 
                'author_counts': pd.Series(row['authors_list']).value_counts().to_dict(),
            }

        # 2. 將結果放入 'all_time' 鍵中，以滿足 ReporterAgent 期望的結構
        period_data['all_time'] = {
            'monthly_breakdown': monthly_breakdown,
            # 全期間總標籤計數
            'tag_counts': self.df['all_tags'].explode().dropna().value_counts().to_dict(), 
            # 確保 daily_breakdown 存在（即使為空），避免 ReporterAgent 讀取時報錯
            'daily_breakdown': {} 
        }

        return period_data


    # -------------------------------
    # ⭐ 新增：tag 時間序列分析（最小幅度新增）
    # -------------------------------
    def analyze_tag_time_series(self) -> Dict[str, Any]:
        """
        為每一個 tag 建立：
        - 月度出現次數
        - 每日出現次數
        """
        if self.df.empty:
            return {}

        tag_ts = {}

        df_expanded = (
            self.df[['date', 'all_tags']]
            .explode('all_tags')
            .dropna(subset=['all_tags'])
        )

        # 月度統計 (修正: to_period 必須使用 'M', 否則會報 ValueError)
        df_expanded['month'] = df_expanded['date'].dt.to_period('M').dt.to_timestamp()

        monthly = (
            df_expanded.groupby(['all_tags', 'month'])
            .size()
            .reset_index(name='count')
        )

        # 轉成 { tag: { "2025-11": N, ... } }
        tag_month_data = {}
        for tag, group in monthly.groupby('all_tags'):
            tag_month_data[tag] = {
                row['month'].strftime('%Y-%m'): int(row['count'])
                for _, row in group.iterrows()
            }

        # 每日統計
        df_expanded['day'] = df_expanded['date'].dt.strftime('%Y-%m-%d')

        daily = (
            df_expanded.groupby(['all_tags', 'day'])
            .size()
            .reset_index(name='count')
        )

        tag_day_data = {}
        for tag, group in daily.groupby('all_tags'):
            tag_day_data[tag] = {
                row['day']: int(row['count'])
                for _, row in group.iterrows()
            }

        return {
            "monthly_tag_trend": tag_month_data,
            "daily_tag_trend": tag_day_data
        }


    def run(self, df):
        """ 執行所有分析步驟並彙整結果。 """
        self.df = df
        self._preprocess_data()

        if self.df.empty:
            return {"error": "分析數據集為空。"}

        self.results['time_series'] = self.analyze_time_series()
        self.results['content_insights'] = self.analyze_tags_and_content()
        self.results['author_insights'] = self.analyze_author_insights()
        self.results['period_insights'] = self.analyze_period_insights()

        # ⭐ 新增 tag 相關的時序數據
        self.results['tag_time_series'] = self.analyze_tag_time_series()

        return self.results