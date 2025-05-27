# 抬头率检测系统后端

## 项目结构

```
taitoulv_backend/
├── app/                    # 主应用目录
│   ├── api/               # API路由目录
│   │   ├── analytics/     # 数据分析相关路由
│   │   ├── auth/         # 认证相关路由
│   │   └── video/        # 视频处理相关路由
│   ├── core/             # 核心配置目录
│   │   ├── config.py     # 配置加载和管理
│   │   ├── database.py   # 数据库连接和会话管理
│   │   └── settings.py   # 项目设置
│   ├── models/           # 数据模型目录
│   │   ├── user.py      # 用户模型
│   │   └── video.py     # 视频分析模型
│   ├── services/         # 业务服务目录
│   │   ├── auth.py      # 认证服务
│   │   └── yolo_service.py  # YOLO模型服务
│   ├── utils/           # 工具函数目录
│   └── main.py         # 应用入口文件
├── uploads/            # 文件上传目录
├── requirements.txt    # 项目依赖
└── start.sh           # 启动脚本
```

## 主要模块说明

### 1. API模块 (`app/api/`)

#### 认证模块 (`auth/`)
- `routes.py`: 实现用户注册、登录、登出等认证相关接口
- 主要接口：
  - POST `/api/auth/register`: 用户注册
  - POST `/api/auth/login`: 用户登录
  - POST `/api/auth/logout`: 用户登出

#### 视频处理模块 (`video/`)
- `routes.py`: 实现视频上传、处理和分析相关接口
- 主要接口：
  - POST `/api/video/upload`: 视频文件上传
  - POST `/api/video/upload/image`: 图片文件上传
  - WS `/api/video/stream`: 实时视频流处理
  - GET `/api/video/sessions/{user_id}`: 获取用户会话记录
  - GET `/api/video/sessions/{session_id}/analysis`: 获取会话分析数据

### 2. 核心模块 (`app/core/`)

#### 配置管理 (`config.py`)
- 加载环境变量
- 项目全局配置
- 安全设置

#### 数据库管理 (`database.py`)
- 数据库连接配置
- 会话管理
- 数据库迁移

#### 项目设置 (`settings.py`)
- 项目常量配置
- 环境变量管理
- 系统参数设置

### 3. 数据模型 (`app/models/`)

#### 用户模型 (`user.py`)
- 用户信息存储
- 认证相关字段
- 用户权限管理

#### 视频模型 (`video.py`)
- 视频会话记录
- 分析结果存储
- 统计数据管理

### 4. 服务模块 (`app/services/`)

#### 认证服务 (`auth.py`)
- 用户认证逻辑
- Token生成和验证
- 密码加密和验证

#### YOLO服务 (`yolo_service.py`)
- YOLO5模型加载和管理
- 图像处理和分析
- 实时视频流处理

## 快速开始

1. 创建并激活虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 创建`.env`文件：
```bash
cp .env.example .env
# 编辑.env文件，设置必要的环境变量
```

4. 启动服务：
```bash
./start.sh
```

## API文档

启动服务后，访问以下地址查看详细的API文档：
- Swagger UI: `http://localhost:3001/docs`
- ReDoc: `http://localhost:3001/redoc`

## 开发指南

1. **添加新的API路由**
   - 在 `app/api/` 下创建新的模块目录
   - 实现 `routes.py` 文件
   - 在 `main.py` 中注册路由

2. **添加新的数据模型**
   - 在 `app/models/` 下创建新的模型文件
   - 在 `database.py` 中导入模型
   - 执行数据库迁移

3. **添加新的服务**
   - 在 `app/services/` 下创建新的服务文件
   - 实现业务逻辑
   - 在需要的地方导入和使用

## 注意事项

1. 所有敏感信息都应该通过环境变量配置
2. 代码提交前需要运行测试用例
3. 保持代码风格一致性
4. 定期更新依赖包版本
5. 注意处理异常情况
