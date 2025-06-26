import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """应用配置"""
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    
    # 向量化配置
    VECTOR_DIMENSION: int = 768
    CHUNK_SIZE: int = 1000
    MIN_CHUNK_LENGTH: int = 50
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://fia-ai.vercel.app",
        "*"  # 开发阶段允许所有来源
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.txt']
    
    # 其他配置
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"

# 创建全局设置实例
settings = Settings()

def get_temp_path() -> str:
    """获取临时文件路径"""
    return "/tmp" 