"""
金融量化分析系统 - FastAPI 后端入口
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analysis
from app.dependencies import get_quant_system
from config import Config

# 创建 FastAPI 应用
app = FastAPI(
    title="金融量化分析系统 API",
    description="基于检索增强生成（RAG）的专业金融分析系统",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "分析",
            "description": "金融查询分析相关接口",
        },
        {
            "name": "数据",
            "description": "数据管理相关接口",
        }
    ]
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(analysis.router, prefix="/api/v1", tags=["分析"])

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化系统"""
    quant_system = get_quant_system()
    print("金融量化分析系统初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    quant_system = get_quant_system()
    # 保存系统状态
    quant_system.save_state()
    print("系统状态已保存")

if  __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.API_PORT)