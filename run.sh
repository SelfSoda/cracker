#!/bin/bash
# 启动脚本

# 检查是否安装了依赖
if ! command -v poetry &> /dev/null; then
    echo "请先安装 Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
poetry install --no-root

# 启动后端（后台运行）
echo "启动后端服务..."
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端界面..."
poetry run streamlit run frontend.py --server.port 8501

# 清理：当脚本退出时停止后端
trap "kill $BACKEND_PID" EXIT

