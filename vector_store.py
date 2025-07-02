import faiss
import numpy as np
import requests
import json
from typing import List, Dict, Any
from tqdm import tqdm
from config import Config
import time
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
class OllamaEmbedder:
    """使用 Ollama API 生成嵌入向量"""

    def __init__(self, model_name: str = "qwen3:4b"):
        self.model_name = model_name
        self.dimension = self._get_embedding_dimension()

    def _get_embedding_dimension(self) -> int:
        """获取嵌入向量的维度"""
        test_text = "测试维度"
        embedding = self.get_embedding(test_text)
        return len(embedding)

    def get_embedding(self, text: str):
        if type(text)==dict:
            text = json.dumps(text)
        r = ollama.embeddings(model=self.model_name, prompt=text)
        return r['embedding']

    def get_embeddings_batch(self, texts: List[str], max_workers=8) -> List[List[float]]:
        embeddings = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.get_embedding, text): text for text in texts}
            for future in tqdm(as_completed(futures), total=len(texts), desc="生成嵌入向量"):
                embedding = future.result()
                embeddings.append(embedding)
        return embeddings


class VectorStore:
    """使用 Ollama 嵌入模型的向量存储"""

    def __init__(self, embed_model: str = "qwen3:4b"):
        self.embedder = OllamaEmbedder(embed_model)
        self.dimension = self.embedder.dimension
        self.index = None
        self.documents = []
        self.metadata = []

    def create_index(self):
        """创建或重置 FAISS 索引"""
        if self.index is not None:
            print("重置现有索引")
        self.index = faiss.IndexFlatL2(self.dimension)
        print(f"创建新索引，维度: {self.dimension}")

    def add_documents(self, docs: List[str], metadatas: List[Dict] = None):
        """添加文档到向量存储"""
        if metadatas is None:
            metadatas = [{}] * len(docs)

        if len(docs) != len(metadatas):
            raise ValueError("文档和元数据数量必须一致")

        # 生成嵌入向量
        embeddings = self.embedder.get_embeddings_batch(docs)
        embeddings_np = np.array(embeddings).astype('float32')

        # 初始化索引（如果尚未创建）
        if self.index is None:
            self.create_index()

        # 添加到索引
        self.index.add(embeddings_np)
        self.documents.extend(docs)
        self.metadata.extend(metadatas)
        print(f"添加 {len(docs)} 个文档，总文档数: {len(self.documents)}")

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """语义搜索"""
        if self.index is None or len(self.documents) == 0:
            return []

        # 获取查询嵌入
        query_embed = self.embedder.get_embedding(query)
        query_embed_np = np.array([query_embed]).astype('float32')

        # 执行搜索
        distances, indices = self.index.search(query_embed_np, k,)

        # 构建结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:  # FAISS 可能返回 -1
                continue

            results.append({
                "content": self.documents[idx],
                "metadata": self.metadata[idx],
                "distance": float(distances[0][i])
            })

        return results

    def save_index(self, file_path: str):
        """保存 FAISS 索引到文件"""
        if self.index is None:
            raise ValueError("索引未初始化")

        faiss.write_index(self.index, file_path)
        print(f"索引已保存到 {file_path}")

        # 保存文档和元数据
        data_file = file_path.replace(".faiss", ".json")
        with open(data_file, "w") as f:
            json.dump({
                "content": self.documents,
                "metadata": self.metadata
            }, f)
        print(f"文档元数据已保存到 {data_file}")

    def load_index(self, file_path: str):
        """从文件加载 FAISS 索引"""
        self.index = faiss.read_index(file_path)
        print(f"索引已从 {file_path} 加载")

        # 加载文档和元数据
        data_file = file_path.replace(".faiss", ".json")
        try:
            with open(data_file, "r") as f:
                data = json.load(f)
                self.documents = data["content"]
                self.metadata = data["metadata"]
            print(f"加载 {len(self.documents)} 个文档")
        except FileNotFoundError:
            print(f"警告: 未找到文档元数据文件 {data_file}")