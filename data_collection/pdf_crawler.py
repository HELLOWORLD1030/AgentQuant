import os
import requests
import time
import random
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config


class PDFCrawler:
    def __init__(self):
        self.base_url = "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&checkedCategory=category_ndbg_szsh#szse"
        self.download_dir = Config.PDF_DIR
        os.makedirs(self.download_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "http://www.cninfo.com.cn/"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_report_links(self, max_pages=10):
        """获取年报链接"""
        report_links = []
        page = 1

        while page <= max_pages and len(report_links) < 150:  # 目标150个
            print(f"正在处理第 {page} 页...")
            params = {
                "pageNum": page,
                "pageSize": 30,
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",
                "searchkey": "",
                "secid": "",
                "category": "category_ndbg_szsh",
                "trade": "",
                "seDate": "",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true"
            }

            try:
                response = self.session.post(
                    "http://www.cninfo.com.cn/new/hisAnnouncement/query",
                    params=params,
                    timeout=30
                )
                data = response.json()

                if data and "announcements" in data:
                    for item in data["announcements"]:
                        # if "年度报告" in item["announcementTitle"] and item["adjunctUrl"].endswith(".pdf"):
                            report_links.append({
                                "title": item["announcementTitle"],
                                "url": "http://static.cninfo.com.cn/" + item["adjunctUrl"],
                                "code": item["secCode"],
                                "name": item["secName"],
                                "date": item["announcementTime"] // 1000  # 转换为秒级时间戳
                            })
                else:
                    print(f"第 {page} 页未找到数据")

                page += 1
                time.sleep(random.uniform(1.0, 3.0))  # 随机延迟

            except Exception as e:
                print(f"获取第 {page} 页时出错: {str(e)}")
                break

        return report_links

    def download_pdf(self, report):
        """下载PDF文件"""
        try:
            file_name = f"{report['code']}_{report['date']}_{report['title'][:50]}.pdf"
            file_path = os.path.join(self.download_dir, file_name)

            # 检查文件是否已存在
            if os.path.exists(file_path):
                return False

            response = self.session.get(report["url"], stream=True, timeout=60)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"已下载: {file_name}")
                return True
            else:
                print(f"下载失败: {report['url']} - 状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"下载 {report['url']} 时出错: {str(e)}")
            return False

    def run(self, max_count=150):
        """运行爬虫"""
        print("开始获取年报链接...")
        reports = self.get_report_links()
        print(f"共获取到 {len(reports)} 份年报链接")

        downloaded = 0
        for report in reports:
            if downloaded >= max_count:
                break

            if self.download_pdf(report):
                downloaded += 1
                time.sleep(random.uniform(0.5, 2.0))  # 下载间隔

        print(f"下载完成，共下载 {downloaded} 份PDF年报")


if __name__ == "__main__":
    crawler = PDFCrawler()
    crawler.run()