# image-generate-mcp-remote

一个基于 UV + Python 的远程 MCP 图片生成服务，统一封装 OpenAI Images 兼容接口与 Gemini `generateContent` 生图接口。

> 本子项目运行时复用工作区根目录 `.venv`。在本目录执行 `uv` 命令时，会通过工作区环境注入使用统一虚拟环境。

## 项目能力

- 提供 `gpt_image_2_official` 工具，兼容 OpenAI Images 风格的文生图与参考图编辑
- 提供 `nano_banana_2_official` 工具，兼容 Gemini `generateContent` 风格的文生图与参考图编辑
- 提供 `list_image_tools_catalog` 工具，用于输出当前服务的默认配置、有效模型与非敏感环境变量信息
- 默认网关已切换到 `uocode`

## 默认上游配置

### OpenAI Images 兼容

- 默认 `BASE_URL`：`https://www.uocode.com/v1`
- 默认模型：`gpt-image-2`
- 典型接口：
  - `POST /v1/images/generations`
  - `POST /v1/images/edits`

### Gemini 原生兼容

- 默认 `BASE_URL`：`https://www.uocode.com`
- 默认模型：`gemini-3.1-flash-image-preview`
- 典型接口：
  - `POST /v1beta/models/{model}:generateContent`

## 安装与启动

### 1. 安装依赖

```bash
uv sync
cp .env.example .env
```

### 2. 配置环境变量

至少填写你要使用的工具对应 API Key：

- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY`

### 3. 启动服务

```bash
# Streamable HTTP（默认）
uv run image-generate-mcp-remote --transport streamable-http --host 127.0.0.1 --port 3001

# SSE
uv run image-generate-mcp-remote --transport sse --host 127.0.0.1 --port 3001

# stdio（本地 MCP 客户端直连）
uv run image-generate-mcp-remote --transport stdio
```

## MCP 配置方式

以下配置示例均为当前项目可直接使用的正确写法。

### 方式一：stdio 直连（推荐本地开发）

适用于大多数支持本地命令启动 MCP Server 的客户端。

```json
{
  "mcpServers": {
    "image-generate-mcp-remote": {
      "command": "uv",
      "args": [
        "run",
        "image-generate-mcp-remote",
        "--transport",
        "stdio"
      ],
      "cwd": "/absolute/path/to/image-generate-mcp-remote",
      "env": {
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL": "https://www.uocode.com/v1",
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL": "gpt-image-2",
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS": "gpt-image-2",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL": "https://www.uocode.com",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL": "gemini-3.1-flash-image-preview",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS": "gemini-3.1-flash-image-preview",
        "IMAGE_OUTPUT_DIR": "storage/images",
        "IMAGE_BASE_URL": "",
        "IMAGE_HTTP_TIMEOUT_SECONDS": "600",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 方式二：Streamable HTTP 远程接入

先启动服务：

```bash
uv run image-generate-mcp-remote --transport streamable-http --host 127.0.0.1 --port 3001
```

服务默认 MCP 路径为：`/mcp`

```json
{
  "mcpServers": {
    "image-generate-mcp-remote": {
      "url": "http://127.0.0.1:3001/mcp"
    }
  }
}
```

### 方式三：SSE 远程接入

先启动服务：

```bash
uv run image-generate-mcp-remote --transport sse --host 127.0.0.1 --port 3001
```

服务默认路径为：

- SSE 入口：`/sse`
- 消息通道：`/messages/`

对于要求分别填写 SSE 地址与消息地址的客户端，可使用：

- `http://127.0.0.1:3001/sse`
- `http://127.0.0.1:3001/messages/`

## 工具列表

### `list_image_tools_catalog`

输出当前服务暴露的图片工具目录，包括：

- 默认网关地址
- 当前有效模型
- 支持模型列表
- 非敏感环境变量生效值

### `gpt_image_2_official`

OpenAI Images 兼容工具。

- `mode=generate` 时调用文生图
- `mode=edit` 时调用参考图编辑 / 图生图
- 默认请求上游：`https://www.uocode.com/v1`

### `nano_banana_2_official`

Gemini `generateContent` 兼容工具。

- `mode=generate` 时调用文生图
- `mode=edit` 时调用参考图编辑 / 图生图
- 默认请求上游：`https://www.uocode.com`

## 环境变量说明

### GPT Image 工具

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY` | 是 | 空 | `gpt_image_2_official` 使用的 API Key |
| `IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL` | 否 | `https://www.uocode.com/v1` | OpenAI Images 兼容网关地址 |
| `IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL` | 否 | `gpt-image-2` | 默认调用模型 |
| `IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS` | 否 | `gpt-image-2` | 允许调用的模型白名单，逗号分隔 |

### Nano Banana 工具

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY` | 是 | 空 | `nano_banana_2_official` 使用的 API Key |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL` | 否 | `https://www.uocode.com` | Gemini 原生兼容网关地址 |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL` | 否 | `gemini-3.1-flash-image-preview` | 默认调用模型 |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS` | 否 | `gemini-3.1-flash-image-preview` | 允许调用的模型白名单，逗号分隔 |

### 通用变量

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMAGE_OUTPUT_DIR` | 否 | `storage/images` | 生成图片的落盘目录 |
| `IMAGE_BASE_URL` | 否 | 空 | 若需要对外暴露图片 URL，可配置对应静态资源基地址 |
| `IMAGE_HTTP_TIMEOUT_SECONDS` | 否 | `600` | 上游图片生成请求超时时间，单位秒 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |

## 调试与验证

```bash
uv run pytest
```

## 许可证

本项目采用 `MIT` 许可证，完整文本见 `LICENSE`。
