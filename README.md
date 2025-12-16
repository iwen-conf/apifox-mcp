# Apifox MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyek0xMiAyMGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6Ii8+PC9zdmc+)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Apifox](https://img.shields.io/badge/Apifox-Integration-orange?logo=swagger&logoColor=white)](https://apifox.com/)

---

这是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的服务器，用于通过 LLM (如 Claude) 直接管理 [Apifox](https://apifox.com/) 项目。

它允许你通过自然语言指令来查看、创建、更新和删除 Apifox 中的 API 接口、数据模型 (Schema)、文件夹等，并能检查 API 定义的完整性。

## ✨ 功能特性

*   **API 接口管理**:
    *   列出接口 (`list_api_endpoints`)
    *   获取接口详情 (`get_api_endpoint_detail`)
    *   创建接口 (`create_api_endpoint`) - 自动处理标准错误响应
    *   更新接口 (`update_api_endpoint`)
    *   删除接口 (`delete_api_endpoint`)
    *   接口完整性检查 (`check_api_responses`, `audit_all_api_responses`)
*   **数据模型 (Schema) 管理**:
    *   列出模型 (`list_schemas`)
    *   获取模型详情 (`get_schema_detail`)
    *   创建模型 (`create_schema`)
    *   更新模型 (`update_schema`)
    *   删除模型 (`delete_schema`)
*   **其他管理**:
    *   目录管理 (`list_folders`, `create_folder`, `delete_folder`)
    *   标签管理 (`list_tags`)
    *   按标签获取接口 (`get_apis_by_tag`, `add_tag_to_api`)
    *   配置检查 (`check_apifox_config`)

## 🛠️ 安装

确保你的系统中已安装 Python 3.10 或更高版本。

1.  **克隆项目**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **创建并激活虚拟环境 (可选但推荐)**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **安装依赖**
    本项目依赖 `mcp` 和 `requests` 库。
    ```bash
    pip install mcp[cli] requests
    ```

## ⚙️ 配置

在使用前，你需要设置以下环境变量来连接你的 Apifox 项目。

| 环境变量 | 描述 | 获取方式 |
| :--- | :--- | :--- |
| `APIFOX_TOKEN` | Apifox 开放 API 令牌 | Apifox 客户端 -> 账号设置 -> API 访问令牌 |
| `APIFOX_PROJECT_ID` | 目标项目 ID | 项目概览页 -> 项目设置 -> 基本设置 -> ID |

## 🚀 使用方法

### 1. 与 Claude Desktop 配合使用

编辑 Claude Desktop 的配置文件 (通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json` 或 `%APPDATA%\Claude\claude_desktop_config.json`)，添加以下内容：

```json
{
  "mcpServers": {
    "apifox": {
      "command": "python",
      "args": [
        "/path/to/your/project/apifox_mcp/main.py"
      ],
      "env": {
        "APIFOX_TOKEN": "your_token_here",
        "APIFOX_PROJECT_ID": "your_project_id_here"
      }
    }
  }
}
```

请确保将 `/path/to/your/project` 替换为实际的项目路径，并填写正确的 Token 和 Project ID。

### 2. 作为独立 MCP 服务器运行

你也可以直接在命令行中运行它：

```bash
export APIFOX_TOKEN=your_token_here
export APIFOX_PROJECT_ID=your_project_id_here

# 只要 apifox_mcp 目录在 PYTHONPATH 中，或者在项目根目录下运行
mcp run apifox_mcp/main.py
```

## 📝 编写规范

本工具在创建和更新接口时强制执行以下规范，以确保文档质量：

1.  **中文描述**: 必须提供中文的 `title` 和 `description`。
2.  **完整 Schema**: `response_schema` 和 `request_body_schema` 中的每个字段必须包含 `description`。
3.  **真实示例**: 示例数据 (`example`) 必须是真实值，不能是简单的类型占位符 (如 "string")。
4.  **错误响应**: 系统会自动为你补充标准的 4xx/5xx 错误响应，无需手动定义。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
