"""
数据模型/Schema 管理工具
========================

提供数据模型的 CRUD 操作。
"""

import json
from typing import Optional, List, Dict

from ..config import mcp, logger, PROJECT_ID, SCHEMA_TYPES
from ..utils import _validate_config, _make_request


@mcp.tool()
def list_schemas(keyword: Optional[str] = None, limit: int = 50) -> str:
    """列出 Apifox 项目中的所有数据模型 (Schema)。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    logger.info("正在获取数据模型列表...")
    
    export_payload = {
        "scope": {"type": "ALL"},
        "options": {"includeApifoxExtensionProperties": True, "addFoldersToTags": False},
        "oasVersion": "3.1",
        "exportFormat": "JSON"
    }
    
    result = _make_request("POST", f"/projects/{PROJECT_ID}/export-openapi?locale=zh-CN", data=export_payload)
    
    if not result["success"]:
        return f"❌ 获取数据模型列表失败: {result.get('error', '未知错误')}"
    
    schemas = result.get("data", {}).get("components", {}).get("schemas", {})
    
    if not schemas:
        return "📭 当前项目中没有数据模型"
    
    schema_list = [{"name": name, "type": s.get("type", "object"), "description": s.get("description", ""), "properties": s.get("properties", {})} for name, s in schemas.items()]
    
    if keyword:
        schema_list = [s for s in schema_list if keyword.lower() in s.get("name", "").lower()]
    
    output_lines = [f"📦 数据模型列表 (共 {len(schema_list)} 个)", "=" * 50]
    
    for schema in schema_list[:limit]:
        output_lines.append(f"• [{schema.get('type', 'object'):8}] {schema.get('name', '未命名')} ({len(schema.get('properties', {}))} 个属性)")
    
    if len(schema_list) > limit:
        output_lines.append(f"\n... 还有 {len(schema_list) - limit} 个模型未显示")
    
    return "\n".join(output_lines)


@mcp.tool()
def create_schema(name: str, schema_type: str = "object", description: str = "", properties: Optional[Dict[str, Dict]] = None, required: Optional[List[str]] = None, items: Optional[Dict] = None, folder_id: int = 0) -> str:
    """创建新的数据模型 (Schema)。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    if schema_type not in SCHEMA_TYPES:
        return f"❌ 错误: 无效的模型类型 '{schema_type}'，支持的类型: {', '.join(SCHEMA_TYPES)}"
    
    json_schema = {"type": schema_type, "description": description}
    if schema_type == "object" and properties:
        json_schema["properties"] = properties
        if required:
            json_schema["required"] = required
    if schema_type == "array" and items:
        json_schema["items"] = items
    
    openapi_spec = {"openapi": "3.0.0", "info": {"title": f"Schema: {name}", "version": "1.0.0"}, "paths": {}, "components": {"schemas": {name: json_schema}}}
    
    import_payload = {"input": json.dumps(openapi_spec), "options": {"targetEndpointFolderId": 0, "targetSchemaFolderId": folder_id, "endpointOverwriteBehavior": "CREATE_NEW", "schemaOverwriteBehavior": "CREATE_NEW"}}
    
    logger.info(f"正在创建数据模型: {name}")
    result = _make_request("POST", f"/projects/{PROJECT_ID}/import-openapi?locale=zh-CN", data=import_payload)
    
    if not result["success"]:
        return f"❌ 创建失败: {result.get('error', '未知错误')}"
    
    created = result.get("data", {}).get("data", {}).get("counters", {}).get("schemaCreated", 0)
    if created == 0:
        return f"⚠️ 数据模型可能已存在或创建失败，请检查 Apifox 项目"
    
    logger.info(f"数据模型创建成功: {name}")
    return f"✅ 数据模型创建成功!\n\n📦 模型信息:\n   • 名称: {name}\n   • 类型: {schema_type}\n   • 属性数量: {len(properties) if properties else 0}"


@mcp.tool()
def update_schema(name: str, new_name: Optional[str] = None, description: Optional[str] = None, properties: Optional[Dict[str, Dict]] = None, required: Optional[List[str]] = None, schema_type: str = "object", folder_id: int = 0) -> str:
    """更新现有的数据模型 (Schema)。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    final_name = new_name if new_name else name
    json_schema = {"type": schema_type, "description": description or ""}
    if properties:
        json_schema["properties"] = properties
        if required:
            json_schema["required"] = required
    
    openapi_spec = {"openapi": "3.0.0", "info": {"title": f"Schema: {final_name}", "version": "1.0.0"}, "paths": {}, "components": {"schemas": {final_name: json_schema}}}
    import_payload = {"input": json.dumps(openapi_spec), "options": {"targetEndpointFolderId": 0, "targetSchemaFolderId": folder_id, "endpointOverwriteBehavior": "OVERWRITE_EXISTING", "schemaOverwriteBehavior": "OVERWRITE_EXISTING"}}
    
    logger.info(f"正在更新数据模型: {name}")
    result = _make_request("POST", f"/projects/{PROJECT_ID}/import-openapi?locale=zh-CN", data=import_payload)
    
    if not result["success"]:
        return f"❌ 更新失败: {result.get('error', '未知错误')}"
    
    updated = result.get("data", {}).get("data", {}).get("counters", {}).get("schemaUpdated", 0)
    action = "更新" if updated > 0 else "创建"
    logger.info(f"数据模型{action}成功: {final_name}")
    return f"✅ 数据模型{action}成功!\n\n📦 模型信息:\n   • 名称: {final_name}\n   • 类型: {schema_type}"


@mcp.tool()
def delete_schema(name: str, confirm: bool = False) -> str:
    """删除数据模型 (Schema)。⚠️ 警告: 此操作不可撤销！"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    if not confirm:
        return f"⚠️ 安全提示: 删除操作不可撤销!\n\n请确认要删除模型: {name}\n\n如果确认删除，请将 confirm 参数设为 True:\ndelete_schema(name=\"{name}\", confirm=True)"
    
    return f"⚠️ 公开 API 暂不支持直接删除数据模型\n\n请在 Apifox 客户端中手动删除模型: {name}\n项目 ID: {PROJECT_ID}"


@mcp.tool()
def get_schema_detail(name: str) -> str:
    """获取数据模型的详细信息。"""
    config_error = _validate_config()
    if config_error:
        return config_error
    
    logger.info(f"正在获取数据模型详情: {name}")
    
    export_payload = {"scope": {"type": "ALL"}, "options": {"includeApifoxExtensionProperties": True}, "oasVersion": "3.1", "exportFormat": "JSON"}
    result = _make_request("POST", f"/projects/{PROJECT_ID}/export-openapi?locale=zh-CN", data=export_payload)
    
    if not result["success"]:
        return f"❌ 获取失败: {result.get('error', '未知错误')}"
    
    schemas = result.get("data", {}).get("components", {}).get("schemas", {})
    if name not in schemas:
        return f"❌ 未找到名为 {name} 的数据模型"
    
    schema = schemas[name]
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    output_lines = [f"📦 数据模型详情: {name}", "=" * 50, f"📝 说明: {schema.get('description', '无')}", f"📊 类型: {schema.get('type', 'unknown')}", ""]
    
    if properties:
        output_lines.append(f"属性列表 ({len(properties)} 个):")
        for prop_name, prop_def in properties.items():
            req_mark = "*" if prop_name in required else " "
            prop_type = prop_def.get("type", "any")
            output_lines.append(f"{req_mark} {prop_name}: {prop_type}")
    
    output_lines.append("\n💡 * 表示必填字段")
    return "\n".join(output_lines)
