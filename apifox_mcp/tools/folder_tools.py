"""
目录管理工具
============

提供目录（标签/文件夹）管理功能。
"""

from ..config import mcp, logger, PROJECT_ID
from ..utils import _validate_config, _make_request


@mcp.tool()
def list_folders() -> str:
    """列出 Apifox 项目中的所有目录结构。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    logger.info("正在获取目录列表...")
    
    export_payload = {"scope": {"type": "ALL"}, "options": {"includeApifoxExtensionProperties": True, "addFoldersToTags": True}, "oasVersion": "3.1", "exportFormat": "JSON"}
    result = _make_request("POST", f"/projects/{PROJECT_ID}/export-openapi?locale=zh-CN", data=export_payload)
    
    if not result["success"]:
        return f"❌ 获取目录列表失败: {result.get('error', '未知错误')}"
    
    openapi_data = result.get("data", {})
    tags = openapi_data.get("tags", [])
    paths = openapi_data.get("paths", {})
    
    tag_counts = {}
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                for tag in details.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    if not tags and not tag_counts:
        return "📭 当前项目中没有目录（标签）"
    
    output_lines = ["📂 目录列表", "=" * 50]
    
    for tag in tags:
        tag_name = tag.get("name", "未命名") if isinstance(tag, dict) else tag
        count = tag_counts.get(tag_name, 0)
        output_lines.append(f"📁 {tag_name} ({count} 个接口)")
    
    for tag_name, count in tag_counts.items():
        if tag_name not in [t.get("name", t) if isinstance(t, dict) else t for t in tags]:
            output_lines.append(f"📁 {tag_name} ({count} 个接口)")
    
    return "\n".join(output_lines)


@mcp.tool()
def delete_folder(folder_name: str, confirm: bool = False) -> str:
    """删除 Apifox 项目中的目录（标签）。⚠️ 警告: 此操作不可撤销！"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    if not confirm:
        return f"⚠️ 安全提示: 删除操作不可撤销!\n\n请确认要删除目录: {folder_name}\n\n如果确认删除，请将 confirm 参数设为 True:\ndelete_folder(folder_name=\"{folder_name}\", confirm=True)"
    
    return f"⚠️ 公开 API 暂不支持直接删除目录\n\n请在 Apifox 客户端中手动删除目录: {folder_name}\n项目 ID: {PROJECT_ID}"


@mcp.tool() 
def create_folder(folder_name: str, description: str = "") -> str:
    """在 Apifox 项目中创建新目录（标签）。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    return f"""📁 创建目录提示

Apifox 的目录系统基于标签（Tags），目录会在创建接口时自动生成。

要创建目录 "{folder_name}"，请使用以下方式：

方式1: 创建新接口时指定标签
create_api_endpoint(
    title="示例接口",
    path="/example",
    method="GET",
    tags=["{folder_name}"],  # 这会自动创建目录
    ...
)

方式2: 使用 add_tag_to_api 工具为现有接口添加标签
add_tag_to_api(
    path="/existing-api",
    method="GET", 
    tags=["{folder_name}"]
)

💡 提示: 也可以在 Apifox 客户端中直接创建目录。"""
