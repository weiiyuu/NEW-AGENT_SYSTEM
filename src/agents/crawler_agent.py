import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class CrawlerAgent:
    def __init__(self, target_count=3):
        self.url = "https://abmedia.io/blog"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.target_count = target_count

    def parse_articles(self, section):
        articles = []

        for art in section.find_all("article"):
            title_tag = art.select_one("h3.title a")
            title = title_tag.get_text(strip=True) if title_tag else "無標題"
            link = title_tag["href"] if title_tag else None

            if not link:
                continue

            # 文章內頁
            res_article = requests.get(link, headers=self.headers)
            soup_article = BeautifulSoup(res_article.text, "html.parser")

            # 作者
            author_tag = soup_article.select_one("address a")
            author = author_tag.get_text(strip=True) if author_tag else "未知"

            # 日期
            time_tag = soup_article.select_one("time")
            date = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

            # tags_start 必須在任何 HTML 分解操作前擷取
            tags_start = []
            tag_start_section = soup_article.select_one("header .cat")
            if tag_start_section:
                for a in tag_start_section.select("a"):
                    txt = a.get_text(strip=True)
                    if txt:
                        tags_start.append(txt)

            # tags_end 必須在任何 HTML 分解操作前擷取 (此元素即將在內容清理階段被移除)
            tags_end = []
            tag_end_section = soup_article.select_one(".exts .cat")
            if tag_end_section:
                for a in tag_end_section.select("a"):
                    txt = a.get_text(strip=True)
                    if txt:
                        tags_end.append(txt)

            # 內容提取與清理
            content_tag = soup_article.select_one("div.desc")
            content = "無內容"

            if content_tag:
                # ====== [新增] 在 HTML 階段移除雜訊區塊 ======
                
                # 1. 移除文章小標題列表 (Table of Contents) - 使用 ID
                if toc_section := content_tag.select_one("div#ez-toc-container"):
                    toc_section.decompose()
                
                # 2. 移除風險提示區塊 - 使用 Class
                if risk_note_section := content_tag.select_one("div.post-note"):
                    risk_note_section.decompose()

                # 3. 移除內文中的廣告區塊 (例如包含「廣告 - 內文未完」的區塊)
                # 判斷其父層 div.abmed- 是更穩定的選擇器
                if inline_ad_section := content_tag.select_one("div.abmed-"):
                    inline_ad_section.decompose()
                
                # 4. 移除文章末尾的 Tags, 廣告, 衍伸閱讀區塊 (.exts)
                # 註：此處移除是為了清理 'content'，tags_end 已經在前面擷取完成。
                if exts_section := content_tag.select_one("div.exts"):
                    exts_section.decompose()
                
                # 在清理完結構性雜訊後，再提取純文字
                # 這裡提取的文字將不包含 TOC, 風險提示, 內嵌廣告和結尾區塊的內容
                content = content_tag.get_text(separator="\n", strip=True)
                # ============================================

            articles.append({
                "title": title,
                "link": link,
                "author": author,
                "date": date,
                "tags_start": tags_start,
                "tags_end": tags_end,
                "content": content,
            })

        return articles

    def run(self):
        """
        真爬蟲模式，抓取文章但不做去重或文字清理
        """
        all_articles = []
        page = 1

        while len(all_articles) < self.target_count:
            next_url = self.url if page == 1 else f"{self.url}/page/{page}/"
            print(f"\n🔎 正在爬第 {page} 頁: {next_url}")

            res_page = requests.get(next_url, headers=self.headers)
            if res_page.status_code != 200:
                print(f"❌ 第 {page} 頁無法取得資料，停止爬蟲。")
                break

            soup_page = BeautifulSoup(res_page.text, "html.parser")
            page_articles = []

            for section_class in [".loop-grid", ".loop-post"]:
                section = soup_page.select_one(section_class)
                if section:
                    page_articles += self.parse_articles(section)

            print(f"📄 第 {page} 頁抓到 {len(page_articles)} 篇文章")

            all_articles += page_articles
            print(f"📦 目前累積: {len(all_articles)} / {self.target_count}")

            if not page_articles:
                print("⚠️ 沒有更多文章，提前結束")
                break

            page += 1

        all_articles = all_articles[:self.target_count]
        print(f"\n✅ 爬蟲完成，共取得 {len(all_articles)} 篇文章\n")
        return pd.DataFrame(all_articles)