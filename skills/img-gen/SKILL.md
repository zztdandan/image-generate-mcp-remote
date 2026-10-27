---
name: img-gen
description: "Generate or edit images with GPT-Image 2.5 (default $0.03/image flat VIP routes) and Nano Banana 2 via direct HTTP API calls. Replaces MCP image-generate-mcp-remote."
version: 2.3.1
license: Proprietary. Internal project skill.
platforms: [linux]
prerequisites:
  commands: ["python3"]
  env: ["IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY | IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY"]
setup:
  help: "Export IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY and/or IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY in the environment that starts the host (DSH injects them at launch). If neither is set, stop and ask the user to set them — do not guess a key or fall back to a file."
metadata:
  hermes:
    tags:
      - image-generation
      - gpt-image-2
      - gpt-image-2-5
      - nano-banana
      - gemini
      - creative
      - generative-ai
    related_skills: [gpt-icon-generate]
    category: design
---

# img-gen — 直接图像生成

通过**进程环境变量**读取 API key，直接发起 HTTP 请求生成/编辑图片。
不依赖 MCP 中间层，也不读取任何 `.env` 文件。

## 适用范围

- 用户要求生成图片（GPT-Image 2.5 / Nano Banana 2）
- 用户要求编辑已有图片
- gpt-icon-generate 等依赖生图能力的技能的下层实现

## 配置门禁（先读这一节）

技能只认进程环境变量。变量由宿主在启动时注入（DSH 启动时注入，见「环境配置」），
技能自身不解析文件、不落盘、不缓存 token。

每次任务开始先跑：

```bash
python3 scripts/check_env.py        # 或 python3 scripts/img_gen.py check
```

- **两个 key 都是 ✗ → 停下，不要继续。** 直接告诉用户缺哪个变量，并给出可复制的
  `export ...`（或「启动 DSH 前注入」）做法，等用户补齐后再重跑本检查。
  这一条优先于其它所有步骤：不要猜 key、不要去翻别人的配置文件、不要换 provider
  硬试、不要因为「上次能用」就假设这次也有。
- **至少一个 ✓ → 继续**，默认走 `--preset auto`。
- 只有 nano-banana 的 key 时，`generate` 仍可跑 Gemini 协议 preset（`--preset` 显式指定，
  或 auto 链里只剩 banana 路线）。

## 计费模型与默认路线

| 路线 | 模型名 | 计费 | 定位 |
|------|--------|------|------|
| **便宜路线** | `gpt-image-2.5-vip`（别名 sunburst-vip）、`-flare-vip`、`-sunburst-vip`、`gpt-image-2-vip` | **$0.03/张，按次**；1K/2K/4K 与 quality 都不加价 | 日常唯一默认 |
| 贵路线 | `gpt-image-2.5-flare` / `-sunburst`、`gpt-image-2`（无 `-vip`） | 官转，按输出 token 计费，明显更贵 | 最后手段 |

规则：

1. **默认用 `--preset auto`**（不写 `--preset` 即是 auto）。auto 只走 $0.03/张 的
   `-vip` 路线，顺序为 apiyi → laozhang，同价互为备份。
2. **不要主动用贵路线。** 贵路线 preset 标记为 `tier=last_resort`，只有两种入口：
   显式写 preset 名，或 auto 加 `--allow-expensive`。CLI 命中时会打印
   `[!] LAST-RESORT ROUTE` 警告。
3. 只有当所有 $0.03 路线都失败（配额不足、分组饱和、5xx、超时）时才考虑
   `--allow-expensive`；用了必须在交付说明里写明「本次走了按 token 计费的官转路线」。
4. 参数写错（HTTP 400）**不换路线重试**——所有路线都会同样失败，直接改参数。

### 当前实测状态（2026-10-26）

- apiyi `apiyi_gpt_image_2_5_vip`（`gpt-image-2.5-vip`）实测可用：
  1280×720 + low 生成 29.9 s，2048×1152 + low 编辑 29.8 s，1280×1280 + url 响应
  39.6 s，返回尺寸与请求逐像素一致。
- 同一 key 当天早些时候曾报 `403 配额不足 / insufficient_quota`，随后恢复——说明该错误
  是账号配额波动。**auto 链遇到 403 会自动落到下一条同价路线，无需改配置。**
- laozhang 网关在 02:11 可用（27 s 出图），02:20 起对本机 TLS 直接断连
  （`SSL: UNEXPECTED_EOF_WHILE_READING`，openssl 握手同样被 reset）。这是 laozhang 侧
  的可用性问题，不是技能代码问题；laozhang 的 `-vip` preset 仍保留为同价备份。
- 环境变量 `IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET` 现为 `apiyi_gpt_image_2_5_vip`
  （$0.03/张）。

## 技能文件

所有脚本为技能自包含：

```
scripts/
├── img_gen.py              ← 统一 CLI（check / generate / edit），--preset auto 链路
├── check_env.py            ← 环境变量检测（缺变量时给出具体设置指引）
├── lib/
│   ├── presets.py          ← preset 目录 + tier/计费/quality/size 校验 + auto 链
│   ├── openai_images.py    ← OpenAI Images 协议（360 s 超时、url/b64 双兜底）
│   └── gemini_gen.py       ← Gemini generateContent 协议
└── presets/
    ├── gpt/    (20 个)     ← 每个 preset 一个 Python 封装
    └── banana/ (3 个)
```

> 图标板生成流程见同仓库的 `skills/gpt-icon-generate`（本技能只负责下层生图）。

## 快速开始

### Step 1 — 检测环境

```bash
python3 scripts/check_env.py          # 或 python3 scripts/img_gen.py check
```

从进程环境变量读取配置，确认 key 存在，并打印 auto 链路顺序、每个 preset 的 tier
与单价。不打印 token 值。缺变量时按「配置门禁」停下并让用户补齐。

### Step 2 — 生成图片（默认便宜路线）

```bash
# auto：依次尝试 apiyi → laozhang 的 $0.03/张 -vip 路线
python3 scripts/img_gen.py generate \
    --prompt "A futuristic steel plant" \
    --save output.png --size 2K --ratio 16:9

# 指定同价路线（跳过自动回退）
python3 scripts/img_gen.py generate \
    --preset laozhang_gpt_image_2_5_flare_vip \
    --prompt "..." --save out.png --size 1K --ratio 16:9 --quality low

# 精确像素（必须是 30 档之一）
python3 scripts/img_gen.py generate --prompt "..." --save out.png --size-px 2048x1152

# 透明底图标
python3 scripts/img_gen.py generate --prompt "linear icon of a sensor, flat, single object" \
    --save icon.png --size 1K --ratio 1:1 --background transparent --output-format png
```

### Step 3 — 编辑图片

```bash
python3 scripts/img_gen.py edit \
    --image input.png --prompt "Add blue sky" \
    --save edited.png --size 2048x1152
```

> ⚠️ **edit 必传 model**：`openai_images.edit` 的 multipart 里必须发送 `model`（脚本已自动传入 `cfg["model"]`）。若缺省，转发网关会回退到 `dall-e-2` 并报 `no available channels for model dall-e-2`，且 `dall-e-2` 不支持大尺寸会连锁抛 `size not supported`。症状看似 size 问题，根因其实是 model 缺失。
>
> **edit 的 size 与 2K**：省略 `--size` 时 apiyi 不会沿用输入图尺寸，而是回落到约 1120px 长边的缩略图（例：输入 1632×2048 → 1120×1405）。要 2K 成品就显式传 30 档里的像素，例如 `--size 2048x1152`、`--size 1632x2048`。table30 preset 会校验，传表外尺寸直接报错，而不是被上游悄悄改写。
>
> **edit 只支持单图**：multipart 只发一个 `image` 字段，无法「原图 + 风格参考图」同时传。需要多图融合时把风格写成文字，或先手工合成一张输入图。
>
> **输入图体积**：单张 >1.5 MB 时 CLI 打印警告。大图容易触发 `shell_api_error` / 超时；输出画质由 `size` 决定，压小输入不会降画质。
>
> **mask 不精确**：三款 -vip 接受 `mask` 但基本整图重绘；需要精确局部重绘只能换官转 `gpt-image-2.5/2`（更贵），不属于本技能默认范围。
>
> **超时**：默认 360 s（`--timeout` 可调）。图片接口是同步调用，没有任务 ID，客户端断开结果即丢但照常计费——不要为了「快点失败」把超时调低。

## 尺寸

3 档（1K / 2K / 4K）× 10 种宽高比 = 30 档，恰好等于 apiyi 文档的 30 档表，详见
`references/size-mapping.md`。

- 草稿/试稿：1K；终稿：2K；印刷/大屏：4K（4K 同价，但偶发 500，优先降到 2K 重试）。
- 写法必须半角小写 `x`（`2048x1152`），不要全角或大写 `X`。
- table30 preset（所有 `-vip`）传表外尺寸会被上游按 16 倍数重对齐，CLI 会直接拒绝。

## quality

- 2.5 系列：`auto` / `low` / `medium` / `high` / `xhigh` / `max` 六档。
- `gpt-image-2-vip`：只到 `high`，传 `xhigh` / `max` 会被上游拒绝（CLI 提前拦截）。
- 档位对齐：2.5 的 `high` ≈ 2-vip 的 `medium`，2.5 的 `max` ≈ 2-vip 的 `high`。
- 不写 `--quality` 就不发该字段，让上游用默认；不要传空字符串。

## 响应格式、重试与花费

- `response_format` **总是显式发送**，默认 `b64_json`；`--response-format url` 时 CLI
  立即下载并落盘（CDN 链接约 24 h 失效）。
- `b64_json` 兼容带 `data:` 前缀与不带两种历史行为。
- `n` 永远是 1：传 `n=3` 会按 3 张扣费但仍只返回 1 张。
- 5xx 与「上游负载已饱和」的 429 自动重试 1 次；`403 insufficient_quota` 不重试，
  直接在 auto 链里换下一条同价路线。
- 每张图独立计费：1K 和 4K 都是 $0.03，所以调试用 1K，别用大图试错。

## Preset 脚本

每个 preset 有独立封装（自动带上自身 preset 名）：

```bash
python3 scripts/presets/gpt/apiyi_gpt_image_2_5_vip.py generate --prompt "..." --save out.png
python3 scripts/presets/gpt/laozhang_gpt_image_2_5_sunburst_vip.py edit \
    --image in.png --prompt "..." --save out.png --size 2048x1152
python3 scripts/presets/banana/laozhang_nano_banana_pro.py generate --prompt "..." --save out.png
```

## 环境配置

技能只读**进程环境变量**，不读 `.env` 文件，也不绑定任何 profile 路径。
变量由宿主在启动时提供：

```bash
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=<token>
export IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET=apiyi_gpt_image_2_5_vip
export IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=<token>
export IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET=apiyi_nano_banana_2
export IMAGE_OUTPUT_DIR=<绝对路径>      # 可选，默认 ~/images
```

- **DSH**：把这些变量写进 Harness home 的 `~/.dsh/.env`（或调用 `dsh` 时所在目录的 `.env`）。
  dsh 启动时按「继承的进程环境 > 工作目录 `.env` > `~/.dsh/.env`」分层加载，并物化进
  `process.env`，会话里派生的 shell / 脚本直接继承。已存在的同名环境变量优先，文件不覆盖它；
  `DSH_*` / `XDG_*` 等启动期变量不允许写进文件，会被启动期校验拒绝并报错。
- **其它宿主**：`systemd` 环境、CI 变量或 `set -a; source <secrets>; set +a` 后启动宿主，效果相同。
- **一次性会话**：`export` 后在同一 shell 里调用脚本即可。
- 只确认变量非空：空字符串等同未设置（防止 `export VAR=` 伪装成已配置）。
- **安全说明**：技能不打印 token 值、不把变量写回磁盘；凭据只以环境变量形式存在于进程内。
- 变量缺失时的行为：`check_env.py` / `img_gen.py check` 退出码 1，并打印缺哪几个变量；
  调用方按「配置门禁」停下并提醒用户设置，不要自行编造。

## 支持的 Preset

23 个 preset，详见 `references/presets.md`。按 tier 分：

| tier | 含义 | 代表 preset |
|------|------|-------------|
| `preferred` | $0.03/张按次，日常默认 | `apiyi_gpt_image_2_5_vip`、`laozhang_gpt_image_2_5_sunburst_vip`、`..._flare_vip` |
| `standard` | 其它厂商/实验线路 | `laozhang_gpt_image_2_vip`、`right_codes_*`、`copperai_*`、banana 系列 |
| `last_resort` | 官转按 token，**贵**，仅最后手段 | `apiyi_gpt_image_2_5_flare`、`laozhang_gpt_image_2_5_sunburst`、`laozhang_gpt_image_2_default` 等 |

## Per-preset 覆盖（多厂商 key / base_url）

每个 preset 可独立指定 key 与 base_url，优先于 family 级配置：

```
IMG_GEN_PRESET_<PRESET_ID_UPPER>_API_KEY=<token>
IMG_GEN_PRESET_<PRESET_ID_UPPER>_BASE_URL=<url>
```

解析优先级：preset 专属键 > provider 级键（apiyi 依次读 `APIYI_API_KEY` /
`IMG_GEN_APIYI_API_KEY` / `IMG_GEN_PRESET_APIYI_GPT_IMAGE_2_5_FLARE_API_KEY`）> family 级键。
因此新增 apiyi preset 不需要把 key 再抄一份进环境变量。
`IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET` 只决定「默认/激活」预设；`--preset <id>`
显式指定的 preset 一律按其自身 base_url/key 走。

## 与 MCP 的对应关系

| 旧 MCP 调用 | 新技能替代 |
|------------|-----------|
| `mcp__image_generate_mcp_remote__gpt_image_2_official` | `img_gen.py generate`（auto → $0.03 路线） |
| `mcp__image_generate_mcp_remote__nano_banana_2_official` | `img_gen.py generate --preset laozhang_nano_banana_pro` |
| `...list_image_tools_catalog_tool` | `img_gen.py check` |
| `...list_image_presets_tool` | `img_gen.py check` |

## 依赖

- Python 3.9+（仅标准库，无 pip 依赖）
- 进程环境变量中至少有 `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY` 或
  `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY` 之一
