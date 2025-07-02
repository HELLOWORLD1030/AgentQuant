import os
import json
# import pdfplumber
from multiprocessing import Pool
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import Config
import fitz


class DataLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

    def _process_pdf(self, filename):
        """处理单个PDF文件"""
        if filename.endswith(".pdf"):
            file_path = os.path.join(Config.PDF_DIR, filename)
            try:
                with fitz.open(file_path) as pdf:
                    text = "\n".join(page.get_text() for page in pdf)

                    metadata = {
                        "source": filename,
                        "type": "pdf",
                        "page_count": len(pdf)
                    }

                    # 分割文本
                    chunks = self.text_splitter.split_text(text)
                    return [{"content": chunk, "metadata": metadata} for chunk in chunks]
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        return []

    def _process_json(self, filename):
        """处理单个JSON文件"""
        if filename.endswith(".json"):
            file_path = os.path.join(Config.JSON_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                result = []
                content_list =[]
                metadata_list=[]
                for item in data:
                    content = f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
                    metadata = {
                        "source": filename,
                        "type": "json",
                        "question_id": item.get("id", "")
                    }
                    # content_list.append(content)
                    # metadata_list.append(metadata)
                    result.append({"content": content, "metadata": metadata})
                return result
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        return []

    def load_pdfs(self):
        """并行加载PDF文档"""
        files = [f for f in os.listdir(Config.PDF_DIR) if f.endswith(".pdf")]

        with Pool(processes=min(4, os.cpu_count())) as pool:  # 限制进程数
            results = list(tqdm(
                pool.imap(self._process_pdf, files),
                total=len(files),
                desc="处理PDF文件"
            ))

        return [item for sublist in results for item in sublist]

    def load_jsons(self):
        """并行加载JSON文档"""
        files = [f for f in os.listdir(Config.JSON_DIR) if f.endswith(".json")]

        with Pool(processes=min(4, os.cpu_count())) as pool:
            results = list(tqdm(
                pool.imap(self._process_json, files),
                total=len(files),
                desc="处理JSON文件"
            ))

        return [item for sublist in results for item in sublist]

    def load_all_data(self):
        """加载所有数据"""
        pdf_data = self.load_pdfs()
        json_data = self.load_jsons()
        return pdf_data + json_data


if __name__ == "__main__":
    loader = DataLoader()
    data = loader.load_all_data()
    print(f"Loaded {len(data)} items")