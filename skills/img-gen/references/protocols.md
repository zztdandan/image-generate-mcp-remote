# API 协议参考

两条链路都是同步 HTTP：没有任务 ID，客户端断开结果就丢，但请求照常计费。
因此本技能默认 `timeout=360 s`，不要按普通 JSON 接口的 30–60 s 配。

## 1. OpenAI Images 协议（GPT-Image 2 / 2.5）

### 生成（Generate）

```
POST {base_url}/images/generations
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "model": "gpt-image-2.5-vip",
  "prompt": "A futuristic city skyline",
  "size": "2048x1152",
  "quality": "low",
  "n": 1,
  "response_format": "b64_json"
}
```

必带 `model`：缺省时转发网关会回退到 `dall-e-2` 并报
`no available channels for model dall-e-2`，随后还会因 dall-e-2 不支持大尺寸
连锁抛 `size not supported`——症状像 size 问题，根因是 model 缺失。

可选字段（仅在显式提供时发送）：

| 字段 | 取值 | 说明 |
|------|------|------|
| `quality` | `auto` / `low` / `medium` / `high` / `xhigh` / `max` | 2.5 六档；`gpt-image-2(-vip)` 只到 `high`，传 xhigh/max 会被拒 |
| `background` | `transparent` / `opaque` / `auto` | `transparent` + png 返回真 alpha |
| `output_format` | `png` / `webp` / `jpeg` | 非 png 可能被上游静默忽略 |
| `response_format` | `b64_json` / `url` | **总是显式传**；默认值历史上变过 |

`n` 固定 1：`-vip` 传 `n=3` 按 3 张扣费但仍只返回 1 张。

响应（`b64_json`）：

```json
{"data": [{"b64_json": "<base64, 无 data: 前缀（历史版本可能带）>"}]}
```

响应（`url`）：

```json
{"data": [{"url": "https://.../image.png"}]}
```

`url` 是约 24 h 失效的 CDN 直链，技能会立即下载落盘。同一条 `data[]` 里
只会有 `url` 与 `b64_json` 其中之一，两条路径都兜住。

### 编辑（Edit）

```
POST {base_url}/images/edits
Authorization: Bearer {api_key}
Content-Type: multipart/form-data; boundary=...

Parts:
  image           — 原始图片（单张；>1.5MB 建议先压）
  mask            — 可选；-vip 接受但基本整图重绘
  prompt          — 编辑指令文本
  model           — 必传（同 generate）
  size            — 可选；table30 preset 必须传 30 档像素才拿到 2K
  quality         — 可选
  background      — 可选
  output_format   — 可选
  n               — 固定 1
  response_format — "b64_json" 或 "url"
```

apiyi 的行为：编辑省略 `size` 时**不**沿用输入图尺寸，而是回落到约 1120px 长边的
缩略图（例：1632×2048 → 1120×1405）。要 2K 成品必须显式传 `2048x1152` /
`1632x2048` 等 30 档像素。

### 尺寸映射（GPT）

本技能 `SIZE_MAP` 的 gpt 值与 apiyi 文档的 30 档表逐项一致（3 tier × 10 比例）：

| Tier | Ratio | 尺寸 |
|------|-------|------|
| 1K | 16:9 | 1280×720 |
| 1K | 1:1 | 1280×1280 |
| 2K | 16:9 | 2048×1152 |
| 2K | 1:1 | 2048×2048 |
| 4K | 16:9 | 3840×2160 |
| 4K | 1:1 | 2880×2880 |

完整 30 档见 `size-mapping.md`。table30 preset 传表外尺寸会被上游按 16 倍数重对齐/
抬到最小边，CLI 会直接拒绝而不是发出去。4K 偶发上游 500，优先降到 2K 重试。

---

## 2. Gemini generateContent 协议（Nano Banana 2）

### 生成（Generate）

```
POST {base_url}/v1beta/models/{model}:generateContent
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "contents": [{"parts": [{"text": "Generate an image of ..."}]}],
  "generationConfig": {"responseModalities": ["IMAGE"]}
}
```

### 编辑（Edit — image-to-image）

```
POST {base_url}/v1beta/models/{model}:generateContent
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "contents": [{
    "parts": [
      {"text": "Edit this image: add a red car"},
      {"inlineData": {"mimeType": "image/png", "data": "<base64>"}}
    ]
  }],
  "generationConfig": {"responseModalities": ["IMAGE"]}
}
```

### 响应（Generate & Edit 共用）

```json
{
  "candidates": [{
    "content": {
      "parts": [{
        "inlineData": {
          "mimeType": "image/png",
          "data": "<base64 encoded image>"
        }
      }]
    }
  }]
}
```

### 尺寸映射（Banana）

| Tier | Ratio | 尺寸 |
|------|-------|------|
| 1K | 16:9 | 1376×768 |
| 1K | 1:1 | 1024×1024 |
| 2K | 16:9 | 2752×1536 |
| 2K | 1:1 | 2048×2048 |
| 4K | 16:9 | 5504×3072 |

完整表见 `size-mapping.md`。
