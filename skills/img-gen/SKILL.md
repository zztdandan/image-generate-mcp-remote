---
name: img-gen
description: "Generate or edit images with GPT Image 2 and Nano Banana 2 via direct HTTP API calls. Replaces MCP image-generate-mcp-remote."
version: 2.0.0
license: Proprietary. Internal project skill.
platforms: [linux]
prerequisites:
  commands: ["python3"]
setup:
  help: "Ensure OS environment variables IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY and/or IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY are set."
metadata:
  hermes:
    tags:
      - image-generation
      - gpt-image-2
      - nano-banana
      - gemini
      - creative
      - generative-ai
    related_skills: [gpt-icon-generate]
    category: design
---

# img-gen — 直接图像生成

通过 OS 环境变量读取 API key，直接发起 HTTP 请求生成/编辑图片。
不依赖 MCP 中间层，不依赖任何 .env 文件。

## 适用范围

- 用户要求生成图片（GPT Image 2 / Nano Banana 2）
- 用户要求编辑已有图片
- gpt-icon-generate 等依赖生图能力的技能的下层实现

## 技能文件

所有脚本为技能自包含：

```
scripts/
├── img_gen.py              ← 统一 CLI（check / generate / edit）
├── check_env.py            ← .env 配置检测
├── lib/
│   ├── presets.py          ← 13 个 preset 配置 + 尺寸映射 + .env 加载
│   ├── openai_images.py    ← OpenAI Images 协议
│   └── gemini_gen.py       ← Gemini generateContent 协议
└── presets/
    ├── gpt/    (10 个)     ← 每个 preset 一个 Python 封装
    └── banana/ (3 个)
```

## 快速开始

### Step 1 — 检测环境

```bash
python3 scripts/check_env.py
```

从 OS 环境变量读取配置，确认 API key 存在，报告各渠道可用状态。
不打印 token 值。如果失败，检查环境变量是否设置。

### Step 2 — 生成图片

```bash
# 使用 GPT preset
python3 scripts/img_gen.py generate \
    --preset laozhang_gpt_image_2_default \
    --prompt "A futuristic steel plant" \
    --save output.png --size 2K --ratio 16:9

# 使用 Banana preset
python3 scripts/img_gen.py generate \
    --preset laozhang_nano_banana_pro \
    --prompt "传统中式园林" \
    --save garden.png --size 4K --ratio 16:9
```

### Step 3 — 编辑图片

```bash
python3 scripts/img_gen.py edit \
    --preset laozhang_gpt_image_2_default \
    --image input.png --prompt "Add blue sky" \
    --save edited.png
```

### Preset 专属脚本

每个 preset 有独立 Python 封装：

```bash
python3 scripts/presets/gpt/laozhang_gpt_image_2_default.py generate --prompt "..." --save out.png
python3 scripts/presets/banana/laozhang_nano_banana_pro.py generate --prompt "..." --save out.png
```

## 环境配置

通过 OS 环境变量配置（无需 .env 文件）：

```
IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=<token>
IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET=laozhang_gpt_image_2_default
IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=<token>
IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET=laozhang_nano_banana_pro
IMAGE_OUTPUT_DIR=/home/base/images
```

**安全说明**：技能检测仅确认环境变量非空，不打印 token 值。

## 支持的 Preset

13 个 preset，详见 `references/presets.md`：

| 协议 | 数量 | Provider |
|------|------|----------|
| OpenAI Images | 10 | laozhang, openai, apiyi, right_codes, copperai |
| Gemini | 3 | laozhang, apiyi, google |

## 尺寸

3 档（1K / 2K / 4K）× 10 种宽高比。详见 `references/size-mapping.md`。

## 与 MCP 的对应关系

| 旧 MCP 调用 | 新技能替代 |
|------------|-----------|
| `mcp__image_generate_mcp_remote__gpt_image_2_official` | `img_gen.py generate --preset laozhang_gpt_image_2_default` |
| `mcp__image_generate_mcp_remote__nano_banana_2_official` | `img_gen.py generate --preset laozhang_nano_banana_pro` |
| `...list_image_tools_catalog_tool` | `img_gen.py check` |
| `...list_image_presets_tool` | `img_gen.py check` |

## 依赖

- Python 3.9+（仅标准库，无 pip 依赖）
- OS 环境变量 `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY` 和/或 `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY` 已设置
