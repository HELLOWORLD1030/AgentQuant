import time

from data_processing.ollama_integration import Qwen3Model
import os
import json
from config import Config
from pypdf import PdfReader


class PDFEnhancer:
    def __init__(self):
        self.llm = Qwen3Model()
        self.metadata_file = os.path.join(Config.PDF_DIR, "metadata.json")
        self.metadata = self.load_metadata()

    def load_metadata(self):
        """加载现有的元数据"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def extract_basic_info(self, pdf_path):
        """提取PDF基本信息"""
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            if i < 3:  # 只读取前三页
                text += page.extract_text() + "\n"
        return text[:5000]  # 限制文本长度

    def generate_metadata(self, pdf_path, file_name):
        """使用LLM生成元数据"""
        # 检查是否已有元数据
        if file_name in self.metadata:
            return self.metadata[file_name]

        # 提取基础信息
        basic_text = self.extract_basic_info(pdf_path)

        # 构建LLM提示
        prompt = f"""
        你是一名金融分析师，请根据以下上市公司年报片段生成结构化元数据：

        {basic_text}

        请按以下JSON格式提供：
        {{
          "company_name": "公司全称",
          "stock_code": "股票代码",
          "report_year": "报告年份",
          "report_type": "年报类型（年度/半年度/季度）",
          "key_topics": ["主题1", "主题2", "主题3"],
          "summary": "报告摘要（100字以内）"
        }}
        """

        # 调用LLM生成元数据
        response = self.llm.generate_response(prompt, max_tokens=8192)

        try:
            # 尝试从响应中提取JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            json_str = response[start_idx:end_idx]
            metadata = json.loads(json_str)

            # 添加文件路径
            metadata["file_path"] = pdf_path
            self.metadata[file_name] = metadata
            self.save_metadata()

            return metadata
        except Exception as e:
            print(f"解析元数据失败: {str(e)}")
            return None

    def process_directory(self):
        """处理整个PDF目录"""
        for file_name in os.listdir(Config.PDF_DIR):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(Config.PDF_DIR, file_name)

                # 跳过已处理的文件
                if file_name in self.metadata:
                    continue

                print(f"处理文件: {file_name}")
                metadata = self.generate_metadata(pdf_path, file_name)

                if metadata:
                    print(f"生成元数据: {metadata['company_name']} {metadata['report_year']}")
                else:
                    print(f"无法为 {file_name} 生成元数据")

                time.sleep(1)  # 避免请求过快


if __name__ == "__main__":
    enhancer = PDFEnhancer()
    enhancer.process_directory()