from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, qa, financial
from app.config import settings
import uvicorn

# 创建FastAPI应用实例
app = FastAPI(
    title="Fia财务分析API",
    description="Fia金融智能助手后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router)
app.include_router(qa.router)
app.include_router(financial.router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Fia财务分析API服务运行中",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "fia-backend"}

# 兼容原有前端的status接口
@app.get("/status")
async def get_status():
    """获取系统状态"""
    from app.services.vector_service import vector_service
    stats = vector_service.get_stats()
    return {
        "success": True,
        "stats": stats
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 