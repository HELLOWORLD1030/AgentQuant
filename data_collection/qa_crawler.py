import os
import requests
import json
import time
import random
from bs4 import BeautifulSoup
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

class QACrawler:
    def __init__(self):
        self.base_url = "https://sns.sseinfo.com/ajax/feeds.do"
        self.download_dir = Config.JSON_DIR
        os.makedirs(self.download_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://sns.sseinfo.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_qa_data(self, page=1, per_page=20):
        """获取问答数据"""
        params = {
            "type": "10",
            "page": page,
            "lastid": -1,
            "show":1,
            "pageSize": per_page
        }

        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            if response.status_code == 200:
                # html_text = html.fromstring(response.content.decode('utf-8'))

                return response.content.decode('utf-8')
            else:
                print(f"获取第 {page} 页失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取第 {page} 页时出错: {str(e)}")
            return None

    def parse_qa_data(self, data):
        """解析问答数据"""

        qa_list = []
        soup = BeautifulSoup(data, "html.parser")
        items = soup.find_all("div", class_="m_feed_item")

        for item in items:
            try:
                # 解析问题
                question_div = item.find("div", class_="m_feed_txt")
                question = question_div.get_text(strip=True) if question_div else ""

                # 解析回答
                answer_div = item.find("div", class_="m_feed_reply")
                answer = answer_div.get_text(strip=True) if answer_div else ""

                # 解析元数据
                meta_div = item.find("div", class_="m_feed_from")
                # time_str = meta_div.find("span").get_text(strip=True) if meta_div else ""

                if question:
                    qa_list.append({
                        "question": question,
                        "answer": answer,
                    })

            except Exception as e:
                print(f"解析问答条目时出错: {str(e)}")
                continue

        return qa_list

    def save_to_json(self, data, page):
        """保存为JSON文件"""
        file_name = f"qa_page_{page}.json"
        file_path = os.path.join(self.download_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return file_path

    def run(self, max_pages=10, per_page=20):
        """运行爬虫"""
        all_qa = []

        for page in range(1, max_pages + 1):
            print(f"正在获取第 {page} 页问答数据...")
            raw_data = self.get_qa_data(page, per_page)

            if raw_data:
                qa_data = self.parse_qa_data(raw_data)
                if qa_data:
                    self.save_to_json(qa_data, page)
                    all_qa.extend(qa_data)
                    print(f"第 {page} 页获取到 {len(qa_data)} 条问答")
                else:
                    print(f"第 {page} 页未解析到有效问答")
            else:
                print(f"第 {page} 页获取失败")

            time.sleep(random.uniform(1.5, 3.0))  # 请求间隔

        print(f"爬取完成，共获取 {len(all_qa)} 条问答数据")
        return all_qa


if __name__ == "__main__":
    crawler = QACrawler()
    crawler.run(max_pages=20)