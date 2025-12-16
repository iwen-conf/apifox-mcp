# ============================================================
# Apifox MCP 服务器 Dockerfile
# ============================================================
# 
# 构建命令:
#   docker build -t apifox-mcp .
#
# 运行命令 (需要设置环境变量):
#   docker run -e APIFOX_TOKEN=your_token -e APIFOX_PROJECT_ID=your_project_id apifox-mcp
#
# 或者使用 .env 文件:
#   docker run --env-file .env apifox-mcp
#
# ============================================================

# 使用轻量级 Python 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置 Python 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装依赖
# mcp[cli] - MCP 官方库，包含 CLI 工具
# requests - HTTP 请求库，用于调用 Apifox API
RUN pip install --no-cache-dir "mcp[cli]" requests

# 复制代码包
COPY apifox_mcp/ ./apifox_mcp/

# MCP 使用 Stdio 通信，不需要暴露端口
# 使用模块方式运行
ENTRYPOINT ["python", "-m", "apifox_mcp.main"]