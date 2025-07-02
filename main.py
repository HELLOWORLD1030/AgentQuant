"""
金融量化分析系统
集成知识检索与智能问答功能，支持专业金融分析
"""

import os
from agentscope.pipelines import SequentialPipeline
from agentscope.message import Msg
from data_loader import DataLoader
from vector_store import VectorStore
from agents import RetrievalAgent, GenerationAgent, ConfidenceEvaluator, DialogueManager
from config import Config


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

    def analyze_query(self, user_query: str) -> dict:
        """
        处理用户查询的完整分析流程

        参数:
            user_query: 用户查询文本

        返回:
            分析结果字典
        """
        # 步骤1: 对话管理处理用户输入
        manager_response = self.dialogue_manager.reply(
            Msg(role="user", content=user_query,name="quant")
        )

        # 步骤2: 置信度评估
        eval_msg = {
            "question": user_query,
            "content": manager_response["content"],
            "context": manager_response.get("context", [])
        }
        final_response = self.confidence_evaluator.reply(eval_msg)

        # 返回结构化分析结果
        return {
            "analysis": final_response["content"],
            "confidence": final_response["confidence"],
            "sources": manager_response.get("sources", []),
            "evaluation": final_response.get("confidence_evaluation", "")
        }

    def run(self):
        """启动系统交互界面"""
        print("金融量化分析系统已启动")
        print("输入'退出'结束分析会话\n")

        session_history = []

        while True:
            try:
                # 获取用户输入
                user_input = input("分析查询: ")
                # user_input = "你觉得哪家公司未来发展最好"
                # 退出条件
                if user_input.lower() in ["退出", "exit", "quit"]:
                    print("分析会话结束")
                    break

                # 空输入处理
                if not user_input.strip():
                    print("请输入有效查询")
                    continue

                # 执行分析流程
                result = self.analyze_query(user_input)

                # 记录会话历史
                session_history.append({
                    "query": user_input,
                    "response": result
                })

                # 显示分析结果
                self._display_results(result)

            except KeyboardInterrupt:
                print("\n会话终止")
                break
            except Exception as e:
                print(f"分析错误: {str(e)}")
                # 记录错误信息
                session_history.append({
                    "query": user_input,
                    "error": str(e)
                })

    def _display_results(self, result: dict):
        """格式化显示分析结果"""
        print("\n分析报告:")
        print("-" * 60)

        # 显示核心分析内容
        print(result["analysis"])

        # 显示元数据信息
        print("\n报告元数据:")
        print(f"置信度: {result['confidence']}")

        if result["sources"]:
            print(f"信息来源: {', '.join(result['sources'])}")
        else:
            print("信息来源: 未标注")

        print("-" * 60)


if __name__ == "__main__":
    analysis_system = QuantAnalysisSystem()
    analysis_system.run()