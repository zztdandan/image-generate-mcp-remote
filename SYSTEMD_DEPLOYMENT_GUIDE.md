# systemd --user 远端 MCP 部署指南

本文档描述本项目作为**远端 MCP 服务**时的推荐部署、更新与运维方式。

本文档已去除个人隐私信息；所有路径均使用通用占位符表示。

补充说明：项目现在已经发布到 `PyPI`，除了源码部署外，也可以使用 `uvx` 或 `uv tool install image-generate-mcp-remote` 拉取已发布版本。

## 1. 适用场景

当前真实使用场景是：

- 通过 `systemd --user` 常驻运行
- 传输模式使用 `streamable-http`
- MCP 客户端通过 `url` 连接远端服务

这意味着它不是 `stdio` 直连模式。

## 2. 推荐目录约定

建议约定如下：

- 部署目录：`<deploy-root>`
- 环境变量文件：`<deploy-root>/.env`
- 虚拟环境入口：`<deploy-root>/.venv/bin/image-generate-mcp-remote`
- systemd unit：`~/.config/systemd/user/image-generate-mcp.service`

例如：

- `<deploy-root>` 可以是 `~/mcp/image-generate-mcp`

如果你希望固定到某个已发布版本，例如 `0.9.6`，推荐在部署目录中显式执行：

```bash
uv tool install --refresh image-generate-mcp-remote==0.9.6
```

或者临时验证某个版本：

```bash
uvx --from image-generate-mcp-remote==0.9.6 image-generate-mcp-remote --help
```

## 3. 当前部署模式对应的 unit 示例

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

上面这个示例表示：

- 传输模式：`streamable-http`
- 监听地址：`127.0.0.1`
- 监听端口：`25235`
- MCP 路径：`/mcp`

如果你希望对所有网卡监听，可把：

- `--host 127.0.0.1`

改为：

- `--host 0.0.0.0`

## 4. 为什么远端 MCP 不能靠客户端 `env` 改配置

这是 MCP 运行模式差异，不是本项目特例：

- `stdio`：客户端自己启动进程，客户端配置里的 `env` 会传给该进程
- `streamable-http` / `sse`：客户端只连接已启动服务，不会把 `env` 注入到服务端进程

所以对于当前这种远端服务部署：

- 改客户端 MCP JSON 里的 `env`，**不会**改变服务端配置
- 要改服务配置，必须改 `EnvironmentFile` 指向的 `.env`，或改 unit 本身

## 5. 环境变量如何配置

推荐在：`<deploy-root>/.env`

常见示例：

```dotenv
IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=...
IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL=https://api.openai.com/v1
IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL=gpt-image-2
IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS=gpt-image-2

IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=...
IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL=https://generativelanguage.googleapis.com
IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL=gemini-3.1-flash-image-preview
IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS=gemini-3.1-flash-image-preview

IMG_GEN_GPT_IMAGE_2_URL_API_KEY=...
IMG_GEN_GPT_IMAGE_2_URL_BASE_URL=https://www.right.codes/draw/v1
IMG_GEN_GPT_IMAGE_2_URL_MODEL=gpt-image-2-vip
IMG_GEN_GPT_IMAGE_2_URL_SUPPORTED_MODELS=gpt-image-2-vip

IMAGE_OUTPUT_DIR=storage/images
IMAGE_BASE_URL=
IMAGE_HTTP_TIMEOUT_SECONDS=180
LOG_LEVEL=INFO
```

修改步骤：

1. 编辑 `<deploy-root>/.env`
2. 保存后执行 `systemctl --user restart image-generate-mcp.service`
3. 用 `systemctl --user status image-generate-mcp.service` 确认重启成功

## 6. 如何更新代码

如果部署目录本身不是 Git 仓库，推荐这样理解更新流程：

1. 先把新代码同步到 `<deploy-root>`
2. 在部署目录执行依赖同步
3. 重启服务
4. 检查状态与日志

参考命令：

```bash
cd <deploy-root>
uv sync
systemctl --user restart image-generate-mcp.service
systemctl --user status image-generate-mcp.service
```

如果只是改 `.env` 而没有改代码，通常不需要 `uv sync`，直接重启即可。

## 7. 如何修改 systemd unit

unit 文件路径：`~/.config/systemd/user/image-generate-mcp.service`

适用场景：

- 改端口
- 改监听地址
- 改传输模式
- 改工作目录
- 改程序入口

修改步骤：

1. 编辑 `~/.config/systemd/user/image-generate-mcp.service`
2. 执行 `systemctl --user daemon-reload`
3. 执行 `systemctl --user restart image-generate-mcp.service`
4. 执行 `systemctl --user status image-generate-mcp.service`

常用命令：

```bash
systemctl --user daemon-reload
systemctl --user restart image-generate-mcp.service
systemctl --user status image-generate-mcp.service
journalctl --user -u image-generate-mcp.service -n 100 --no-pager
```

## 8. OpenCode 的 MCP JSON 如何配置

### 8.1 远端 `streamable-http`

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
注意，timeout为关键参数，生成图片一般需要3分钟/张，mcp工具默认重试3次，故最多可能12分钟出一张图（渠道不稳定情况下），如果不设置超时，默认为30秒，一定生成不了图片。
文档推荐值为 `500000` 毫秒（500 秒），符合常规重试时间；同时可在说明中补充极端情况下最长可能达到 12 分钟。
如果服务对外监听并通过其他域名或 IP 暴露，把上面的 `url` 改成实际可访问地址即可。

### 8.2 本地 `stdio`

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
        "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY": "sk-xxxx",
        "IMG_GEN_GPT_IMAGE_2_URL_API_KEY": "sk-xxxx",
        "IMAGE_OUTPUT_DIR": "storage/images",
        "IMAGE_HTTP_TIMEOUT_SECONDS": "600",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

注意：只有 `stdio` 这种客户端拉起进程的模式，`env` 才会直接生效到服务进程。
注意，timeout为关键参数，生成图片一般需要3分钟/张，mcp工具默认重试3次，故最多可能12分钟出一张图（渠道不稳定情况下），如果不设置超时，默认为30秒，一定生成不了图片。
生图调用耗时较长，`IMAGE_HTTP_TIMEOUT_SECONDS` 只控制本服务请求上游生图接口及下载图片的 HTTP 超时；如果客户端支持 MCP tool-call 超时配置，文档推荐显式配置为 `500000` 毫秒（500 秒），避免默认 `30` 秒过早超时；同时也应知道渠道极不稳定时最长可能接近 `12` 分钟。

## 9. 常见问题

### 9.1 改了客户端 JSON 但远端服务没变化

原因：

- 当前是远端服务模式，客户端只连 `url`
- 客户端 `env` 不会注入到已经运行中的服务进程

正确做法：

- 修改 `<deploy-root>/.env`
- 重启 `image-generate-mcp.service`

### 9.2 改了 `.env` 但配置还是旧的

通常原因：

- 修改后没有重启服务

正确做法：

```bash
systemctl --user restart image-generate-mcp.service
```

### 9.3 改了 unit 但服务参数没变化

通常原因：

- 修改后没有执行 `daemon-reload`

正确做法：

```bash
systemctl --user daemon-reload
systemctl --user restart image-generate-mcp.service
```

### 9.4 能否改成 `0.0.0.0`

可以。

本项目程序没有把 host 写死，`--host` 是 CLI 参数；当前是否对外开放取决于 unit 中的启动参数。

但如果改成 `0.0.0.0`，请同时评估：

- 防火墙
- 安全组
- 反向代理
- 认证与访问控制

## 10. 一句话操作指引

- 改模型、Key、Base URL：改 `<deploy-root>/.env`，然后 `restart`
- 改端口、host、transport：改 `~/.config/systemd/user/image-generate-mcp.service`，然后 `daemon-reload + restart`
- 远端接入：配实际可访问的 `http(s)://<host>:<port>/mcp`
- 当前真实部署模式：`streamable-http`
