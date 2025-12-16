"""
Apifox MCP 服务器包
==================

提供与 Apifox API 交互的 MCP 工具集。
"""

from .config import mcp, logger

__version__ = "2.0.0"
__all__ = ["mcp", "logger"]
