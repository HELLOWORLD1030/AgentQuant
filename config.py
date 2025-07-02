import os
from dotenv import load_dotenv

from pathlib import Path

# 加载环境变量
load_dotenv()

# 获取项目根目录路径




class Config:
    PROJECT_ROOT = Path(__file__).resolve().parent
    EMB_MODEL = "nomic-embed-text"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    QWEN_MODEL = "qwen3:4b"

    # 数据路径
    PDF_DIR = os.path.join(str(PROJECT_ROOT),"data/pdfs")
    JSON_DIR = os.path.join(str(PROJECT_ROOT),"data/jsons")

    # FAISS索引路径
    VECTOR_STORE_PATH = "vector_store.faiss"

    # 文本分块配置
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_TOKEN = 16384
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    # CORS 配置
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    # 数据更新配置
    DATA_UPDATE_INTERVAL = int(os.getenv("DATA_UPDATE_INTERVAL", 1440))


