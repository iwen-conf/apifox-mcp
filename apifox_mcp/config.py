"""
配置模块
========

包含 MCP 服务初始化、环境变量配置和常量定义。
"""

import os
import logging
from mcp.server.fastmcp import FastMCP

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ApifoxMCP")

# ============================================================
# MCP 服务初始化
# ============================================================
mcp = FastMCP(
    name="Apifox-Builder",
)

# ============================================================
# 环境变量配置
# ============================================================
APIFOX_TOKEN = os.getenv("APIFOX_TOKEN")  # Apifox 开放 API 令牌
PROJECT_ID = os.getenv("APIFOX_PROJECT_ID")  # 目标项目 ID

# Apifox API 基础地址
APIFOX_PUBLIC_API = "https://api.apifox.com/v1"
APIFOX_INTERNAL_API = "https://api.apifox.com/api/v1"
APIFOX_API_VERSION = "2024-03-28"

# ============================================================
# 常量定义
# ============================================================

# 接口状态枚举
API_STATUS = {
    "developing": "开发中",
    "testing": "测试中", 
    "released": "已发布",
    "deprecated": "已废弃"
}

# 请求体类型枚举
REQUEST_BODY_TYPES = ["none", "json", "form-data", "x-www-form-urlencoded", "raw", "binary"]

# HTTP 方法枚举
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# 常见 HTTP 状态码及其含义
HTTP_STATUS_CODES = {
    200: "成功",
    201: "创建成功",
    204: "无内容",
    400: "请求错误",
    401: "未授权",
    403: "禁止访问",
    404: "未找到",
    405: "方法不允许",
    409: "冲突",
    422: "无法处理的实体",
    429: "请求过多",
    500: "服务器内部错误",
    502: "网关错误",
    503: "服务不可用"
}

# JSON Schema 基本类型
SCHEMA_TYPES = ["string", "integer", "number", "boolean", "array", "object", "null"]
