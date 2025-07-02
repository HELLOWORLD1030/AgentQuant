"""
金融问答系统核心组件
实现基于检索增强生成（RAG）的金融问答流程
包含检索、生成、对话管理和置信度评估四个核心模块
"""

from agentscope.agents import AgentBase
import ollama
from typing import List, Dict, Any, Union
from config import Config  # 配置文件
from agentscope.message import Msg


class RetrievalAgent(AgentBase):
    """文档检索代理，负责从向量库中检索相关信息"""

    def __init__(self, vector_store: Any):
        """
        初始化检索代理

        参数:
            vector_store: 向量数据库实例，需实现search方法
        """
        super().__init__("retrieval_agent")
        self.vector_store = vector_store  # 向量数据库实例

    def reply(self, msg: Dict) -> Dict:
        """
        执行语义检索并返回相关文档

        参数:
            msg: 输入消息，需包含文本内容

        返回:
            包含检索结果的字典，包含上下文和原始文档信息
        """
        # 提取查询文本
        query = msg.get_text_content()

        # 执行向量数据库检索
        results = self.vector_store.search(
            query=query,
            k=10  # 返回前10个最相关结果
        )

        # 构建可读的上下文字符串
        context_parts = []
        for i, res in enumerate(results):
            source = res['metadata'].get('source', '未知来源')
            content = res['content']
            context_parts.append(f"来源 {i + 1} ({source}):\n{content}...")

        context = "\n\n".join(context_parts)

        # 返回结构化结果
        return {
            "role": "system",
            "name": self.name,
            "content": context,
            "context": results,  # 保留原始文档信息用于溯源
            "type": "retrieval",
            "query": query,  # 保留原始查询
        }


class GenerationAgent(AgentBase):
    """回答生成代理，基于检索结果生成专业回答"""

    def __init__(self, model_name: str = "qwen3:4b"):
        """
        初始化生成代理

        参数:
            model_name: Ollama模型名称，默认为qwen3:4b
        """
        super().__init__("generation_agent")
        self.model_name = model_name
        self.client = ollama.Client(host=Config.OLLAMA_HOST)

        # 系统提示词 - 定义回答格式和要求
        self.system_prompt = """
        作为金融分析师，请根据提供的上下文回答问题：
        1. 确保答案准确专业
        2. 标注信息来源
        3. 评估答案置信度
        4. 保持回答简洁

        回答格式：
        [分析]: <详细分析>
        [来源]: <引用来源>
        [置信度]: <高/中/低>
        """

    def format_prompt(self, context: str, question: str) -> List[Dict]:
        """
        构建LLM提示消息

        参数:
            context: 检索得到的上下文
            question: 用户问题

        返回:
            格式化后的消息列表
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"上下文:\n{context}\n\n问题: {question}"}
        ]

    def extract_confidence(self, response: str) -> str:
        """
        从生成响应中提取置信度

        参数:
            response: LLM生成的完整响应文本

        返回:
            置信度等级: "高", "中", "低"
        """
        # 默认置信度为低
        confidence = "低"

        # 检查响应中是否包含置信度标记
        if "[置信度]: 高" in response:
            confidence = "高"
        elif "[置信度]: 中" in response:
            confidence = "中"

        return confidence

    def extract_sources(self, response: str, context: List) -> List[str]:
        """
        从生成响应中提取并验证信息来源

        参数:
            response: LLM生成的完整响应文本
            context: 检索得到的原始文档列表

        返回:
            有效来源列表
        """
        sources = []

        # 尝试提取来源部分
        if "[来源]:" in response:
            source_text = response.split("[来源]:")[1]
            # 取第一个换行符前的内容
            source_line = source_text.split("\n")[0].strip()
            sources = [s.strip() for s in source_line.split(",")]

        # 获取上下文中所有有效来源
        context_sources = [res['metadata'].get('source', '') for res in context]

        # 验证来源是否在上下文中存在
        valid_sources = [
            src for src in sources
            if src and src in context_sources
        ]

        # 如果没有有效来源，使用上下文中的前三个来源
        if not valid_sources and context_sources:
            valid_sources = list(set(context_sources))[:10]

        return valid_sources

    def reply(self, msg: Dict) -> Dict:
        """
        基于检索结果生成回答

        参数:
            msg: 包含检索结果的消息

        返回:
            生成的回答消息
        """
        # 提取检索结果
        context = msg.get("content", "")
        context_data = msg.get("context", [])
        question = msg.get("query", "")

        # 构建提示
        messages = self.format_prompt(context, question)

        # 调用模型API生成回答
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "num_predict": Config.MAX_TOKEN,  # 减少token数量
                    "temperature": 0.3
                }
            )
            content = response["message"]["content"]
        except Exception as e:
            content = f"生成回答时出错: {str(e)}"

        # 确保回答格式正确
        if "[分析]:" not in content:
            content = f"[分析]: {content}"

        # 提取结构化信息
        confidence = self.extract_confidence(content)
        sources = self.extract_sources(content, context_data)

        # 返回结构化回答
        return {
            "role": "assistant",
            "name": self.name,
            "content": content,
            "confidence": confidence,
            "sources": sources,
            "context": context_data  # 保留上下文用于后续评估
        }


class DialogueManager(AgentBase):
    """对话管理代理，协调检索和生成流程"""

    def __init__(self, retrieval_agent: RetrievalAgent, generation_agent: GenerationAgent):
        """
        初始化对话管理器

        参数:
            retrieval_agent: 检索代理实例
            generation_agent: 生成代理实例
        """
        super().__init__("dialogue_manager")
        self.retrieval_agent = retrieval_agent
        self.generation_agent = generation_agent
        self.history = []  # 对话历史记录

    def reply(self, msg: Union[Dict, Msg]) -> Dict:
        """
        处理用户输入，协调检索和生成流程

        参数:
            msg: 用户输入消息

        返回:
            系统生成的回答
        """
        # 更新对话历史
        self.history.append(msg)

        # 执行检索
        retrieval_result = self.retrieval_agent(msg)

        # 准备生成请求
        generation_msg = {
            "content": retrieval_result["content"],
            "context": retrieval_result.get("context", []),
            "query": msg.get_text_content(),  # 原始问题
            "history": self.history[-5:]  # 最近5条历史记录
        }

        # 生成回答
        response = self.generation_agent(generation_msg)

        # 更新历史
        self.history.append(response)

        return response


class ConfidenceEvaluator(AgentBase):
    """置信度评估代理，对生成答案进行质量评估"""

    def __init__(self, model_name: str = "qwen3:4b"):
        """
        初始化置信度评估器

        参数:
            model_name: 评估使用的模型名称
        """
        super().__init__("confidence_evaluator")
        self.client = ollama.Client(host=Config.OLLAMA_HOST)
        self.model_name = model_name

    def evaluate_confidence(self, question: str, answer: str, context: List) -> str:
        """
        评估回答的质量和置信度

        参数:
            question: 原始问题
            answer: 生成的回答
            context: 检索得到的原始文档

        返回:
            评估结果文本
        """
        # 提取来源信息
        sources = {res['metadata'].get('source', '未知') for res in context}

        # 构建评估提示
        prompt = f"""
        作为金融质量评估专家，请评估以下回答：

        问题: {question}
        回答: {answer}
        信息来源: {', '.join(sources)}

        评估标准：
        1. 回答与问题的相关性
        2. 回答与信息的一致性
        3. 回答的专业性和完整性

        评估结果格式：
        [逻辑一致性]: <高/中/低>
        [来源可靠性]: <高/中/低>
        [综合置信度]: <高/中/低>
        """

        # 调用模型进行评估
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 512}
            )
            return response["message"]["content"]
        except Exception as e:
            return f"评估失败: {str(e)}"

    def extract_confidence_level(self, evaluation: str) -> str:
        """
        从评估文本中提取综合置信度

        参数:
            evaluation: 评估结果文本

        返回:
            置信度等级: "高", "中", "低"
        """
        # 默认置信度为中
        confidence = "中"

        # 检查评估文本中的置信度标记
        if "[综合置信度]: 高" in evaluation:
            confidence = "高"
        elif "[综合置信度]: 低" in evaluation:
            confidence = "低"

        return confidence

    def reply(self, msg: Dict) -> Dict:
        """
        执行置信度评估

        参数:
            msg: 包含问题和回答的消息

        返回:
            包含评估结果的消息
        """
        # 提取评估所需信息
        question = msg.get("query", "")
        answer = msg.get("content", "")
        context = msg.get("context", [])

        # 执行评估
        evaluation = self.evaluate_confidence(question, answer, context)

        # 提取置信度等级
        confidence = self.extract_confidence_level(evaluation)

        # 更新消息
        msg["confidence_evaluation"] = evaluation
        msg["confidence"] = confidence

        return msg