"""gpt_image_2_vip 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider, PresetRuntimeConfig, PresetStability


class RightCodesGptImage2VipPreset(BaseGptImage2Preset):
    """RightCodesGptImage2VipPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "right_codes_gpt_image_2_vip"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    model = "gpt-image-2-vip"
    stability = PresetStability.EXPERIMENTAL
    notes = ("Model is visible but archived docs did not obtain a successful sample; do not use as default.",)
    runtime = PresetRuntimeConfig(timeout_seconds=250.0, retry_count=1)
