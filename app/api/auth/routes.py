from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.config import settings
from app.services.auth import authenticate_user, create_access_token, get_password_hash
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
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # 检查用户是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "注册成功"}

@public_router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    print("=====登录数据请求=====")
    print(f"用户名:{form_data.username}")
    print(f"密码{'*'*len(form_data.password) if form_data.password else 'None'}")
    print("=====================")

    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    # 由于JWT是无状态的，服务器端不需要特殊处理
    # 客户端需要删除本地存储的token
    return {"message": "登出成功"}
