"""nano_banana_2_images 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider, PresetRuntimeConfig


class RightCodesNanoBanana2ImagesPreset(BaseGptImage2Preset):
    """RightCodesNanoBanana2ImagesPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "right_codes_nano_with_image_api_images"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    model = "nano-banana-2"
    runtime = PresetRuntimeConfig(timeout_seconds=180.0, retry_count=1)
    notes = ("Uses OpenAI Images style endpoint despite the nano-banana-2 model name.",)
