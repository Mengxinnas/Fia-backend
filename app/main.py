from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from typing import Optional

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
    allow_origins=["*"],  # 生产环境中应该配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class QuestionRequest(BaseModel):
    text: str

class AnalysisRequest(BaseModel):
    analysis_type: str = "comprehensive"
    company_name: Optional[str] = None

# 初始化服务
from app.services.file_parser import FileParserService
from app.services.vector_service import vector_service
from app.services.qa_service import QAService
from app.services.financial_service import FinancialService

file_parser = FileParserService()
qa_service = QAService()
financial_service = FinancialService()

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

@app.get("/status")
async def get_status():
    """获取系统状态"""
    stats = vector_service.get_stats()
    return {
        "success": True,
        "stats": stats
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """文件上传接口"""
    try:
        # 检查文件类型
        allowed_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
        
        # 检查文件大小 (50MB)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # 解析文件
            text = await file_parser.extract_text(temp_path, file_ext)
            
            # 向量化存储
            doc_id = await vector_service.add_document(text, file.filename)
            
            return {
                "success": True,
                "message": "文件上传成功",
                "document_id": doc_id,
                "filename": file.filename,
                "text_length": len(text)
            }
            
        finally:
            # 清理临时文件
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.post("/api/qa/ask")
async def ask_question(request: QuestionRequest):
    """智能问答接口"""
    try:
        answer = await qa_service.answer_question(request.text)
        return {
            "success": True,
            "question": request.text,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")

@app.post("/api/financial-analysis")
async def financial_analysis(request: AnalysisRequest):
    """财务分析接口"""
    try:
        analysis = await financial_service.generate_analysis(
            analysis_type=request.analysis_type,
            company_name=request.company_name
        )
        return {
            "success": True,
            "analysis": analysis,
            "analysis_type": request.analysis_type,
            "company_name": request.company_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"财务分析失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 