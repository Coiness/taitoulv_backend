from fastapi import APIRouter, WebSocket, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import shutil
import cv2
import numpy as np
from app.core.config import settings
from app.services.yolo_service_new import yolo_service
from app.core.database import get_db
from app.models.video import VideoSession, VideoAnalysis
from sqlalchemy.orm import Session
from app.api.auth.routes import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.websocket("/stream")
async def video_stream(websocket: WebSocket):
    """处理实时视频流"""
    await websocket.accept()
    try:
        # 创建新的视频会话
        session_start = datetime.utcnow()
        session_id = None  # TODO: 保存会话ID到数据库
        
        total_head_up_rate = 0
        frame_count = 0
        
        while True:
            # 接收视频帧数据
            frame_data = await websocket.receive_bytes()
            
            # 将字节数据转换为OpenCV格式
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 处理视频帧
            result = await yolo_service.process_frame(frame)
            
            # 更新统计信息
            total_head_up_rate += result["head_up_rate"]
            frame_count += 1
            
            # 返回检测结果
            await websocket.send_json({
                "timestamp": result["timestamp"],
                "detections": result["detections"],
                "head_up_rate": result["head_up_rate"],
                "visualization": result["visualization"],  # 可视化图像的Base64编码
                "average_head_up_rate": total_head_up_rate / frame_count if frame_count > 0 else 0
            })
            
    except Exception as e:
        print(f"Error in video stream: {e}")
    finally:
        # 保存会话数据
        if session_id:
            session_end = datetime.utcnow()
            session_duration = (session_end - session_start).total_seconds()
            average_head_up_rate = total_head_up_rate / frame_count if frame_count > 0 else 0
            # TODO: 更新数据库中的会话信息
        await websocket.close()


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """处理上传的图片文件"""
    # 检查文件扩展名
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported types: jpg, jpeg, png"
        )
    
    # 检查文件大小
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE/1024/1024}MB"
        )
    
    # 创建用户专属的图片保存目录
    user_image_dir = settings.UPLOAD_DIR / str(current_user.id) / "images"
    user_image_dir.mkdir(exist_ok=True, parents=True)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = user_image_dir / unique_filename
    
    try:
        # 保存图片文件
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 处理图片
        result = await yolo_service.process_image(file_path)
        
        if result["status"] == "success":
            # 保存分析结果
            analysis = VideoAnalysis(
                user_id=current_user.id,
                timestamp=datetime.utcnow(),
                tilt_up_rate=result["head_up_rate"],
                is_attentive=result["head_up_rate"] > 0.5,  # 可根据需求调整阈值
                confidence=max([det["confidence"] for det in result["detections"]], default=0.0)
            )
            db.add(analysis)
            db.commit()
            
            return {
                "status": "success",
                "filename": unique_filename,
                "result": result
            }
            
    except Exception as e:
        # 如果处理失败，删除上传的文件
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )
    finally:
        file.file.close()

@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取用户的视频分析会话记录"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this user's sessions"
        )
    
    sessions = db.query(VideoSession).filter(VideoSession.user_id == user_id).all()
    return [{
        "id": session.id,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "average_head_up_rate": session.average_head_up_rate,
        "session_duration": session.session_duration
    } for session in sessions]
