from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
import os

# 加载环境变量
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # 基础配置
    PROJECT_NAME: str = "抬头率检测系统"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./app.db"
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # WebSocket配置
    WS_URL: str = "ws://localhost:8000/ws"
    
    # 文件上传配置
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "mp4", "avi", "mov"]
    
    # YOLO5配置
    YOLO5_MODEL_PATH: str = os.getenv("YOLO5_MODEL_PATH", "app/models/best.pt")
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    # YOLOv8配置
    YOLO8_MODEL_PATH: str = os.getenv("YOLO8_MODEL_PATH", "app/models/yolov8_best.pt")
    YOLO8_CONFIDENCE_THRESHOLD: float = 0.4
    YOLO8_IOU_THRESHOLD: float = 0.45
    
    # 临时标记：是否启用YOLO处理（在模型准备好之前设为False）
    ENABLE_YOLO: bool = os.getenv("ENABLE_YOLO", "true").lower() == "true"
    
    class Config:
        case_sensitive = True

settings = Settings()
