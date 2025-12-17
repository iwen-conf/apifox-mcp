"""
API 响应审计工具
================

提供 API 响应完整性检查和审计功能。
"""

from typing import Optional, List, Dict

from ..config import mcp, logger, PROJECT_ID
from ..utils import _validate_config, _make_request


# ============================================================
# 错误响应码常量
# ============================================================

REQUIRED_4XX_CODES = [400, 401, 403, 404]  # 所有 API 都需要
REQUIRED_5XX_CODES = [500, 502, 503]  # 所有 API 都需要
OPTIONAL_4XX_CODES = [409, 422]  # POST/PUT/PATCH 可能需要


# ============================================================
# 辅助函数
# ============================================================


def _check_response_completeness(api_responses: Dict, method: str) -> Dict:
    """检查单个 API 的响应完整性 - 完整检查所有 4xx 和 5xx"""
    
    # 收集现有的响应码
    existing_codes = set()
    success_info = {"has": False, "has_schema": False, "has_example": False}
    
    for code_str, resp in api_responses.items():
        code = int(code_str) if code_str.isdigit() else 0
        existing_codes.add(code)
        
        content = resp.get("content", {})
        has_schema = False
        has_example = False
        
        for media_type, media_def in content.items():
            if media_def.get("schema"):
                has_schema = True
            if media_def.get("example") or media_def.get("examples"):
                has_example = True
        
        if 200 <= code < 300:
            success_info["has"] = True
            success_info["has_schema"] = has_schema
            success_info["has_example"] = has_example
    
    # 确定必需的错误码
    required_4xx = list(REQUIRED_4XX_CODES)  # [400, 401, 403, 404]
    required_5xx = list(REQUIRED_5XX_CODES)  # [500, 502, 503]
    
    # POST/PUT/PATCH 额外需要 409, 422
    if method.upper() in ["POST", "PUT", "PATCH"]:
        required_4xx.extend(OPTIONAL_4XX_CODES)  # 添加 409, 422
    
    # 检查缺失项
    missing_4xx = [code for code in required_4xx if code not in existing_codes]
    missing_5xx = [code for code in required_5xx if code not in existing_codes]
    
    missing = []
    
    # 成功响应检查
    if not success_info["has"]:
        missing.append("成功响应(2xx)")
    elif not success_info["has_schema"]:
        missing.append("成功响应Schema")
    elif not success_info["has_example"]:
        missing.append("成功响应示例")
    
    # 4xx 缺失
    for code in missing_4xx:
        code_names = {400: "请求参数错误", 401: "未授权", 403: "禁止访问", 404: "资源不存在", 409: "资源冲突", 422: "实体无法处理"}
        missing.append(f"{code}({code_names.get(code, '')})")
    
    # 5xx 缺失
    for code in missing_5xx:
        code_names = {500: "服务器错误", 502: "网关错误", 503: "服务不可用"}
        missing.append(f"{code}({code_names.get(code, '')})")
    
    return {
        "response_codes": sorted(existing_codes),
        "required_4xx": required_4xx,
        "required_5xx": required_5xx,
        "missing_4xx": missing_4xx,
        "missing_5xx": missing_5xx,
        "missing": missing,
        "success_info": success_info,
        "is_complete": len(missing) == 0
    }


# ============================================================
# MCP 工具
# ============================================================


@mcp.tool()
def check_api_responses(path: str, method: str) -> str:
    """
    检查单个 API 的响应体定义完整性。
    
    检查内容：
    - 成功响应 (2xx): Schema 和 Example
    - 4xx 错误: 400, 401, 403, 404 (POST/PUT/PATCH 额外检查 409, 422)
    - 5xx 错误: 500, 502, 503
    
    Args:
        path: 接口路径
        method: HTTP 方法
        
    Returns:
        响应完整性检查报告
    """
    config_error = _validate_config()
    if config_error:
        return config_error
    
    method_lower = method.lower()
    logger.info(f"正在检查接口响应完整性: {method.upper()} {path}")
    
    export_payload = {
        "scope": {"type": "ALL"},
        "options": {"includeApifoxExtensionProperties": True},
        "oasVersion": "3.1",
        "exportFormat": "JSON"
    }
    
    result = _make_request("POST", f"/projects/{PROJECT_ID}/export-openapi?locale=zh-CN", data=export_payload)
    
    if not result["success"]:
        return f"❌ 获取失败: {result.get('error', '未知错误')}"
    
    paths = result.get("data", {}).get("paths", {})
    
    if path not in paths:
        return f"❌ 未找到路径为 {path} 的接口"
    
    path_item = paths[path]
    if method_lower not in path_item:
        return f"❌ 未找到 {method.upper()} {path} 接口"
    
    api = path_item[method_lower]
    responses = api.get("responses", {})
    title = api.get("summary", "未命名")
    
    check = _check_response_completeness(responses, method)
    existing = set(check["response_codes"])
    
    output = [
        f"📋 响应完整性检查: {title}",
        f"📍 路径: {method.upper()} {path}",
        "=" * 50,
        f"现有响应码: {', '.join(map(str, check['response_codes'])) or '无'}",
        "",
        "━━━ 成功响应 (2xx) ━━━",
    ]
    
    # 成功响应检查
    si = check["success_info"]
    if si["has"]:
        output.append(f"   ✅ 成功响应存在")
        output.append(f"      {'✅' if si['has_schema'] else '❌'} Schema 定义")
        output.append(f"      {'✅' if si['has_example'] else '❌'} 响应示例")
    else:
        output.append(f"   ❌ 成功响应缺失")
    
    # 4xx 检查
    output.append("")
    output.append("━━━ 4xx 客户端错误 ━━━")
    code_names = {400: "请求参数错误", 401: "未授权", 403: "禁止访问", 404: "资源不存在", 409: "资源冲突", 422: "实体无法处理"}
    for code in check["required_4xx"]:
        status = "✅" if code in existing else "❌"
        output.append(f"   {status} {code} {code_names.get(code, '')}")
    
    # 5xx 检查
    output.append("")
    output.append("━━━ 5xx 服务端错误 ━━━")
    code_names = {500: "服务器内部错误", 502: "网关错误", 503: "服务不可用"}
    for code in check["required_5xx"]:
        status = "✅" if code in existing else "❌"
        output.append(f"   {status} {code} {code_names.get(code, '')}")
    
    # 总结
    output.append("")
    if check["is_complete"]:
        output.append("🎉 该接口响应定义完整!")
    else:
        output.append(f"⚠️ 缺失 {len(check['missing'])} 项:")
        for m in check["missing"]:
            output.append(f"   • {m}")
        output.append("")
        output.append("💡 使用 update_api_endpoint 可自动补充所有缺失响应")
    
    return "\n".join(output)


@mcp.tool()
def audit_all_api_responses(
    tag: Optional[str] = None,
    show_complete: bool = False
) -> str:
    """
    审计所有 API 的响应完整性，找出响应定义不完整的接口。
    
    检查每个接口是否包含：
    - 成功响应 (2xx) 及其 Schema 和 Example
    - 4xx 客户端错误: 400, 401, 403, 404 (POST/PUT/PATCH 额外检查 409, 422)
    - 5xx 服务端错误: 500, 502, 503
    
    Args:
        tag: (可选) 只检查指定标签下的接口
        show_complete: 是否显示完整的接口，默认只显示不完整的
        
    Returns:
        审计报告，列出所有响应不完整的接口
    """
    config_error = _validate_config()
    if config_error:
        return config_error
    
    logger.info("正在审计所有 API 响应完整性...")
    
    export_payload = {
        "scope": {"type": "ALL"},
        "options": {"includeApifoxExtensionProperties": True},
        "oasVersion": "3.1",
        "exportFormat": "JSON"
    }
    
    result = _make_request("POST", f"/projects/{PROJECT_ID}/export-openapi?locale=zh-CN", data=export_payload)
    
    if not result["success"]:
        return f"❌ 获取失败: {result.get('error', '未知错误')}"
    
    paths = result.get("data", {}).get("paths", {})
    
    if not paths:
        return "📭 当前项目中没有接口"
    
    incomplete_apis = []
    complete_apis = []
    total_count = 0
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method not in ["get", "post", "put", "delete", "patch"]:
                continue
            
            # 标签过滤
            api_tags = details.get("tags", [])
            if tag and tag not in api_tags:
                continue
            
            total_count += 1
            title = details.get("summary", "未命名")
            responses = details.get("responses", {})
            
            check = _check_response_completeness(responses, method)
            
            api_info = {
                "method": method.upper(),
                "path": path,
                "title": title,
                "codes": check["response_codes"],
                "missing": check["missing"]
            }
            
            if check["missing"]:
                incomplete_apis.append(api_info)
            else:
                complete_apis.append(api_info)
    
    # 生成报告
    output = [
        "📊 API 响应完整性审计报告",
        "=" * 60,
        f"📍 检查范围: {f'标签 [{tag}]' if tag else '全部接口'}",
        f"📋 总接口数: {total_count}",
        f"✅ 完整: {len(complete_apis)} 个",
        f"❌ 不完整: {len(incomplete_apis)} 个",
        ""
    ]
    
    if incomplete_apis:
        output.append("=" * 60)
        output.append("❌ 响应不完整的接口:")
        output.append("")
        
        for api in incomplete_apis:
            output.append(f"[{api['method']:6}] {api['path']}")
            output.append(f"         名称: {api['title']}")
            output.append(f"         现有响应码: {', '.join(map(str, sorted(api['codes']))) or '无'}")
            output.append(f"         缺失: {', '.join(api['missing'])}")
            output.append("")
    
    if show_complete and complete_apis:
        output.append("=" * 60)
        output.append("✅ 响应完整的接口:")
        output.append("")
        for api in complete_apis:
            output.append(f"[{api['method']:6}] {api['path']} | {api['title']}")
    
    if incomplete_apis:
        output.append("")
        output.append("💡 提示: 使用 update_api_endpoint 或在 Apifox 客户端中补充缺失的响应定义")
    else:
        output.append("")
        output.append("🎉 所有接口响应定义都完整!")
    
    return "\n".join(output)
