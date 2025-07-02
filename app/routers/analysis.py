"""
分析相关路由
"""

from fastapi import APIRouter, Depends
from app.models import AnalysisRequest, AnalysisResult, SystemStatus
from app.dependencies import get_quant_system
from app.core.system import QuantAnalysisSystem

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult, summary="分析金融查询")
async def analyze_query(
        request: AnalysisRequest,
        quant_system: QuantAnalysisSystem = Depends(get_quant_system)
) -> AnalysisResult:
    """
    处理金融查询并返回分析结果

    参数:
    - query: 金融分析查询文本
    返回:
    - 包含分析结果、置信度、来源等信息的对象
    """
    return quant_system.analyze_query(request.query)


@router.get("/status", response_model=SystemStatus, summary="获取系统状态")
async def get_status(
        quant_system: QuantAnalysisSystem = Depends(get_quant_system)
) -> SystemStatus:
    """
    获取系统当前状态信息

    返回:
    - 系统状态、最后更新时间、文档数量等信息
    """
    return quant_system.get_system_status()