from pathlib import Path

# 项目设置
PROJECT_NAME = "Taitoulv Backend"
API_V1_STR = "/api"

# CORS设置
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# 文件上传设置
UPLOAD_DIR = Path("uploads")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# 安全设置
SECRET_KEY = "your-secret-key-here"  # 在生产环境中应该使用环境变量
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 数据库设置
DATABASE_URL = "sqlite:///./sql_app.db"
