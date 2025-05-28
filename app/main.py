from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.services.yolo_service import yolo_service
from app.api.auth.routes import router as auth_router
from app.api.auth.routes import public_router as auth_public_router
from app.api.video.routes import router as video_router

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="抬头率检测系统API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 路由配置
app.include_router(auth_public_router, prefix="/api/auth/public", tags=["auth_public"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(video_router, prefix="/api/video", tags=["video"])

# 测试连接端点
@app.get("/api/test")
async def test_connection():
    """测试后端连接是否正常"""
    return {
        "status": "ok",
        "message": "Backend connection successful",
        "version": "1.0.0"
    }

# 文件上传和处理
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 重置文件指针
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # 检查文件扩展名
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 创建上传目录
    upload_dir = settings.UPLOAD_DIR
    upload_dir.mkdir(exist_ok=True)
    
    # 保存文件
    file_path = upload_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    # 处理文件（图片或视频）
    is_video = file_ext in ['mp4', 'avi', 'mov']
    try:
        if is_video:
            result = await yolo_service.process_video(file_path)
        else:
            result = await yolo_service.process_image(file_path)
            
        return {
            "filename": file.filename,
            "status": "success",
            "result": result,
            "message": "File processed successfully"
        }
        
    except Exception as e:
        # 如果处理失败，删除上传的文件
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# 在启动时初始化
@app.on_event("startup")
async def startup_event():
    """服务启动时的初始化操作"""
    # 确保必要的目录存在
    for dir_path in ["uploads/videos", "uploads/images"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # TODO: 可以在这里添加其他初始化操作
    # 比如预加载YOLO5模型等
