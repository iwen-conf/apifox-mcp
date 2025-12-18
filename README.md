# Apifox MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Compatible-purple?logo=python&logoColor=white)](https://docs.astral.sh/uv/)
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

    **使用 uv**
    ```bash
    uv venv
    # 激活虚拟环境
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

    **使用 venv**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **安装依赖**

    本项目支持使用 [uv](https://docs.astral.sh/uv/) (推荐用于本地开发) 或 pip 来安装依赖。

    **使用 uv (推荐，更快的本地开发)**
    ```bash
    # 安装 uv (如果尚未安装)
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # 安装依赖
    uv sync
    
    # 运行 MCP server
    uv run python -m apifox_mcp.main
    ```

    **使用 pip (传统方式)**
    ```bash
    pip install mcp[cli] requests
    
    # 运行 MCP server
    python -m apifox_mcp.main
    ```

## ⚙️ 配置

在使用前，你需要设置以下环境变量来连接你的 Apifox 项目。

| 环境变量 | 描述 | 获取方式 |
| :--- | :--- | :--- |
| `APIFOX_TOKEN` | Apifox 开放 API 令牌 | Apifox 客户端 -> 账号设置 -> API 访问令牌 |
| `APIFOX_PROJECT_ID` | 目标项目 ID | 项目概览页 -> 项目设置 -> 基本设置 -> ID |

## 重点⚠️
### APIFOX_TOKEN获取方式
<img width="1594" height="1029" alt="截屏2025-12-17 01 58 51" src="https://github.com/user-attachments/assets/aad5da36-a99d-484b-959c-116918897487" />


### APIFOX_PROJECT_ID获取方式

<img width="2032" height="1167" alt="截屏2025-12-17 01 57 06" src="https://github.com/user-attachments/assets/a381baf8-7da0-4d88-950c-ac8b78c7af8d" />


### 设置项目文档为公开
ps:我实际使用发现只有设置为文档发布才能正常操作项目

 <img width="1594" height="1029" alt="截屏2025-12-17 01 55 12" src="https://github.com/user-attachments/assets/59cb26ea-26af-47a4-8329-aabe4ec63bce" />



## ⚙️ 配置

在使用前，你需要获取以下凭证来连接你的 Apifox 项目。

| 环境变量 | 描述 | 获取方式 |
| :--- | :--- | :--- |
| `APIFOX_TOKEN` | Apifox 开放 API 令牌 | Apifox 客户端 -> 账号设置 -> API 访问令牌 |
| `APIFOX_PROJECT_ID` | 目标项目 ID | 项目概览页 -> 项目设置 -> 基本设置 -> ID |

## 🐳 使用方法 (Docker)

### 方法一：从源码构建

```bash
git clone https://github.com/iwen-conf/apifox-mcp.git
cd apifox-mcp
docker build -t apifox-mcp .
```

### 方法二：使用预构建镜像

从 [Releases](https://github.com/iwen-conf/apifox-mcp/releases) 下载 `apifox-mcp.tar`，然后加载：

```bash
docker load -i apifox-mcp.tar
```

### 配置 Claude Desktop

编辑 Claude Desktop 的配置文件：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### 方式一：使用 Docker (推荐用于生产环境)

```json
{
  "mcpServers": {
    "apifox": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "APIFOX_TOKEN",
        "-e", "APIFOX_PROJECT_ID",
        "apifox-mcp"
      ],
      "env": {
        "APIFOX_TOKEN": "your_token_here",
        "APIFOX_PROJECT_ID": "your_project_id_here"
      }
    }
  }
}
```

#### 方式二：使用 uv (推荐用于本地开发)

```json
{
  "mcpServers": {
    "apifox": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/apifox-mcp",
        "python",
        "-m",
        "apifox_mcp.main"
      ],
      "env": {
        "APIFOX_TOKEN": "your_token_here",
        "APIFOX_PROJECT_ID": "your_project_id_here"
      }
    }
  }
}
```

> **注意**: 
> - 请将 `your_token_here` 和 `your_project_id_here` 替换为你的实际凭证
> - 使用 uv 方式时，请将 `/path/to/apifox-mcp` 替换为实际的项目路径

### 3. 命令行运行 (可选)

你也可以直接在命令行中测试：

```bash
# 使用环境变量
docker run -i --rm \
  -e APIFOX_TOKEN=your_token \
  -e APIFOX_PROJECT_ID=your_project_id \
  apifox-mcp

# 或者使用 .env 文件
docker run -i --rm --env-file .env apifox-mcp
```

## 📝 编写规范

本工具在创建和更新接口时强制执行以下规范，以确保文档质量：

1.  **中文描述**: 必须提供中文的 `title` 和 `description`。
2.  **完整 Schema**: `response_schema` 和 `request_body_schema` 中的每个字段必须包含 `description`。
3.  **真实示例**: 示例数据 (`example`) 必须是真实值，不能是简单的类型占位符 (如 "string")。
4.  **错误响应**: 系统会自动为你补充标准的 4xx/5xx 错误响应，无需手动定义。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
