"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class AnalysisResult(BaseModel):
    """分析结果模型"""
    query: str
    analysis: str
    confidence: str
    sources: List[str] = []
    evaluation: str = ""
    timestamp: str

class SystemStatus(BaseModel):
    """系统状态模型"""
    status: str
    last_updated: Optional[str] = None
    document_count: Optional[int] = None
    message: Optional[str] = None

class DataUpdateResponse(BaseModel):
    """数据更新响应模型"""
    status: str
    documents_added: int
    documents_removed: int
    total_documents: int
    time_elapsed: float