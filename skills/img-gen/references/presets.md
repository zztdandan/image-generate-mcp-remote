# 预设清单（Preset Catalog）

共 13 个预设，覆盖 6 家 provider，2 种协议。

## GPT Image 2（OpenAI Images 协议）

| # | Preset ID | Provider | Model | Base URL | 稳定性 |
|---|-----------|----------|-------|----------|--------|
| 1 | `laozhang_gpt_image_2_vip` | laozhang | gpt-image-2-vip | https://api.laozhang.ai/v1 | stable |
| 2 | `laozhang_gpt_image_2_default` | laozhang | gpt-image-2 | https://api.laozhang.ai/v1 | stable |
| 3 | `laozhang_gpt_image_2_enterprise` | laozhang | gpt-image-2 | https://api.laozhang.ai/v1 | stable |
| 4 | `laozhang_gpt_image_2_sora_official` | laozhang | gpt-image-2 | https://api.laozhang.ai/v1 | stable |
| 5 | `openai_gpt_image_2` | openai | gpt-image-2 | https://api.openai.com/v1 | stable |
| 6 | `apiyi_gpt_image_2` | apiyi | gpt-image-2 | https://api.apiyi.com/v1 | stable |
| 7 | `right_codes_gpt_image_2` | right_codes | gpt-image-2 | https://www.right.codes/draw/v1 | stable |
| 8 | `right_codes_gpt_image_2_vip` | right_codes | gpt-image-2-vip | https://www.right.codes/draw/v1 | experimental |
| 9 | `right_codes_nano_with_image_api_images` | right_codes | nano-banana-2 | https://www.right.codes/draw/v1 | stable |
| 10 | `copperai_gpt_image_2` | copperai | gpt-image-2 | https://api.copperai.dev/v1 | experimental |

### 注意事项

- `laozhang_gpt_image_2_vip`：当前 MCP 活跃预设，支持 1K/2K，4K 已屏蔽。
- #1—#4 共享同一 base URL，区别在于 model 和 preset 策略。
- `right_codes_nano_with_image_api_images`：通过 OpenAI Images 协议调用 nano-banana-2 模型。
- 质量参数（quality）在 preset 中已 drop，不发送给上游。

## Nano Banana 2（Gemini generateContent 协议）

| # | Preset ID | Provider | Model | Base URL | 稳定性 |
|---|-----------|----------|-------|----------|--------|
| 11 | `laozhang_nano_banana_pro` | laozhang | gemini-3-pro-image-preview | https://api.laozhang.ai | stable |
| 12 | `apiyi_nano_banana_2` | apiyi | gemini-3.1-flash-image-preview | https://api.apiyi.com | stable |
| 13 | `google_nano_banana` | google | gemini-3.1-flash-image-preview | https://generativelanguage.googleapis.com | stable |

### 注意事项

- `laozhang_nano_banana_pro`：当前 MCP 活跃预设，支持 1K/2K/4K 全档位。
- 认证仅需 `Authorization: Bearer` header，不需要 `x-goog-api-key`。
- 支持 thinking_level（minimal / High）和 include_thoughts 参数。
- 响应中图片以 base64 inlineData 形式返回。

## 已注册但未独立脚本的临时工具

以下工具为 MCP 中用于探索的临时工具，不绑定固定 preset，本技能不为其生成独立封装：

- `gpt_image_2_temporary`
- `nano_banana_2_temporary`

如需使用临时工具模式，可直接调用 `lib/openai_images.py` 或 `lib/gemini_gen.py` 并传入自定义 base_url、model、api_key。
