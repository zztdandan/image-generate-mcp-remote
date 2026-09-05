# API 协议参考

## 1. OpenAI Images 协议（GPT Image 2）

### 生成（Generate）

```
POST {base_url}/images/generations
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "prompt": "A futuristic city skyline",
  "size": "2048x1152",
  "n": 1,
  "response_format": "b64_json"
}
```

响应：
```json
{
  "data": [
    {
      "b64_json": "<base64 encoded image data>"
    }
  ]
}
```

### 编辑（Edit）

```
POST {base_url}/images/edits
Authorization: Bearer {api_key}
Content-Type: multipart/form-data; boundary=...

Parts:
  image        — 原始图片（PNG，<4MB）
  mask         — 遮罩图片（可选，透明区域表示要编辑的部分）
  prompt       — 编辑指令文本
  size         — 输出尺寸（如 "2048x1152"）
  n            — 生成数量
  response_format — "b64_json"
```

### 尺寸映射（GPT）

| Tier | Ratio | 尺寸 |
|------|-------|------|
| 1K | 16:9 | 1280×720 |
| 1K | 1:1 | 1280×1280 |
| 2K | 16:9 | 2048×1152 |
| 2K | 1:1 | 2048×2048 |
| 4K | 16:9 | 3840×2160 |
| 4K | 1:1 | 2880×2880 |

注：`laozhang_gpt_image_2_vip` 屏蔽 4K 请求。

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
| 4K | 1:1 | 4096×4096 |

注：Banana 支持全部 1K/2K/4K 档位，无尺寸屏蔽。

### 可选参数

- `thinking_level`：`"minimal"`（默认）或 `"High"`
- `include_thoughts`：`true` 时响应中包含模型的思考过程文本
