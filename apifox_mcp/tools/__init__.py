"""
MCP 工具模块
============

导入并注册所有 MCP 工具。
"""

# 导入所有工具模块以注册装饰器
from . import config_tools
from . import api_tools
from . import schema_tools
from . import folder_tools
from . import tag_tools
from . import audit_tools
from . import crud_tools
from . import validation_tools

__all__ = [
    "config_tools",
    "api_tools", 
    "schema_tools",
    "folder_tools",
    "tag_tools",
    "audit_tools",
    "crud_tools",
    "validation_tools"
]
