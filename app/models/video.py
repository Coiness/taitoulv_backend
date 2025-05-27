from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class VideoSession(Base):
    __tablename__ = "video_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    average_head_up_rate = Column(Float)
    session_duration = Column(Float)  # 以秒为单位
    
    # 关联关系
    user = relationship("User", back_populates="video_sessions")

class VideoAnalysis(Base):
    __tablename__ = "video_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tilt_up_rate = Column(Float)
    is_attentive = Column(Boolean)
    confidence = Column(Float)
    session_id = Column(Integer, index=True)  # 用于分组同一会话的分析结果
