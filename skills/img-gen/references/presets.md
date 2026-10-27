# 预设清单（Preset Catalog）

共 23 个预设，覆盖 6 家 provider、2 种协议。每个预设带 `tier`（使用优先级）
与 `billing`（计费方式）两个元数据，CLI 的 `check` 会直接打印。

## 怎么选（一句话）

- 日常：`--preset auto`，只走 `preferred`（$0.03/张按次）。
- 要指定：`laozhang_gpt_image_2_5_sunburst_vip`（画质）或 `..._flare_vip`（速度）。
- `last_resort` 一律不用，除非所有 $0.03 路线都失败。

## GPT-Image 2.5 VIP（$0.03/张，按次；**默认**）

| Preset ID | Provider | Model | Base URL | tier | 特点 |
|-----------|----------|-------|----------|------|------|
| `apiyi_gpt_image_2_5_vip` | apiyi | gpt-image-2.5-vip（= sunburst-vip） | https://api.apiyi.com/v1 | preferred | 画质/编辑精度优先，auto 首选 |
| `apiyi_gpt_image_2_5_flare_vip` | apiyi | gpt-image-2.5-flare-vip | https://api.apiyi.com/v1 | preferred | 速度优先，画面偏软 |
| `apiyi_gpt_image_2_5_sunburst_vip` | apiyi | gpt-image-2.5-sunburst-vip | https://api.apiyi.com/v1 | preferred | 上一条的全名写法 |
| `apiyi_gpt_image_2_vip` | apiyi | gpt-image-2-vip | https://api.apiyi.com/v1 | preferred | 上一代，quality 只到 high |
| `laozhang_gpt_image_2_5_flare_vip` | laozhang | gpt-image-2.5-flare-vip | https://api.laozhang.ai/v1 | preferred | apiyi 不可用时的同价备份 |
| `laozhang_gpt_image_2_5_sunburst_vip` | laozhang | gpt-image-2.5-sunburst-vip | https://api.laozhang.ai/v1 | preferred | apiyi 同价备份（当前未激活） |
| `laozhang_gpt_image_2_vip` | laozhang | gpt-image-2-vip | https://api.laozhang.ai/v1 | standard | 上一代 VIP |

**共同契约**（apiyi 文档 2026-10）：

- `size` 只认 30 档（10 比例 × 1K/2K/4K），表外尺寸会被 16 倍数重对齐或抬到最小边；
  本技能 `SIZE_MAP` 的 gpt 值与该表逐项一致，CLI 对 table30 预设做前置校验。
- `quality`：2.5 两款六档全开（`auto/low/medium/high/xhigh/max`）；`gpt-image-2-vip`
  到 `high`，传 `xhigh/max` 会被拒。2.5 的 `high` ≈ 2-vip 的 `medium`，2.5 的 `max` ≈ 2-vip 的 `high`。
- `n` 永远 1：传 `n=3` 按 3 张扣费但仍只回 1 张。
- `response_format` 总是显式传；默认 `b64_json`（无 `data:` 前缀，但要兼容带前缀），
  `url` 是约 24 h 失效的 CDN 直链，CLI 会立即下载落盘。
- `background: transparent` + `output_format: png` 返回真 alpha PNG（不承诺，实测可用）。
  其它 `output_format`（jpeg 等）会被静默忽略，仍回 PNG。
- `mask` 接受但整图重绘，不做精确局部重绘。
- 出图 90–150 s 量级，客户端超时按 360 s 配；4K 偶发 500，优先降到 2K 重试。
- RPM 500 以内不需要并发限制；429 先看 `error.message`：参数被拒改参数，
  「当前分组上游负载已饱和」退避重试。
- 失败请求（400/5xx）不计费；200 但模型用文字软拒绝会照常计费。

### 线路现状（2026-10-26 实测）

`apiyi_gpt_image_2_5_vip` 实测可用：1280×720 low 生成 29.9 s、2048×1152 low 编辑
29.8 s、1280×1280 + `response_format=url` 39.6 s，尺寸逐像素命中。当天早些时候同一 key
曾返回 `403 {"code":"insufficient_quota"}`，随后恢复，属于账号配额波动。

laozhang 网关 02:11 可用（27 s），02:20 起对本机 TLS 直接 reset
（`SSL: UNEXPECTED_EOF_WHILE_READING`，openssl 握手同样失败）——laozhang 侧可用性问题，
与技能代码无关。auto 链仍保留 laozhang `-vip` 作为同价备份，恢复后自动生效。

## GPT-Image 2.5 官转（按 token 计费，**贵，最后手段**）

| Preset ID | Provider | Model | tier |
|-----------|----------|-------|------|
| `apiyi_gpt_image_2_5_flare` | apiyi | gpt-image-2.5-flare | last_resort |
| `apiyi_gpt_image_2_5_sunburst` | apiyi | gpt-image-2.5-sunburst | last_resort |
| `laozhang_gpt_image_2_5_flare` | laozhang | gpt-image-2.5-flare | last_resort |
| `laozhang_gpt_image_2_5_sunburst` | laozhang | gpt-image-2.5-sunburst | last_resort |
| `laozhang_gpt_image_2_default` / `_enterprise` / `_sora_official` | laozhang | gpt-image-2 | last_resort |
| `apiyi_gpt_image_2` | apiyi | gpt-image-2 | last_resort |
| `openai_gpt_image_2` | openai | gpt-image-2（官方直连） | last_resort |

这些是按 token 计费的官转/官方线路，同尺寸同 quality 下成本远高于 `-vip` 的
$0.03/张。**默认不要用**：auto 加 `--allow-expensive` 才会把它们排到便宜路线之后，
显式写 preset 名时 CLI 会打印 `[!] LAST-RESORT ROUTE` 警告。

## 其它 GPT 线路（standard）

| Preset ID | Provider | Model | 备注 |
|-----------|----------|-------|------|
| `right_codes_gpt_image_2` | right_codes | gpt-image-2 | 实验渠道 |
| `right_codes_gpt_image_2_vip` | right_codes | gpt-image-2-vip | $0.03/张，experimental |
| `right_codes_nano_with_image_api_images` | right_codes | nano-banana-2 | 用 OpenAI Images 协议调 nano |
| `copperai_gpt_image_2` | copperai | gpt-image-2 | experimental |

## Nano Banana 2（Gemini generateContent 协议）

| Preset ID | Provider | Model | Base URL | tier |
|-----------|----------|-------|----------|------|
| `laozhang_nano_banana_pro` | laozhang | gemini-3-pro-image-preview | https://api.laozhang.ai | standard |
| `apiyi_nano_banana_2` | apiyi | gemini-3.1-flash-image-preview | https://api.apiyi.com | standard |
| `google_nano_banana` | google | gemini-3.1-flash-image-preview | https://generativelanguage.googleapis.com | standard |

### 注意事项

- `laozhang_nano_banana_pro`：支持 1K/2K/4K 全档位。
- 认证仅需 `Authorization: Bearer` header，不需要 `x-goog-api-key`。
- 响应中图片以 base64 inlineData 形式返回。
- banana preset 不参与 GPT 的 auto 链（协议不同）。

## auto 链

`--preset auto`（默认）按顺序尝试，命中即停：

```
apiyi_gpt_image_2_5_vip            $0.03
apiyi_gpt_image_2_5_flare_vip      $0.03
laozhang_gpt_image_2_5_sunburst_vip $0.03
laozhang_gpt_image_2_5_flare_vip   $0.03
```

只有 401/403/404/408/409/425/429/5xx 与网络超时才会跳到下一条；HTTP 400 立即停止
（参数错误换路线也没用）。全部失败时提示加 `--allow-expensive`，此时才追加
`LAST_RESORT_CHAIN`（按 token 计费的官转线路）。

## 已注册但未独立脚本的临时工具

以下工具为 MCP 中用于探索的临时工具，不绑定固定 preset，本技能不为其生成独立封装：

- `gpt_image_2_temporary`
- `nano_banana_2_temporary`

如需临时工具模式，直接调用 `lib/openai_images.py` 或 `lib/gemini_gen.py` 并传入
自定义 base_url、model、api_key。
