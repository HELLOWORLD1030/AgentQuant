"""
金融量化分析系统核心类
"""

import os
import json
from datetime import datetime
from app.models import AnalysisResult
from data_loader import DataLoader
from vector_store import VectorStore
from agents import RetrievalAgent, GenerationAgent, ConfidenceEvaluator, DialogueManager
from config import Config
from agentscope.message import Msg
class QuantAnalysisSystem:
    """金融量化分析系统主类"""

    def __init__(self):
        """
        初始化系统组件：
        1. 向量数据库
        2. 数据加载器
        3. 核心处理代理
        """
        # 初始化向量存储
        self.vector_store = VectorStore(embed_model=Config.EMB_MODEL)

        # 检查并加载向量索引
        self._setup_vector_store()

        # 初始化系统代理
        self._initialize_agents()

    def _setup_vector_store(self):
        """配置向量存储索引"""
        if os.path.exists(Config.VECTOR_STORE_PATH):
            print("加载现有金融知识库...")
            self.vector_store.load_index(Config.VECTOR_STORE_PATH)
        else:
            print("构建金融知识库索引...")
            self._build_vector_index()

    def _build_vector_index(self):
        """构建向量索引"""
        # 创建索引结构
        self.vector_store.create_index()

        # 加载数据文档
        loader = DataLoader()
        documents = loader.load_all_data()

        # 准备索引内容
        content_list = []
        metadata_list = []

        for doc in documents:
            content_list.append(doc["content"])
            metadata_list.append({
                "source": doc["metadata"].get("source", "未标注来源"),
                "date": doc["metadata"].get("date", "未知日期")
            })

        # 添加文档到索引
        self.vector_store.add_documents(content_list, metadata_list)

        # 保存索引
        self.vector_store.save_index(Config.VECTOR_STORE_PATH)
        print(f"金融知识库构建完成，包含 {len(content_list)} 条文档")

    def _initialize_agents(self):
        """初始化处理代理"""
        # 检索代理 - 负责知识检索
        self.retrieval_agent = RetrievalAgent(self.vector_store)

        # 生成代理 - 负责内容生成
        self.generation_agent = GenerationAgent(model_name=Config.QWEN_MODEL)

        # 置信度评估 - 负责答案质量评估
        self.confidence_evaluator = ConfidenceEvaluator()

        # 对话管理 - 协调处理流程
        self.dialogue_manager = DialogueManager(
            self.retrieval_agent,
            self.generation_agent
        )

    def analyze_query(self, user_query: str) -> AnalysisResult:
        """
        处理用户查询的完整分析流程

        参数:
            user_query: 用户查询文本

        返回:
            分析结果对象
        """
        # 步骤1: 对话管理处理用户输入
        manager_response = self.dialogue_manager.reply(
            Msg(role="user", content=user_query, name="quant")
        )

        # 步骤2: 置信度评估
        eval_msg = {
            "question": user_query,
            "content": manager_response["content"],
            "context": manager_response.get("context", [])
        }
        final_response = self.confidence_evaluator.reply(eval_msg)

        # 返回结构化分析结果
        return AnalysisResult(
            query=user_query,
            analysis=final_response["content"],
            confidence=final_response["confidence"],
            sources=manager_response.get("sources", []),
            evaluation=final_response.get("confidence_evaluation", ""),
            timestamp=datetime.now().isoformat()
        )

    def save_state(self):
        """保存系统状态"""
        state = {
            "last_updated": datetime.now().isoformat(),
            "vector_store_path": Config.VECTOR_STORE_PATH,
            "document_count": len(self.vector_store.documents)
        }

        with open(Config.SYSTEM_STATE_PATH, "w") as f:
            json.dump(state, f)
        print(f"系统状态已保存到 {Config.SYSTEM_STATE_PATH}")

    def get_system_status(self):
        """获取系统状态"""
        try:
            with open(Config.SYSTEM_STATE_PATH, "r") as f:
                state = json.load(f)
            return {
                "status": "running",
                **state
            }
        except FileNotFoundError:
            return {
                "status": "initialized",
                "message": "系统尚未保存状态"
            }