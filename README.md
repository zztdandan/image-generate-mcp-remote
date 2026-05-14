# image-generate-mcp-remote

一个基于 UV + Python 的远程 MCP 图片生成服务，统一封装 OpenAI Images 兼容接口与 Gemini `generateContent` 生图接口。

> 本子项目运行时复用工作区根目录 `.venv`。在本目录执行 `uv` 命令时，会通过工作区环境注入使用统一虚拟环境。

> 注意，timeout为关键参数，生成图片一般需要3分钟/张，mcp工具默认重试3次，故最多可能12分钟出一张图（渠道不稳定情况下），如果不设置超时，默认为30秒，一定生成不了图片。
> 文档推荐将 MCP 客户端 `timeout` 显式设置为 `500000` 毫秒（500 秒）；这是常规重试场景下的推荐值，同时请知悉极端情况下最长仍可能到 12 分钟。

## 项目能力

- 提供 `gpt_image_2_official` 工具，兼容 OpenAI Images 风格的文生图与参考图编辑
- 提供 `nano_banana_2_official` 工具，兼容 Gemini `generateContent` 风格的文生图与参考图编辑
- 提供 `gpt-image-2-url` 工具，兼容 `https://www.right.codes/draw/v1/images/generations` 并自动下载返回图片 URL
- 提供 `list_image_tools_catalog` 工具，用于输出当前服务的默认配置、有效模型与非敏感环境变量信息
- 提供 `skills/gpt-icon-generate/SKILL.md` 图标生成技能，约定规则网格图标板生成、校验和切图流程
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

## 通过 uv / PyPI 安装使用

`uv` 本身没有单独的“官方包仓库”，常规做法是把包发布到 `PyPI`，然后让用户通过 `uv` 直接下载运行。

当前发布链路会把 GitHub Release 对应版本自动发布到 `PyPI`。

- PyPI 项目名：`image-generate-mcp-remote`
- 推荐临时运行：`uvx image-generate-mcp-remote --transport stdio`
- 推荐安装到工具目录：`uv tool install image-generate-mcp-remote`

例如，安装 `v0.9.4` 后可直接这样使用：

```bash
# 临时运行，不落本地项目源码
uvx image-generate-mcp-remote --transport stdio

# 或安装为全局工具
uv tool install image-generate-mcp-remote
image-generate-mcp-remote --transport stdio

# 指定版本
uvx --from image-generate-mcp-remote==0.9.4 image-generate-mcp-remote --transport stdio
```

## 从源码安装与启动

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
      "timeout": 500000,
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
      "url": "http://127.0.0.1:3001/mcp",
      "timeout": 500000
    }
  }
}
```

上面的 `timeout` 不要省略。注意，timeout为关键参数，生成图片一般需要3分钟/张，mcp工具默认重试3次，故最多可能12分钟出一张图（渠道不稳定情况下），如果不设置超时，默认为30秒，一定生成不了图片。文档示例推荐值为 `500000` 毫秒（500 秒），用于覆盖常规重试场景。

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

如果客户端还支持单独配置 MCP tool-call 超时，也应显式设置 `timeout`；文档推荐值为 `500000` 毫秒（500 秒），但在渠道极不稳定时，单张图最长仍可能接近 `12` 分钟。

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
- 支持显式传入 `timeout_seconds`，默认 `180` 秒
- 支持显式传入 `retry_count`，默认 `3`，表示失败后额外重试 3 次，总尝试次数为 4 次
- 若传入 `size="宽x高"`，服务会自动归一化到支持的 30 档常用尺寸后再请求上游
- 如传入无法解析的 `size`，错误信息会直接列出该工具支持的尺寸预设；也可先调用 `list_image_tools_catalog` 查看 `supported_size_presets`

### `nano_banana_2_official`

Gemini `generateContent` 兼容工具。

- `mode=generate` 时调用文生图
- `mode=edit` 时调用参考图编辑 / 图生图
- 默认请求上游：`https://www.uocode.com`
- 支持显式传入 `timeout_seconds`，默认 `180` 秒
- 支持显式传入 `retry_count`，默认 `3`，表示失败后额外重试 3 次，总尝试次数为 4 次

### `gpt-image-2-url`

URL 返回型 `gpt-image-2` 独立工具。

- 调用接口：`POST /images/generations`
- 默认请求上游：`https://www.right.codes/draw/v1`
- 默认模型：`gpt-image-2-vip`
- 该工具会向上游请求 `response_format=url`，上游返回 `https` 图片地址后，服务端会自动下载该 URL 并保存到 `save_path`；调用方不需要再手动下载
- 入参 `image` 是可选的参考图 URL 列表，不是输出图片 URL
- 返回结果继续复用统一 `ImageToolResult` 结构，保留耗时、token 使用量与上游响应摘要
- 支持显式传入 `timeout_seconds`，默认 `180` 秒
- 支持显式传入 `retry_count`，默认 `3`，表示失败后额外重试 3 次，总尝试次数为 4 次
- `size="宽x高"` 仅接受该 URL 工具支持的预设：全部 1K 共享尺寸，加上 `storage/images/benchmark-*` 中已实测通过的尺寸
- 如传入不支持的 `size`，错误信息会直接列出该工具支持的尺寸预设；也可先调用 `list_image_tools_catalog` 查看 `supported_size_presets`

## 内置技能

### `gpt-icon-generate`

- 技能文件：`skills/gpt-icon-generate/SKILL.md`
- 用途：批量图标板生成、规则网格校验、透明 PNG 切图、UI 图标库落盘
- 默认链路：优先使用 `gpt_image_2_official` 生成 `2K`、`1:1`、`4x4 / 16` 图标板
- 附带脚本：`skills/gpt-icon-generate/scripts/verify_image_output.py`、`skills/gpt-icon-generate/scripts/plan_icon_sheet_params.py`、`skills/gpt-icon-generate/scripts/split_icon_sheet_connected_bbox.py`

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
| `IMAGE_HTTP_TIMEOUT_SECONDS` | 否 | `180` | 服务端请求上游图片生成接口及下载图片的 HTTP 超时时间，单位秒；远端 MCP 客户端自身也可能有独立 tool-call 超时，需要在客户端侧另行配置，文档推荐 `timeout=500000` 毫秒（500 秒），并可补充说明极端情况下最长可能到 12 分钟 |
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

- GitHub Release：创建如 `v0.9.4` 的 release 后，会自动触发 `.github/workflows/release.yml`
- PyPI 发布：工作流使用 `uv build --no-sources` 与 `uv publish`
- Trusted Publishing：建议在 `PyPI` 中为仓库 `zztdandan/image-generate-mcp-remote` 配置 GitHub Actions trusted publisher，并将 workflow 文件名填写为 `release.yml`、environment 填写 `pypi`
- Token 回退方案：若暂不使用 Trusted Publishing，可在 GitHub 仓库 secrets 中配置 `UV_PUBLISH_TOKEN`，同一工作流会自动读取并发布

## 许可证

本项目采用 `MIT` 许可证，完整文本见 `LICENSE`。
