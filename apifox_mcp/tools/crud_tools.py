"""
CRUD 批量生成工具
=================

根据资源模型自动生成标准 RESTful CRUD 接口。

⚠️ 强制约束 - Schema 公共组件规范：
========================================
本模块 **强制** 将所有 Schema 定义为公共组件：
- 资源模型 → components/schemas/{Resource}
- 请求体 → components/schemas/Create{Resource}Request
- 列表响应 → components/schemas/{Resource}ListResponse
- 错误响应 → components/schemas/ErrorResponse（共享）

所有接口的请求体和响应体都使用 $ref 引用公共组件，
**绝不允许内联定义**。这确保了 Apifox 中的数据模型可复用、易维护。
"""

import json
from typing import Optional, List, Dict

from ..config import mcp, logger, PROJECT_ID, HTTP_STATUS_CODES
from ..utils import _validate_config, _make_request, _build_openapi_spec


# ============================================================
# 标准响应模板
# ============================================================

STANDARD_ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "integer", "description": "错误码"},
        "message": {"type": "string", "description": "错误信息"},
        "details": {"type": "object", "description": "详细信息"}
    },
    "required": ["code", "message"]
}

STANDARD_ERROR_RESPONSES = {
    400: {"code": 400, "name": "请求参数错误", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 400, "message": "请求参数错误"}},
    401: {"code": 401, "name": "未授权", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 401, "message": "未授权，请先登录"}},
    403: {"code": 403, "name": "禁止访问", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 403, "message": "无权限访问此资源"}},
    404: {"code": 404, "name": "资源不存在", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 404, "message": "请求的资源不存在"}},
    409: {"code": 409, "name": "资源冲突", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 409, "message": "资源已存在或状态冲突"}},
    422: {"code": 422, "name": "实体无法处理", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 422, "message": "请求格式正确但语义错误"}},
    500: {"code": 500, "name": "服务器内部错误", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 500, "message": "服务器内部错误，请稍后重试"}},
    502: {"code": 502, "name": "网关错误", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 502, "message": "网关错误，上游服务不可用"}},
    503: {"code": 503, "name": "服务不可用", "schema": STANDARD_ERROR_SCHEMA, "example": {"code": 503, "message": "服务暂时不可用，请稍后重试"}}
}


def _get_error_responses(method: str) -> List[Dict]:
    """获取指定方法的标准错误响应"""
    codes = [400, 401, 403, 404, 500, 502, 503]
    if method in ["POST", "PUT", "PATCH"]:
        codes.extend([409, 422])
    return [STANDARD_ERROR_RESPONSES[c].copy() for c in codes if c in STANDARD_ERROR_RESPONSES]


def _build_list_schema(item_schema_or_ref: Dict, resource_name_cn: str) -> Dict:
    """
    构建列表响应 Schema（带分页）
    
    Args:
        item_schema_or_ref: 列表项的 Schema 或 $ref 引用
                           如 {"$ref": "#/components/schemas/User"}
        resource_name_cn: 资源中文名称
    """
    return {
        "type": "object",
        "description": f"{resource_name_cn}列表响应",
        "properties": {
            "items": {
                "type": "array",
                "description": f"{resource_name_cn}列表",
                "items": item_schema_or_ref
            },
            "total": {"type": "integer", "description": "总数量"},
            "page": {"type": "integer", "description": "当前页码"},
            "page_size": {"type": "integer", "description": "每页数量"}
        },
        "required": ["items", "total"]
    }


def _build_list_example(item_example: Dict, resource_name_cn: str) -> Dict:
    """构建列表响应示例"""
    return {
        "items": [item_example],
        "total": 100,
        "page": 1,
        "page_size": 20
    }


def _generate_item_example(schema: Dict, id_value: int = 1) -> Dict:
    """根据 Schema 生成示例数据"""
    example = {}
    properties = schema.get("properties", {})
    
    for name, prop in properties.items():
        prop_type = prop.get("type", "string")
        description = prop.get("description", name)
        
        if name == "id":
            example[name] = id_value
        elif prop_type == "integer":
            example[name] = 1
        elif prop_type == "number":
            example[name] = 1.0
        elif prop_type == "boolean":
            example[name] = True
        elif prop_type == "array":
            example[name] = []
        elif prop_type == "object":
            example[name] = {}
        else:
            # string 类型，根据字段名生成有意义的值
            if "email" in name.lower():
                example[name] = "user@example.com"
            elif "phone" in name.lower():
                example[name] = "13800138000"
            elif "name" in name.lower():
                example[name] = "示例名称"
            elif "time" in name.lower() or "date" in name.lower():
                example[name] = "2024-01-01T12:00:00Z"
            elif "url" in name.lower():
                example[name] = "https://example.com"
            else:
                example[name] = f"示例{description}"
    
    return example


@mcp.tool()
def generate_crud_apis(
    resource_name: str,
    resource_name_cn: str,
    base_path: str,
    model_schema: Dict,
    id_field: str = "id",
    id_type: str = "integer",
    operations: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    folder_id: int = 0,
    description_prefix: str = ""
) -> str:
    """
    根据资源模型自动生成标准 RESTful CRUD 接口。
    
    生成的接口：
    - GET    {base_path}        列表查询（分页）
    - GET    {base_path}/{id}   获取单个资源
    - POST   {base_path}        创建资源
    - PUT    {base_path}/{id}   更新资源
    - DELETE {base_path}/{id}   删除资源
    
    Args:
        resource_name: 资源英文名称，如 "user", "order"
        resource_name_cn: 资源中文名称，如 "用户", "订单"
        base_path: 基础路径，如 "/api/v1/users"
        model_schema: 数据模型的 JSON Schema
                      ⚠️ 每个字段必须有 description
                      示例: {
                          "type": "object",
                          "properties": {
                              "id": {"type": "integer", "description": "ID"},
                              "name": {"type": "string", "description": "名称"}
                          },
                          "required": ["name"]
                      }
        id_field: 主键字段名，默认 "id"
        id_type: 主键类型，默认 "integer"
        operations: 要生成的操作列表，默认全部
                    可选: ["list", "get", "create", "update", "delete"]
        tags: 标签列表，默认使用 [resource_name_cn + "管理"]
        folder_id: 目标目录 ID
        description_prefix: 接口描述前缀，如 "【版本】v1\\n【环境】REST 接口"
        
    Returns:
        生成结果报告
        
    Example:
        >>> generate_crud_apis(
        ...     resource_name="user",
        ...     resource_name_cn="用户",
        ...     base_path="/api/v1/users",
        ...     model_schema={
        ...         "type": "object",
        ...         "properties": {
        ...             "id": {"type": "integer", "description": "用户ID"},
        ...             "name": {"type": "string", "description": "用户名"},
        ...             "email": {"type": "string", "description": "邮箱"}
        ...         },
        ...         "required": ["name", "email"]
        ...     }
        ... )
    """
    config_error = _validate_config()
    if config_error:
        return config_error
    
    # 默认值
    if operations is None:
        operations = ["list", "get", "create", "update", "delete"]
    if tags is None:
        tags = [f"{resource_name_cn}管理"]
    
    # 验证 Schema
    if not model_schema or not model_schema.get("properties"):
        return "❌ model_schema 必须包含 properties 定义"
    
    # 检查字段描述
    properties = model_schema.get("properties", {})
    missing_desc = [name for name, prop in properties.items() if not prop.get("description")]
    if missing_desc:
        return f"❌ 以下字段缺少 description: {', '.join(missing_desc)}"
    
    # 生成示例数据
    item_example = _generate_item_example(model_schema)
    
    # 构建创建/更新时的请求体 Schema（移除 id 字段）
    create_schema = {
        "type": "object",
        "description": f"创建{resource_name_cn}请求体",
        "properties": {k: v for k, v in properties.items() if k != id_field},
        "required": [r for r in model_schema.get("required", []) if r != id_field]
    }
    create_example = {k: v for k, v in item_example.items() if k != id_field}
    
    # 构建所有接口
    all_paths = {}
    created_apis = []
    
    # 描述模板
    def make_desc(action: str) -> str:
        desc = f"{action}{resource_name_cn}"
        if description_prefix:
            desc = f"{description_prefix}\n\n{desc}"
        return desc
    
    # ============================================================
    # 收集所有 Schema 到 components
    # ============================================================
    components_schemas = {}
    
    # 资源主模型（如 User）
    resource_schema_name = resource_name.capitalize()
    components_schemas[resource_schema_name] = model_schema
    
    # 创建/更新请求模型（如 CreateUserRequest）
    create_request_schema_name = f"Create{resource_schema_name}Request"
    components_schemas[create_request_schema_name] = create_schema
    
    # 列表响应模型（如 UserListResponse）
    list_response_schema_name = f"{resource_schema_name}ListResponse"
    list_schema = _build_list_schema({"$ref": f"#/components/schemas/{resource_schema_name}"}, resource_name_cn)
    components_schemas[list_response_schema_name] = list_schema
    
    # 错误响应模型
    error_schema_name = "ErrorResponse"
    components_schemas[error_schema_name] = STANDARD_ERROR_SCHEMA
    
    # ============================================================
    # 构建接口（使用 $ref 引用）
    # ============================================================
    
    # 1. LIST - 获取列表
    if "list" in operations:
        list_example = _build_list_example(item_example, resource_name_cn)
        
        all_paths.setdefault(base_path, {})
        all_paths[base_path]["get"] = {
            "summary": f"获取{resource_name_cn}列表",
            "description": make_desc("获取") + "列表，支持分页",
            "operationId": f"list_{resource_name}s",
            "tags": tags,
            "parameters": [
                {"name": "page", "in": "query", "required": False, "description": "页码", "schema": {"type": "integer", "default": 1}},
                {"name": "page_size", "in": "query", "required": False, "description": "每页数量", "schema": {"type": "integer", "default": 20}}
            ],
            "responses": _build_responses_with_ref(200, "成功", list_response_schema_name, list_example, "GET", error_schema_name)
        }
        created_apis.append(f"GET {base_path}")
    
    # 2. GET - 获取单个
    if "get" in operations:
        detail_path = f"{base_path}/{{{id_field}}}"
        all_paths.setdefault(detail_path, {})
        all_paths[detail_path]["get"] = {
            "summary": f"获取{resource_name_cn}详情",
            "description": make_desc("获取") + "详情",
            "operationId": f"get_{resource_name}",
            "tags": tags,
            "parameters": [
                {"name": id_field, "in": "path", "required": True, "description": f"{resource_name_cn}ID", "schema": {"type": id_type}}
            ],
            "responses": _build_responses_with_ref(200, "成功", resource_schema_name, item_example, "GET", error_schema_name)
        }
        created_apis.append(f"GET {detail_path}")
    
    # 3. CREATE - 创建
    if "create" in operations:
        all_paths.setdefault(base_path, {})
        all_paths[base_path]["post"] = {
            "summary": f"创建{resource_name_cn}",
            "description": make_desc("创建"),
            "operationId": f"create_{resource_name}",
            "tags": tags,
            "requestBody": {
                "required": True,
                "content": {"application/json": {
                    "schema": {"$ref": f"#/components/schemas/{create_request_schema_name}"},
                    "example": create_example
                }}
            },
            "responses": _build_responses_with_ref(201, "创建成功", resource_schema_name, item_example, "POST", error_schema_name)
        }
        created_apis.append(f"POST {base_path}")
    
    # 4. UPDATE - 更新
    if "update" in operations:
        detail_path = f"{base_path}/{{{id_field}}}"
        all_paths.setdefault(detail_path, {})
        all_paths[detail_path]["put"] = {
            "summary": f"更新{resource_name_cn}",
            "description": make_desc("更新"),
            "operationId": f"update_{resource_name}",
            "tags": tags,
            "parameters": [
                {"name": id_field, "in": "path", "required": True, "description": f"{resource_name_cn}ID", "schema": {"type": id_type}}
            ],
            "requestBody": {
                "required": True,
                "content": {"application/json": {
                    "schema": {"$ref": f"#/components/schemas/{create_request_schema_name}"},
                    "example": create_example
                }}
            },
            "responses": _build_responses_with_ref(200, "更新成功", resource_schema_name, item_example, "PUT", error_schema_name)
        }
        created_apis.append(f"PUT {detail_path}")
    
    # 5. DELETE - 删除
    if "delete" in operations:
        detail_path = f"{base_path}/{{{id_field}}}"
        all_paths.setdefault(detail_path, {})
        all_paths[detail_path]["delete"] = {
            "summary": f"删除{resource_name_cn}",
            "description": make_desc("删除"),
            "operationId": f"delete_{resource_name}",
            "tags": tags,
            "parameters": [
                {"name": id_field, "in": "path", "required": True, "description": f"{resource_name_cn}ID", "schema": {"type": id_type}}
            ],
            "responses": _build_responses_with_ref(204, "删除成功", None, None, "DELETE", error_schema_name)
        }
        created_apis.append(f"DELETE {detail_path}")
    
    # 构建 OpenAPI 规范（包含 components）
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": f"{resource_name_cn} CRUD API", "version": "1.0.0"},
        "paths": all_paths,
        "components": {"schemas": components_schemas}
    }
    
    # 导入到 Apifox
    import_payload = {
        "input": json.dumps(openapi_spec),
        "options": {
            "targetEndpointFolderId": folder_id,
            "targetSchemaFolderId": 0,
            "endpointOverwriteBehavior": "CREATE_NEW",  # 接口不覆盖，避免意外修改
            # Schema 使用覆盖策略，避免重复创建相同的 Schema（如 ErrorResponse）
            "schemaOverwriteBehavior": "OVERWRITE_EXISTING"
        }
    }
    
    logger.info(f"正在批量创建 {resource_name_cn} CRUD 接口...")
    result = _make_request("POST", f"/projects/{PROJECT_ID}/import-openapi?locale=zh-CN", data=import_payload)
    
    if not result["success"]:
        return f"❌ 创建失败: {result.get('error', '未知错误')}"
    
    counters = result.get("data", {}).get("data", {}).get("counters", {})
    created = counters.get("endpointCreated", 0)
    updated = counters.get("endpointUpdated", 0)
    
    return f"""✅ CRUD 接口批量生成成功!

📋 生成信息:
   • 资源: {resource_name_cn} ({resource_name})
   • 基础路径: {base_path}
   • 标签: {', '.join(tags)}
   • 创建: {created} 个
   • 更新: {updated} 个

📌 生成的接口:
{chr(10).join('   • ' + api for api in created_apis)}

💡 系统已自动添加标准错误响应 (400/401/403/404/500)"""


def _build_responses_with_ref(
    code: int, 
    name: str, 
    schema_name: Optional[str], 
    example: Optional[Dict], 
    method: str,
    error_schema_name: str = "ErrorResponse"
) -> Dict:
    """
    构建响应对象（使用 $ref 引用，包含成功响应和错误响应）
    
    Args:
        code: 成功响应状态码
        name: 响应名称
        schema_name: 成功响应的 Schema 名称（用于 $ref 引用）
        example: 成功响应示例
        method: HTTP 方法
        error_schema_name: 错误响应 Schema 名称
    """
    responses = {}
    
    # 成功响应
    if schema_name or code == 204:
        resp = {"description": name}
        if schema_name:
            resp["content"] = {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                }
            }
            if example:
                resp["content"]["application/json"]["example"] = example
        responses[str(code)] = resp
    
    # 错误响应（使用 $ref 引用共享的 ErrorResponse）
    for err_resp in _get_error_responses(method):
        err_code = str(err_resp["code"])
        responses[err_code] = {
            "description": err_resp["name"],
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{error_schema_name}"},
                    "example": err_resp["example"]
                }
            }
        }
    
    return responses


# 保留旧函数以保持向后兼容
def _build_responses(code: int, name: str, schema: Optional[Dict], example: Optional[Dict], method: str) -> Dict:
    """[已废弃] 请使用 _build_responses_with_ref 代替"""
    responses = {}
    
    if schema or code == 204:
        resp = {"description": name}
        if schema:
            resp["content"] = {"application/json": {"schema": schema}}
            if example:
                resp["content"]["application/json"]["example"] = example
        responses[str(code)] = resp
    
    for err_resp in _get_error_responses(method):
        err_code = str(err_resp["code"])
        responses[err_code] = {
            "description": err_resp["name"],
            "content": {"application/json": {"schema": err_resp["schema"], "example": err_resp["example"]}}
        }
    
    return responses
