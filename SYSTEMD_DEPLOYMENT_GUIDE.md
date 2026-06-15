# systemd --user 远端 MCP 部署指南

本文档描述本项目作为**远端 MCP 服务**时的推荐部署、更新与运维方式。

本文档的当前结论是：

- **生产部署优先使用 wheel 安装到独立 `.venv`**
- **不要把源码仓 + editable venv 当成正式部署形态**
- 远端 `systemd --user` 服务应只依赖：wheel、`.venv`、`.env`、`storage/` 与 unit 文件

## 1. 适用场景

当前真实使用场景是：

- 通过 `systemd --user` 常驻运行
- 传输模式使用 `streamable-http`
- MCP 客户端通过 `url` 连接远端服务

这意味着它不是 `stdio` 直连模式。

## 2. 推荐部署目录

推荐把部署目录理解为**运行时目录**，而不是源码目录。

建议结构如下：

```text
<deploy-root>/
├── .env
├── .venv/
├── storage/
│   └── images/
└── wheels/
    └── image_generate_mcp_remote-<version>-py3-none-any.whl
```

例如：

- `<deploy-root>` 可以是 `~/mcp/image-generate-mcp`

其中：

- `.env`：服务环境变量
- `.venv`：仅用于运行当前 MCP 服务
- `storage/images`：图片落盘目录
- `wheels/`：归档已部署 wheel，便于回滚和审计

## 3. 为什么不推荐源码 + editable venv 当正式部署

源码部署虽然方便开发，但不适合作为正式服务形态，主要问题是：

- 服务实际行为直接受源码目录变更影响
- editable 安装可能出现版本元数据与实际源码不一致
- 运维侧很难明确回答“当前服务到底跑的是哪个构建产物”
- 回滚需要回滚整个源码树，不如 wheel 文件清晰

因此，当前推荐策略是：

- 在源码仓构建 wheel
- 把 wheel 复制到部署目录
- 用部署目录自己的 `.venv` 安装这个 wheel
- systemd 只启动该 `.venv` 里的入口脚本

## 4. 构建 wheel

在源码仓目录执行：

```bash
cd /path/to/image-generate-mcp-remote
uv build
```

构建成功后会得到：

- `dist/image_generate_mcp_remote-<version>-py3-none-any.whl`
- `dist/image_generate_mcp_remote-<version>.tar.gz`

生产部署使用 `.whl` 即可。

## 5. 首次部署（推荐流程）

假设：

- 源码仓：`/path/to/image-generate-mcp-remote`
- 部署目录：`<deploy-root>`
- 本次 wheel：`image_generate_mcp_remote-<version>-py3-none-any.whl`

推荐步骤：

```bash
mkdir -p <deploy-root>/wheels <deploy-root>/storage/images
cp /path/to/image-generate-mcp-remote/dist/image_generate_mcp_remote-<version>-py3-none-any.whl <deploy-root>/wheels/

uv venv <deploy-root>/.venv
uv pip install --python <deploy-root>/.venv/bin/python <deploy-root>/wheels/image_generate_mcp_remote-<version>-py3-none-any.whl
```

这样安装后：

- 代码从 `.venv/site-packages/` 读取
- 不再依赖部署目录中是否存在源码树
- `dist-info` 与实际安装版本一致

## 6. 当前部署模式对应的 unit 示例

```ini
[Unit]
Description=Image Generate MCP Remote Service
After=default.target

[Service]
Type=simple
WorkingDirectory=%h/mcp/image-generate-mcp
EnvironmentFile=%h/mcp/image-generate-mcp/.env
ExecStart=%h/mcp/image-generate-mcp/.venv/bin/image-generate-mcp-remote --transport streamable-http --host 127.0.0.1 --port 25235
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

这里的关键点是：

- `WorkingDirectory` 指向部署根目录，用于加载 `.env` 与相对路径 `storage/images`
- `ExecStart` 指向部署目录 `.venv` 中的入口脚本
- 入口脚本来自 wheel 安装结果，而不是 editable 源码注入

## 7. 环境变量如何配置

推荐在：`<deploy-root>/.env`

常见示例：

```dotenv
IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=...
IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET=openai_gpt_image_2

IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=...
IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET=google_nano_banana

IMAGE_OUTPUT_DIR=storage/images
LOG_LEVEL=INFO
```

正式 preset 工具当前真正使用的环境变量只有：

- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET`
- `IMAGE_OUTPUT_DIR`
- `LOG_LEVEL`

## 8. 已废弃的旧环境变量口径

下面这些旧变量不再是当前正式 preset 工具的部署入口：

- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS`
- `IMAGE_BASE_URL`
- `IMAGE_HTTP_TIMEOUT_SECONDS`

原因：

- `base_url`、`model`、`timeout`、`retry` 现在由 active preset 决定
- 如果要切换默认线路，应修改 `..._PRESET`
- 如果要按次临时切换，应在工具调用时传 `preset + api_key`

## 9. timeout / retry 的正确理解

当前正式 preset 的预算规则是：

- 统一只有 `1` 次默认机会 + `1` 次重试机会
- 即 `retry_count=1`，总尝试次数为 `2`
- 正式工具上游 HTTP timeout 不由 `.env` 控制，而由 active preset 决定

当前预算口径：

- 仅支持 `1K` 的 preset：`120s`
- 支持 `2K` 的 preset：`150s`
- 支持 `4K` 的 preset：`200s`

因此 MCP 客户端仍应显式配置较大的 tool-call timeout，推荐继续使用：

- `500000` 毫秒（500 秒）

## 10. 如何更新版本

推荐更新流程：

1. 在源码仓重新 `uv build`
2. 将新 wheel 复制到 `<deploy-root>/wheels/`
3. 用部署目录 `.venv` 重新安装该 wheel
4. 重启服务
5. 检查状态与日志

参考命令：

```bash
cp /path/to/source/dist/image_generate_mcp_remote-<version>-py3-none-any.whl <deploy-root>/wheels/
uv pip install --python <deploy-root>/.venv/bin/python --reinstall <deploy-root>/wheels/image_generate_mcp_remote-<version>-py3-none-any.whl
systemctl --user restart image-generate-mcp.service
systemctl --user status image-generate-mcp.service
```

如果只是改 `.env` 而没有改 wheel，则通常不需要重新安装，只需重启服务。

## 11. 如何修改 systemd unit

unit 文件路径：`~/.config/systemd/user/image-generate-mcp.service`

适用场景：

- 改端口
- 改监听地址
- 改传输模式
- 改工作目录
- 改程序入口

修改步骤：

```bash
systemctl --user daemon-reload
systemctl --user restart image-generate-mcp.service
systemctl --user status image-generate-mcp.service
```

常用命令：

```bash
systemctl --user daemon-reload
systemctl --user restart image-generate-mcp.service
systemctl --user status image-generate-mcp.service
journalctl --user -u image-generate-mcp.service -n 100 --no-pager
```

## 12. OpenCode 的 MCP JSON 如何配置

### 12.1 远端 `streamable-http`

```json
{
  "mcpServers": {
    "image-generate-mcp-remote": {
      "url": "http://127.0.0.1:25235/mcp",
      "timeout": 500000
    }
  }
}
```

### 12.2 本地 `stdio`

本地开发可以继续直接用源码仓 `uv run`；但这属于开发模式，不是生产部署模式。

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

## 13. 常见问题

### 13.1 改了客户端 JSON 但远端服务没变化

原因：

- 当前是远端服务模式，客户端只连 `url`
- 客户端 `env` 不会注入到已经运行中的服务进程

正确做法：

- 修改 `<deploy-root>/.env`
- 重启 `image-generate-mcp.service`

### 13.2 为什么 wheel 部署更适合生产

因为它能稳定回答三个问题：

- 当前运行的是哪个构建产物
- 当前 `.venv` 安装的是哪个版本
- 当前回滚应该回滚到哪个 wheel 文件

### 13.3 能否改成 `0.0.0.0`

可以，但请同时评估：

- 防火墙
- 安全组
- 反向代理
- 认证与访问控制

## 14. 一句话操作指引

- 开发调试：源码仓 `uv run`
- 正式部署：构建 wheel，安装到部署目录 `.venv`
- 改默认线路：改 `<deploy-root>/.env` 里的 `..._PRESET`，然后 `restart`
- 改默认 Key：改 `<deploy-root>/.env` 里的 `..._API_KEY`，然后 `restart`
- 改端口、host、transport：改 `~/.config/systemd/user/image-generate-mcp.service`，然后 `daemon-reload + restart`
