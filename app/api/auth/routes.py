from fastapi import APIRouter, Depends, HTTPException, status,Form,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.config import settings
from app.services.auth import authenticate_user, create_access_token, get_password_hash,authenticate_user_by_email
from app.models.user import User

router = APIRouter()
public_router = APIRouter() # 公共路由，不需要身份验证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/public/login")

# 用户注册请求模型
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

# 添加用户身份验证函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """从token中获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的身份认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 从数据库获取用户
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@public_router.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    email: EmailStr = Form(...),
    db: Session = Depends(get_db)
):
    #emial会自动验证格式，如果格式不正确会抛出ValidationError
    # 检查用户是否已存在
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "注册成功"}

@public_router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")


    user = await authenticate_user_by_email(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    print("token:", access_token)
    # 返回token和用户名
    username = user.username
    return {"access_token": access_token, "token_type": "bearer","username": username}

@router.post("/logout")
async def logout():
    # 由于JWT是无状态的，服务器端不需要特殊处理
    # 客户端需要删除本地存储的token
    return {"message": "登出成功"}


# 添加密码重置请求模型
class PasswordResetRequest(BaseModel):
    email: EmailStr
    password_new: str

@public_router.post("/forgot")
async def forgot_password(
    email: EmailStr = Form(...),
    password_new: str = Form(...),
    db: Session = Depends(get_db)
):
    # 检查用户是否存在
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新密码
    print("新密码:", password_new)
    hashed_password = get_password_hash(password_new)
    user.hashed_password = hashed_password
    
    # 提交更改到数据库
    db.commit()
    
    return {"message": "密码已成功重置"}