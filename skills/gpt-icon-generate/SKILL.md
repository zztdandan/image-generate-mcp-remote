---
name: gpt-icon-generate
description: "当用户有任何图标生成、图标包、规则网格图标板、UI 图标、产品功能图标、应用图标、图标切图、透明 PNG、去白底、生成图片后拆分图标、MCP 图片生成等需求时使用。默认流程是用 `image-generate-mcp-remote_gpt_image_2_official` 生成 2K、1:1、4x4/16 个图标、纯白背景、每个图标带贴合轮廓描边/外发光/柔和阴影的图标板；如果用户指定行列、比例、尺寸或 URL 版工具，则按用户参数生成规则网格，并用校验脚本、参数规划脚本和 connected bbox 切图脚本输出透明 PNG。"
license: Proprietary. Internal project skill.
---

# GPT Icon Generation Skill

## 用途

- 生成图标、图标包、应用图标、UI 图标、产品功能图标。
- 生成规则网格图标板，并拆分成透明 PNG 单图。
- 默认走 `2K`、`1:1`、`4x4 / 16 icons`、白底、贴合图标轮廓描边/外发光/柔和阴影。
- 用户可以指定行数、列数、尺寸、比例、MCP 工具、`pad`、`border`、`fuzz`、`postprocess` 等参数。
- 不支持自由散排；如果生成结果不是规则网格，应重新生成，不要强行切图。

## MCP 与路径

- 本项目 MCP 配置文件：`.opencode/opencode.json`
- 默认图片 MCP 工具：`image-generate-mcp-remote_gpt_image_2_official`
- URL 版工具：`image-generate-mcp-remote_gpt-image-2-url`
- 生成前优先调用 `image-generate-mcp-remote_list_image_tools_catalog_tool` 检查当前工具支持的 size preset。
- 推荐输出路径：当前工作目录下的明确绝对路径，例如 `/home/base/repo/document/app-icons-sheet.png`

## 默认流程

如果用户没有特别指定，使用以下默认流程：

1. 使用 `image-generate-mcp-remote_gpt_image_2_official`。
2. 生成 `2048x2048`、`1:1`、纯白背景图标板。
3. 图标布局为 `4x4`，共 `16` 个图标；`expected_count = rows * cols`。
4. 提示词要求每个图标都有**贴合自身轮廓**的外描边、外发光或柔和阴影。
5. 不要要求远离图标的方形卡片框、圆角矩形底板、大面积 backplate 或 tile。
6. 生成后运行 `verify_image_output.py` 校验实际宽高、比例、通道。
7. 用实际宽高和行列运行 `plan_icon_sheet_params.py` 计算切图参数。
8. 用 `split_icon_sheet_connected_bbox.py` 做整图连通域切图。
9. 如需 UI 图标库，把每张图等比缩放后居中放入计算得到的透明画布，不固定写死 `512x512`。

## 可配置参数

- `rows`：图标板行数，默认 `4`
- `cols`：图标板列数，默认 `4`
- `size`：生成尺寸，默认 `2048x2048`
- `aspect_ratio`：图片比例，默认 `1:1`
- `tool`：图片生成工具，默认 `gpt_image_2_official`，用户可指定 `gpt-image-2-url`
- `fuzz`：背景 floodfill 容差，默认 `1.5%`
- `pad`：组件 bbox 外扩像素，默认由实际图片尺寸计算
- `border`：透明图标边缘留白，默认由实际图片尺寸计算
- `min_area`：主组件最小面积阈值，默认由实际图片尺寸计算
- `postprocess`：透明边缘后处理模式，默认 `baseline`，可选 `alpha_open_blur`

`expected_count` 不需要用户指定，始终等于 `rows * cols`。

## 工具选择规则

1. 默认使用 `image-generate-mcp-remote_gpt_image_2_official`。
2. 如果用户明确要求 URL 版、right.codes draw 兼容链路，或 official 工具不可用，再使用 `image-generate-mcp-remote_gpt-image-2-url`。
3. 如果目标尺寸不被当前工具支持，选择同宽高比下最接近的可用尺寸，并告知用户。
4. 如果请求 `2K` 但实际返回 `1K`，不直接失败；必须以实际输出尺寸重新计算切图参数。

## 生成建议

- 明确要求 `exactly {expected_count} icons in a {rows}x{cols} regular grid`。
- 明确要求 `canvas size {width}x{height}`。
- 明确要求 `pure white page background`。
- 明确要求 `ample padding between icons`。
- 明确要求 `each icon centered in its own cell`。
- **优先要求每个图标外面有贴合图标轮廓的细、柔和、可见但不过厚的阴影轮廓**，便于后续稳定切图。
- **不要生成远离图标的正方形卡片框、圆角矩形底板、大面积 backplate 或 tile**；外框应像贴纸描边一样沿图标外轮廓包裹。
- 若需要透明底，提示词里写 `transparent background with real alpha channel`，并在生成后验证。
- 若模型经常生成伪透明图，不要继续强依赖 alpha，改为生成纯白背景 + 每个图标外贴合轮廓的描边/外发光/柔和阴影。

## 正确边框要求

- 正确：贴合图标外轮廓的 thin outline / subtle glow / soft shadow，像 sticker cutline。
- 错误：远离图标的正方形卡片框、圆角矩形框、统一 tile、整格背景板。
- 目的：让连通域算法能把“图标 + 贴合轮廓阴影/描边”识别为一个主组件，同时外部白底仍与图像边缘连通，便于去底。

## 默认阴影提示词

- 默认使用第一优先方案：**细、柔和、贴边、不过厚**的轮廓阴影。
- 只有当默认阴影过弱、切图时与白底分离不够明显，才建议切到第二优先方案：**更清晰的浅灰轮廓 + 柔和阴影**。

推荐默认英文表述：

```text
Each icon must have a subtle, thin, contour-hugging soft shadow that is clearly visible but not thick, staying very close to the silhouette like a refined sticker edge.
```

推荐备选英文表述：

```text
Each icon must have a clearly visible, contour-hugging light-gray rim plus a soft shadow, with medium strength and continuous separation from the white background.
```

使用建议：

- 默认先用第一套提示词；这是当前测试里观感和可切性最平衡的方案。
- 如果用户反馈阴影不够明显、切图分离困难，再建议第二套提示词。
- 不默认使用更厚、更重的 cool-gray outline；那类方案只适合非常难分离的特殊图。

## 生成后校验

生成后必须先校验实际输出尺寸：

```bash
python3 .opencode/skills/gpt-icon-generate/scripts/verify_image_output.py \
  /absolute/path/to/sheet.png \
  --requested-width 2048 \
  --requested-height 2048
```

- 如果实际尺寸与请求尺寸一致：继续正常流程。
- 如果实际尺寸不同但比例一致：继续流程，但后续全部使用实际尺寸计算参数。
- 如果实际比例与请求比例不同：默认停止并重新生成，除非用户明确接受该比例。
- 没有 alpha 不视为失败，因为默认流程是白底后切透明。

## 参数规划

用实际图片尺寸和行列计算切图参数：

```bash
python3 .opencode/skills/gpt-icon-generate/scripts/plan_icon_sheet_params.py \
  --width 1280 \
  --height 1280 \
  --rows 4 \
  --cols 4
```

计算规则：

- `expected_count = rows * cols`
- `cell_width = width / cols`
- `cell_height = height / rows`
- `icon_canvas_size = floor(min(cell_width, cell_height))`
- `recommended_icon_extent = floor(icon_canvas_size * 0.8)`
- `pad`、`border`、`min_area` 基于实际图片尺寸相对 `2048` 的比例自动计算

## 切图（关键）

**优先使用通用参数化脚本：**

```bash
python3 .opencode/skills/gpt-icon-generate/scripts/split_icon_sheet_connected_bbox.py \
  /absolute/path/to/sheet.png \
  /absolute/path/to/output-dir \
  --rows 4 \
  --cols 4 \
  --pad 18 \
  --border 10 \
  --fuzz 1.5% \
  --postprocess baseline \
  --min-area 19531
```

本 skill 统一使用 `split_icon_sheet_connected_bbox.py`；不再保留单独的 4x4 专用切图脚本。

### 为什么必须使用 connected bbox 脚本

- 不能直接用机械网格 crop：图标稍微偏移就会切到边缘或混入隔壁内容。
- 不能先按单元裁切再去背景：如果图标偏移、外轮廓靠近格线，仍会切错。
- 不能把所有白色直接换成 alpha：会把图标内部白色、高光、白色面板、文字等“打穿”。
- 不能用 `convert ... -composite` 错误顺序抠 alpha：可能把彩图变成灰黑图。

### 正确算法

1. 对整张图做灰度、反相、阈值、形态学闭运算，得到前景 mask。
2. 对整张图做 connected components，找出面积最大的 `rows * cols` 个主图标组件。
3. 按组件真实 bbox 裁切原始彩图，而不是按固定网格裁切。
4. 对每个裁切图从四个角做 floodfill，只移除与边缘连续相连的背景。
5. 默认后处理是 `baseline`，不额外改动 alpha 边缘；如果用户觉得边缘毛刺明显，可切到 `alpha_open_blur` 做轻量开运算 + 轻微模糊。
6. 内部白色因为不与裁切图边缘背景连通，会被保留。
7. 输出彩色透明 `srgba` PNG。

## 后处理模式

- `baseline`：默认方案。保持最原始的 floodfill 透明边界，当前测试里对白色内纹样保护最好。
- `alpha_open_blur`：备选改进方案。适合用户觉得 `baseline` 边缘毛刺偏明显时使用，会轻微柔化并清掉小尖刺，但可能略微软化边缘。

推荐顺序：先用 `baseline`；只有当用户明确反馈边缘不够顺时，再切到 `alpha_open_blur`。

## 调参提示

- 如果 alpha 透明通道侵入了图标本体，尤其是切进内部白色、浅色高光或细节，优先怀疑 `fuzz` 偏大；应尝试改用更小的 `fuzz` 值重新切图。
- 如果 `fuzz` 降低后仍有侵入，通常说明图标外轮廓的隔离阴影/描边过浅、存在断口，或生成图本身不够适合当前 floodfill 分离策略；这时应考虑重新生成图标板并强化贴边轮廓。
- 如果图标主体保护已经较好，但透明边缘毛刺偏多、边缘不够顺，可保持当前 `fuzz`，改用 `postprocess=alpha_open_blur` 作为温和改进方案。
- 不建议同时大幅提高 `fuzz` 和启用更强后处理；前者解决的是“清背景范围”，后者解决的是“边缘观感”，两者职责不同。

## UI 图标库输出

如需统一透明画布，不要固定写死 `512x512`。使用 `plan_icon_sheet_params.py` 的输出：

- `icon_canvas_size`：最终透明画布尺寸
- `recommended_icon_extent`：图标主体建议缩放上限

示例：

```bash
mkdir -p /absolute/path/to/icons-ui
for f in /absolute/path/to/icons/icon-*.png; do
  base=$(basename "$f")
  convert "$f" -resize "256x256>" -background none -gravity center -extent 320x320 \
    "PNG32:/absolute/path/to/icons-ui/$base"
done
```

其中 `256` 与 `320` 应替换为 `recommended_icon_extent` 和 `icon_canvas_size`。

## 非 1:1 图片

支持非 `1:1` 图片，但必须仍然是规则网格：

1. 使用用户指定或 MCP 支持的实际尺寸。
2. 根据实际 `width / cols` 和 `height / rows` 计算单元格尺寸。
3. 以 `min(cell_width, cell_height)` 作为图标透明画布基准。
4. 切图仍使用 connected components，不使用机械网格 crop。
5. 如果生成结果不是规则网格，应重新生成，不要强行切图。

## 1K 与 2K

默认优先使用 `2K`，但 `1K` 是有效流程。

如果实际输出为 `1K`：

1. 不视为失败。
2. 使用 `verify_image_output.py` 获取实际尺寸。
3. 使用实际尺寸重新计算 `cell_width`、`cell_height`、`pad`、`border`、`min_area`。
4. 后续切图和透明画布尺寸均基于实际尺寸计算。

## 通用图标提示词模板

```text
Create a premium icon sheet with exactly {expected_count} distinct icons arranged in a clean {rows}x{cols} regular grid. Canvas size {width}x{height}. Pure white page background. Each icon must be visually centered inside its own cell with ample empty padding so no icon touches crop boundaries. Every icon must have a contour-hugging outer rim: a thin light outline, subtle glow, or soft shadow that closely follows the actual silhouette of the icon like a sticker border. Do NOT create square card tiles, rounded rectangle panels, large backplates, or frames far away from the icon. The outline/shadow must cling to the icon shape and leave the natural icon silhouette as the crop boundary. Unified design language, crisp edges, high detail, balanced spacing.
```

默认代入：`rows=4`、`cols=4`、`expected_count=16`、`width=2048`、`height=2048`。

## 输出约定

- 图标板：`<name>-sheet.png`
- 切图目录：`<name>-icons/`
- 单图文件：`icon-00.png` 到 `icon-NN.png`
- UI 图标库画布尺寸和缩放尺寸由 `plan_icon_sheet_params.py` 输出决定
