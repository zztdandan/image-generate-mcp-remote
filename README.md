# image-generate-mcp-remote

一个基于 UV + Python 的远程 MCP 图片生成服务，统一封装 OpenAI Images 兼容接口与 Gemini `generateContent` 生图接口。

> 本子项目运行时复用工作区根目录 `.venv`。在本目录执行 `uv` 命令时，会通过工作区环境注入使用统一虚拟环境。

> 注意，timeout为关键参数，生成图片一般需要3分钟/张，mcp工具默认重试3次，故最多可能12分钟出一张图（渠道不稳定情况下），如果不设置超时，默认为30秒，一定生成不了图片。
> 文档推荐将 MCP 客户端 `timeout` 显式设置为 `500000` 毫秒（500 秒）；这是常规重试场景下的推荐值，同时请知悉极端情况下最长仍可能到 12 分钟。

## 项目能力

- 提供 `gpt_image_2_official` 工具，兼容 OpenAI Images 风格的文生图与参考图编辑
- 提供 `nano_banana_2_official` 工具，兼容 Gemini `generateContent` 风格的文生图与参考图编辑
- 提供 `gpt_image_2_temporary` 与 `nano_banana_2_temporary` 临时探索工具，用于陌生兼容站点试跑；成功后应固化为正式 preset
- 提供 `list_image_tools_catalog` 工具，用于输出当前服务的 default-active preset、尺寸支持、参数指导与非敏感环境变量信息
- 提供 `skills/gpt-icon-generate/SKILL.md` 图标生成技能，约定规则网格图标板生成、校验和切图流程

## 启动期预设（Preset）

Provider、model、base_url、timeout、retry 及字段派发行为默认由启动期 preset 决定。

- `gpt_image_2_official` 与 `nano_banana_2_official` 允许按次传入 `preset` 与 `api_key` 做临时覆盖
- 如果按次传入 `preset`，则同一请求里必须同时传入 `api_key`
- 不传按次覆盖参数时，仍回退到环境变量配置的 preset 与 API Key

- 通过 `IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET` 选择 `gpt_image_2_official` 的 active preset，例如 `openai_gpt_image_2`、`right_codes_gpt_image_2`、`apiyi_gpt_image_2`、`laozhang_gpt_image_2_default`、`laozhang_gpt_image_2_sora_official`、`laozhang_gpt_image_2_enterprise`、`laozhang_gpt_image_2_vip`
- 通过 `IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET` 选择 `nano_banana_2_official` 的 active preset，默认 `google_nano_banana`
- 不配置时回退到内置默认 preset（`openai_gpt_image_2` / `google_nano_banana`）

典型接口：
  - `POST /v1/images/generations`
  - `POST /v1/images/edits`
  - `POST /v1beta/models/{model}:generateContent`

## 通过 uv / PyPI 安装使用

`uv` 本身没有单独的“官方包仓库”，常规做法是把包发布到 `PyPI`，然后让用户通过 `uv` 直接下载运行。

当前发布链路会把 GitHub Release 对应版本自动发布到 `PyPI`。

- PyPI 项目名：`image-generate-mcp-remote`
- 推荐安装到工具目录：`uv tool install image-generate-mcp-remote`
- 推荐阅读真实部署与 MCP 配置导览：`./SYSTEMD_DEPLOYMENT_GUIDE.md`

例如，安装 `v0.9.6` 后可用于远端 MCP 服务部署或供 MCP 客户端以 `stdio` 模式拉起：

```bash
# 安装为全局工具
uv tool install image-generate-mcp-remote

# 指定版本
uv tool install --refresh image-generate-mcp-remote==0.9.6
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
```

这里不再单列 `stdio` 的独立启动命令；对本项目而言，`stdio` 的意义在于由 MCP 客户端按配置拉起，而不是人工单独启动。真正的 MCP 配置导览请直接看 `./SYSTEMD_DEPLOYMENT_GUIDE.md`。

## 当前实际部署（systemd --user）

本项目当前真正使用中的远端 MCP 服务，不是 `stdio` 直连，而是 `systemd --user` 托管的 `streamable-http` 服务。

- 服务名：`image-generate-mcp.service`
- unit 文件位置模式：`~/.config/systemd/user/image-generate-mcp.service`
- 工作目录：部署目录 `<deploy-root>`
- 环境文件：`<deploy-root>/.env`
- 当前接入地址：`http://127.0.0.1:25235/mcp`

部署、更新、修改环境变量、重启服务、OpenCode MCP JSON 配置的完整说明见：

- `./SYSTEMD_DEPLOYMENT_GUIDE.md`

对于当前这个远端服务，需要特别注意：

- 改 OpenCode MCP JSON 里的 `env`，不会改变已启动服务的环境变量
- 要改服务配置，必须修改 `<deploy-root>/.env` 或 `image-generate-mcp.service`
- 改 `.env` 后执行 `systemctl --user restart image-generate-mcp.service`
- 改 `.service` 后执行 `systemctl --user daemon-reload && systemctl --user restart image-generate-mcp.service`

## MCP 配置方式

以下配置示例均为当前项目可直接使用的正确写法。

如果你关注的是真实远端部署、systemd 托管、客户端如何接入在线 MCP 服务，建议优先阅读 `./SYSTEMD_DEPLOYMENT_GUIDE.md`；本节仅保留最常见配置摘要。

### 方式一：通用 stdio 直连（推荐本地开发）

适用于使用通用 MCP 配置风格的客户端，主要是 claude code

```json
{
  "mcpServers": {
    "image-generate-mcp-remote": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "image-generate-mcp-remote",
        "--transport",
        "stdio"
      ],
      "timeout": 500000,
      "cwd": "/Users/zhongting/workspace/image-generate-mcp-remote",
      "env": {
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET": "openai_gpt_image_2",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET": "google_nano_banana",
        "IMAGE_OUTPUT_DIR": "storage/images",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 方式二：OpenCode 本地 stdio 直连

OpenCode 的 `opencode.json` 使用自己的 MCP 配置结构：本地 MCP 需要声明 `type: "local"`，并把启动命令和参数合并写入 `command` 数组；环境变量字段名是 `environment`，不是通用示例里的 `env`；OpenCode 也不使用 `mcpServers` 作为顶层字段，而是使用 `mcp`。

适用于项目级配置文件，例如：`<project>/.opencode/opencode.json`。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "image-generate-mcp-remote": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--directory",
        "/absolute/path/to/image-generate-mcp-remote",
        "image-generate-mcp-remote",
        "--transport",
        "stdio"
      ],
      "enabled": true,
      "timeout": 500000,
      "environment": {
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET": "openai_gpt_image_2",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET": "google_nano_banana",
        "IMAGE_OUTPUT_DIR": "storage/images",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

两种 stdio 配置的区别：

- 通用 MCP 客户端常见字段：`mcpServers.command + args + cwd + env`
- OpenCode 字段：`mcp.<name>.type=local + command[] + environment`
- 两者启动的是同一个本地 MCP server，差异只在客户端配置 schema，不是服务端能力差异
- 图片生成务必保留较长的客户端侧 `timeout`，推荐 `500000` 毫秒

### 方式三：Streamable HTTP 远程接入

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

### 方式四：SSE 远程接入

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
- provider、model、base_url、timeout、retry 及字段派发默认由启动期 preset 决定
- 可按次传入 `preset` 与 `api_key` 临时切换 preset；若传 `preset`，必须同传 `api_key`
- 尺寸输入统一为 `image_size` + `aspect_ratio` 两个枚举，preset 按共享尺寸合同映射到对应 GPT 请求像素尺寸
- 支持解析 `data[0].b64_json` 与 `data[0].url`；若上游返回 `url`，服务端会自动下载并保存到 `save_path`
- 如传入不支持的枚举组合，错误信息会直接列出该工具支持的尺寸预设；也可先调用 `list_image_tools_catalog` 查看 `supported_size_presets`

### `nano_banana_2_official`

Gemini `generateContent` 兼容工具。

- `mode=generate` 时调用文生图
- `mode=edit` 时调用参考图编辑 / 图生图
- provider、model、base_url、timeout、retry 及字段派发默认由启动期 preset 决定
- 可按次传入 `preset` 与 `api_key` 临时切换 preset；若传 `preset`，必须同传 `api_key`
- 鉴权请求头同时发送 `Authorization: Bearer <key>` 与 `x-goog-api-key: <key>` 以兼容更多 Gemini 兼容网关
- 响应解析兼容 `inlineData` / `inline_data` 与 `mimeType` / `mime_type`
- 尺寸输入统一为 `image_size` + `aspect_ratio` 两个枚举，服务会按共享尺寸合同映射到 `imageConfig`
- 共享尺寸合同已同时记录 `gpt` 请求尺寸与 `nano banana` 实际输出尺寸

### `gpt_image_2_temporary`

OpenAI Images 兼容站点的临时探索工具。

- 允许按次传入 `api_key`、`base_url`、`model`、`timeout_seconds`
- 默认只发送保守字段：`model`、`prompt`、由 `image_size + aspect_ratio` 映射得到的 `size`
- `quality`、`output_format`、`background`、`moderation` 默认不发送；只有显式设置对应 `send_*` 参数时才转发
- 不进入 preset registry，不应作为生产默认工具；试跑成功后应新增 provider guide 与正式 preset class
- 输出检测兼容常见 `b64_json`、`url`、markdown 图片链接、data URL 等形态

### `nano_banana_2_temporary`

Gemini `generateContent` 兼容站点的临时探索工具。

- 允许按次传入 `api_key`、`base_url`、`model`、`timeout_seconds`
- 默认发送文本 prompt 与保守 `generationConfig.imageConfig`
- 不进入 preset registry，不应作为生产默认工具；试跑成功后应新增 provider guide 与正式 preset class
- 输出检测兼容 Gemini `inlineData` / `inline_data`，也会扫描文本中的 markdown 图片链接、data URL 与 HTTPS URL

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
| `IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET` | 否 | `openai_gpt_image_2` | 启动期 active preset id |

### Nano Banana 工具

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY` | 是 | 空 | `nano_banana_2_official` 使用的 API Key |
| `IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET` | 否 | `google_nano_banana` | 启动期 active preset id |

### 通用变量

| 变量名 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `IMAGE_OUTPUT_DIR` | 否 | `storage/images` | 生成图片的落盘目录 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |


## 许可证

本项目采用 `MIT` 许可证，完整文本见 `LICENSE`。
