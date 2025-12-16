"""
Apifox MCP 服务器入口
=====================

启动 MCP 服务器，加载所有工具。
"""

from .config import mcp, logger

# 导入所有工具模块以注册装饰器
from . import tools  # noqa: F401


def main():
    """启动 MCP 服务器"""
    logger.info("正在启动 Apifox MCP 服务器 v2.0.0...")
    logger.info("可用工具: check_apifox_config, list_api_endpoints, create_api_endpoint, update_api_endpoint, delete_api_endpoint, get_api_endpoint_detail, list_schemas, create_schema, update_schema, delete_schema, get_schema_detail, list_folders, delete_folder, create_folder, list_tags, get_apis_by_tag, add_tag_to_api")
    mcp.run()


if __name__ == "__main__":
    main()
