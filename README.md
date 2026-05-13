# image-generate-mcp-remote

一个基于 UV + Python 的远程 MCP 图片生成服务，统一封装 OpenAI Images 兼容接口与 Gemini `generateContent` 生图接口。

> 本子项目运行时复用工作区根目录 `.venv`。在本目录执行 `uv` 命令时，会通过工作区环境注入使用统一虚拟环境。

## 项目能力

- 提供 `gpt_image_2_official` 工具，兼容 OpenAI Images 风格的文生图与参考图编辑
- 提供 `nano_banana_2_official` 工具，兼容 Gemini `generateContent` 风格的文生图与参考图编辑
- 提供 `gpt-image-2-url` 工具，兼容 `https://www.right.codes/draw/v1/images/generations` 并自动下载返回图片 URL
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

## 通过 uv 安装使用

`uv` 本身没有单独的“官方包仓库”，常规做法是把包发布到 `PyPI`，然后让用户通过 `uv` 直接下载运行。

当 `v0.9.1` 发布到 `PyPI` 后，可直接这样使用：

```bash
# 临时运行，不落本地项目源码
uvx image-generate-mcp-remote --transport stdio

# 或安装为全局工具
uv tool install image-generate-mcp-remote
image-generate-mcp-remote --transport stdio
```

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

## 当前实际部署（systemd --user）

本项目当前真正使用中的远端 MCP 服务，不是 `stdio` 直连，而是 `systemd --user` 托管的 `streamable-http` 服务。

- 服务名：`image-generate-mcp.service`
- unit 文件位置模式：`~/.config/systemd/user/image-generate-mcp.service`
- 工作目录：部署目录 `<deploy-root>`
- 环境文件：`<deploy-root>/.env`
- 当前接入地址：`http://127.0.0.1:25235/mcp`

部署、更新、修改环境变量、重启服务、OpenCode MCP JSON 配置的完整说明见：

- `SYSTEMD_DEPLOYMENT_GUIDE.md`

对于当前这个远端服务，需要特别注意：

- 改 OpenCode MCP JSON 里的 `env`，不会改变已启动服务的环境变量
- 要改服务配置，必须修改 `<deploy-root>/.env` 或 `image-generate-mcp.service`
- 改 `.env` 后执行 `systemctl --user restart image-generate-mcp.service`
- 改 `.service` 后执行 `systemctl --user daemon-reload && systemctl --user restart image-generate-mcp.service`

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
- 若传入 `size="宽x高"`，服务会自动归一化到支持的 30 档常用尺寸后再请求上游

### `nano_banana_2_official`

Gemini `generateContent` 兼容工具。

- `mode=generate` 时调用文生图
- `mode=edit` 时调用参考图编辑 / 图生图
- 默认请求上游：`https://www.uocode.com`

### `gpt-image-2-url`

URL 返回型 `gpt-image-2` 独立工具。

- 调用接口：`POST /images/generations`
- 默认请求上游：`https://www.right.codes/draw/v1`
- 默认模型：`gpt-image-2-vip`
- 上游返回 `https` 图片地址后，服务会自动下载并保存到 `save_path`
- 返回结果继续复用统一 `ImageToolResult` 结构，保留耗时、token 使用量与上游响应摘要
- 仅接受共享的 30 档 `size="宽x高"` 预设尺寸

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

### GPT Image 2 URL 工具

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMG_GEN_GPT_IMAGE_2_URL_API_KEY` | 是 | 空 | `gpt-image-2-url` 使用的 API Key |
| `IMG_GEN_GPT_IMAGE_2_URL_BASE_URL` | 否 | `https://www.right.codes/draw/v1` | URL 返回型网关地址 |
| `IMG_GEN_GPT_IMAGE_2_URL_MODEL` | 否 | `gpt-image-2-vip` | 默认调用模型 |
| `IMG_GEN_GPT_IMAGE_2_URL_SUPPORTED_MODELS` | 否 | `gpt-image-2-vip` | 允许调用的模型白名单，逗号分隔 |

## 调试与验证

```bash
uv run pytest
```

## 发布说明

- GitHub Release：创建如 `v0.9.1` 的 release 后，会自动触发 `.github/workflows/release.yml`
- PyPI 发布：工作流使用 `uv build --no-sources` 与 `uv publish`
- Trusted Publishing：建议在 `PyPI` 中为仓库 `zztdandan/image-generate-mcp-remote` 配置 GitHub Actions trusted publisher，并将 workflow 文件名填写为 `.github/workflows/release.yml`

## 许可证

本项目采用 `MIT` 许可证，完整文本见 `LICENSE`。
