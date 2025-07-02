from data_processing.ollama_integration import Qwen3Model
import os
import json
import re
from config import Config


class QAEnhancer:
    def __init__(self):
        self.llm = Qwen3Model()
        self.enhanced_dir = os.path.join(Config.JSON_DIR, "enhanced")
        os.makedirs(self.enhanced_dir, exist_ok=True)

    def clean_text(self, text):
        """基础文本清洗"""
        if not text:
            return ""

        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s.,?;:!()\-—\'"@#$%&*+=/\\]', '', text)
        return text.strip()

    def categorize_question(self, question):
        """使用LLM对问题进行分类"""
        prompt = f"""
            # 指令
            你是一名金融专家，请对以下问题进行主题分类。
            你的回答必须只包含类别名称，不要包含任何思考过程、解释或额外文本。

            # 问题
            "{question}"

            # 类别选项
            [股票分析, 公司财报, 投资策略, 经济政策, 行业趋势, 交易规则, 金融产品, 风险管理, 其他]

            # 输出要求
            只需返回类别名称，不要添加任何其他内容。
            """

        response = self.llm.generate_response(prompt, max_tokens=8192)
        return response.strip()

    def enhance_qa(self, qa_item):
        """增强单条QA数据"""
        # 基础清洗
        cleaned_question = self.clean_text(qa_item.get("question", ""))
        cleaned_answer = self.clean_text(qa_item.get("answer", ""))

        if not cleaned_question:
            return None

        # 分类
        category = self.categorize_question(cleaned_question)

        # 评估质量
        quality = "high"
        if len(cleaned_question) < 5:
            quality = "low"

        return {
            "id": qa_item.get("id", ""),
            "question": cleaned_question,
            "answer": cleaned_answer,
            "category": category,
            "quality": quality,
            "source": "sseinfo.com",
            "timestamp": qa_item.get("timestamp", "")
        }

    def process_file(self, file_path):
        """处理单个JSON文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        enhanced_data = []
        for item in data:
            enhanced_item = self.enhance_qa(item)
            if enhanced_item:
                enhanced_data.append(enhanced_item)

        # 保存增强后的数据
        base_name = os.path.basename(file_path)
        output_path = os.path.join(self.enhanced_dir, f"enhanced_{base_name}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)

        return len(enhanced_data)

    def run(self):
        """处理所有JSON文件"""
        total_enhanced = 0

        for file_name in os.listdir(Config.JSON_DIR):
            if file_name.endswith(".json") and "enhanced" not in file_name:
                file_path = os.path.join(Config.JSON_DIR, file_name)
                print(f"处理文件: {file_name}")

                count = self.process_file(file_path)
                total_enhanced += count
                print(f"增强 {count} 条问答")

        print(f"处理完成，共增强 {total_enhanced} 条问答数据")

if __name__ == "__main__":
    enhancer = QAEnhancer()
    enhancer.run()