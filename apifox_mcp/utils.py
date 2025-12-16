"""
工具函数模块
============

包含 API 请求、参数构建等辅助函数。
"""

import json
import requests
from typing import Optional, List, Dict, Any

from .config import (
    APIFOX_TOKEN, PROJECT_ID, APIFOX_PUBLIC_API, 
    APIFOX_API_VERSION, HTTP_STATUS_CODES, logger
)


def _get_headers() -> Dict[str, str]:
    """
    获取 Apifox API 请求头
    
    Returns:
        包含认证信息和版本号的请求头字典
    """
    return {
        "Authorization": f"Bearer {APIFOX_TOKEN}",
        "Content-Type": "application/json",
        "X-Apifox-Api-Version": APIFOX_API_VERSION
    }


def _validate_config() -> Optional[str]:
    """
    验证环境变量配置
    
    Returns:
        如果配置有效返回 None，否则返回错误信息
    """
    if not APIFOX_TOKEN:
        return "❌ 错误: 缺少 APIFOX_TOKEN 环境变量，请在环境变量中设置你的 Apifox 访问令牌"
    if not PROJECT_ID:
        return "❌ 错误: 缺少 APIFOX_PROJECT_ID 环境变量，请在环境变量中设置目标项目 ID"
    return None


def _make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    use_public_api: bool = True
) -> Dict[str, Any]:
    """
    发送 API 请求的通用方法
    
    Args:
        method: HTTP 方法 (GET, POST, PUT, DELETE)
        endpoint: API 端点路径 (不含基础 URL)
        data: 请求体数据
        params: URL 查询参数
        use_public_api: 是否使用公开 API (默认 True)
        
    Returns:
        包含 success、data、error 的结果字典
    """
    base_url = APIFOX_PUBLIC_API
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=_get_headers(),
            timeout=30
        )
        
        if response.status_code in [200, 201, 204]:
            try:
                return {
                    "success": True,
                    "data": response.json() if response.text else {},
                    "status_code": response.status_code
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": {"raw": response.text},
                    "status_code": response.status_code
                }
        else:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = error_data.get('message', '') or error_data.get('errorMessage', '') or error_data.get('error', '')
            except:
                error_detail = response.text[:200] if response.text else "未知错误"
            
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {error_detail}",
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时，请检查网络连接"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "网络连接失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_parameter(
    name: str,
    location: str,
    param_type: str = "string",
    required: bool = False,
    description: str = "",
    example: Any = None
) -> Dict[str, Any]:
    """
    构建 OpenAPI 格式的参数对象
    
    Args:
        name: 参数名称
        location: 参数位置 (query, path, header)
        param_type: 参数类型
        required: 是否必填
        description: 参数描述
        example: 示例值
        
    Returns:
        符合 OpenAPI 规范的参数字典
    """
    param = {
        "name": name,
        "in": location,
        "required": required if location != "path" else True,
        "description": description,
        "schema": {"type": param_type}
    }
    
    if example is not None:
        param["example"] = example
        
    return param


def _build_parameters_list(
    query_params: Optional[List[Dict]] = None,
    path_params: Optional[List[Dict]] = None,
    header_params: Optional[List[Dict]] = None
) -> List[Dict[str, Any]]:
    """
    构建完整的参数列表
    
    Args:
        query_params: Query 参数列表
        path_params: Path 参数列表  
        header_params: Header 参数列表
        
    Returns:
        合并后的参数列表
    """
    parameters = []
    
    if query_params:
        for param in query_params:
            parameters.append(_build_parameter(
                name=param.get("name", ""),
                location="query",
                param_type=param.get("type", "string"),
                required=param.get("required", False),
                description=param.get("description", ""),
                example=param.get("example")
            ))
    
    if path_params:
        for param in path_params:
            parameters.append(_build_parameter(
                name=param.get("name", ""),
                location="path",
                param_type=param.get("type", "string"),
                required=True,
                description=param.get("description", ""),
                example=param.get("example")
            ))
    
    if header_params:
        for param in header_params:
            parameters.append(_build_parameter(
                name=param.get("name", ""),
                location="header",
                param_type=param.get("type", "string"),
                required=param.get("required", False),
                description=param.get("description", ""),
                example=param.get("example")
            ))
    
    return parameters


def _build_request_body(
    body_type: str = "json",
    schema: Optional[Dict] = None,
    example: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    构建请求体配置
    
    Args:
        body_type: 请求体类型
        schema: JSON Schema 定义
        example: 请求体示例
        
    Returns:
        请求体配置字典
    """
    request_body = {"type": body_type}
    
    if body_type == "json":
        if schema:
            request_body["jsonSchema"] = schema
        if example:
            request_body["example"] = example
        
    return request_body


def _build_responses(
    responses_config: Optional[List[Dict]] = None,
    success_schema: Optional[Dict] = None,
    success_example: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    构建响应配置列表
    
    Args:
        responses_config: 响应配置列表
        success_schema: 成功响应的 JSON Schema
        success_example: 成功响应的示例
        
    Returns:
        响应配置列表
    """
    responses = []
    
    if responses_config:
        for resp in responses_config:
            code = resp.get("code", 200)
            response_item = {
                "code": code,
                "name": resp.get("name", HTTP_STATUS_CODES.get(code, "响应")),
                "contentType": "json"
            }
            
            if resp.get("schema"):
                response_item["jsonSchema"] = resp["schema"]
                
            if resp.get("example"):
                response_item["examples"] = [{
                    "name": f"{code} 示例",
                    "data": resp["example"]
                }]
                
            responses.append(response_item)
    
    elif success_schema or success_example:
        response_item = {
            "code": 200,
            "name": "成功",
            "contentType": "json"
        }
        
        if success_schema:
            response_item["jsonSchema"] = success_schema
            
        if success_example:
            response_item["examples"] = [{
                "name": "默认示例",
                "data": success_example
            }]
            
        responses.append(response_item)
    
    return responses


def _build_openapi_spec(
    title: str,
    path: str,
    method: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    query_params: Optional[List[Dict]] = None,
    path_params: Optional[List[Dict]] = None,
    header_params: Optional[List[Dict]] = None,
    request_body_type: str = "none",
    request_body_schema: Optional[Dict] = None,
    request_body_example: Optional[Dict] = None,
    responses: Optional[List[Dict]] = None,
    response_schema: Optional[Dict] = None,
    response_example: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    构建 OpenAPI 3.0 规范格式的接口定义
    
    Args:
        title: 接口名称
        path: 接口路径
        method: HTTP 方法
        description: 接口描述
        tags: 标签列表
        query_params: Query 参数
        path_params: Path 参数
        header_params: Header 参数
        request_body_type: 请求体类型
        request_body_schema: 请求体 Schema
        request_body_example: 请求体示例
        responses: 响应配置列表
        response_schema: 成功响应 Schema
        response_example: 成功响应示例
        
    Returns:
        OpenAPI 3.0 格式的规范字典
    """
    # 构建参数列表
    parameters = []
    
    if query_params:
        for p in query_params:
            param = {
                "name": p.get("name", ""),
                "in": "query",
                "required": p.get("required", False),
                "description": p.get("description", ""),
                "schema": {"type": p.get("type", "string")}
            }
            if p.get("example") is not None:
                param["example"] = p["example"]
            parameters.append(param)
    
    if path_params:
        for p in path_params:
            param = {
                "name": p.get("name", ""),
                "in": "path",
                "required": True,
                "description": p.get("description", ""),
                "schema": {"type": p.get("type", "string")}
            }
            if p.get("example") is not None:
                param["example"] = p["example"]
            parameters.append(param)
    
    if header_params:
        for p in header_params:
            param = {
                "name": p.get("name", ""),
                "in": "header",
                "required": p.get("required", False),
                "description": p.get("description", ""),
                "schema": {"type": p.get("type", "string")}
            }
            if p.get("example") is not None:
                param["example"] = p["example"]
            parameters.append(param)
    
    # 构建操作对象
    operation = {
        "summary": title,
        "description": description,
        "operationId": title.replace(" ", "_").lower(),
        "tags": tags or []
    }
    
    if parameters:
        operation["parameters"] = parameters
    
    # 构建请求体
    if request_body_type == "json" and (request_body_schema or request_body_example):
        content = {"application/json": {}}
        if request_body_schema:
            content["application/json"]["schema"] = request_body_schema
        if request_body_example:
            content["application/json"]["example"] = request_body_example
        operation["requestBody"] = {
            "required": True,
            "content": content
        }
    
    # 构建响应
    openapi_responses = {}
    
    if responses:
        for resp in responses:
            code = str(resp.get("code", 200))
            resp_obj = {
                "description": resp.get("name", HTTP_STATUS_CODES.get(int(code), "响应"))
            }
            if resp.get("schema") or resp.get("example"):
                content = {"application/json": {}}
                if resp.get("schema"):
                    content["application/json"]["schema"] = resp["schema"]
                if resp.get("example"):
                    content["application/json"]["example"] = resp["example"]
                resp_obj["content"] = content
            openapi_responses[code] = resp_obj
    elif response_schema or response_example:
        content = {"application/json": {}}
        if response_schema:
            content["application/json"]["schema"] = response_schema
        if response_example:
            content["application/json"]["example"] = response_example
        openapi_responses["200"] = {
            "description": "成功",
            "content": content
        }
    else:
        openapi_responses["200"] = {"description": "成功"}
    
    operation["responses"] = openapi_responses
    
    # 构建完整的 OpenAPI 规范
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": "1.0.0"
        },
        "paths": {
            path: {
                method.lower(): operation
            }
        }
    }
    
    return openapi_spec


def _format_api_info(api: Dict) -> str:
    """
    格式化单个接口信息为可读字符串
    
    Args:
        api: 接口数据字典
        
    Returns:
        格式化后的字符串
    """
    from .config import API_STATUS
    
    method = api.get("method", "???").upper()
    path = api.get("path", "/???")
    title = api.get("title", "未命名")
    status = api.get("status", "developing")
    api_id = api.get("id", "???")
    
    return f"[{method:6}] {path:30} | {title} (ID: {api_id}, 状态: {API_STATUS.get(status, status)})"
