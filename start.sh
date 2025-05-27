#!/bin/zsh

# 检查Python版本
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -gt 3 ] || { [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 8 ]; }; then
    echo "Python version $python_version is compatible."
else
    echo "Error: Python version must be >= 3.8 (current: $python_version)"
    exit 1
fi

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装/更新依赖
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# 确保上传目录存在
mkdir -p uploads/videos uploads/images

# 初始化数据库
echo "Initializing database..."
python3 -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 启动服务器
echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
