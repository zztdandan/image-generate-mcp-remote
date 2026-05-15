"""gpt_image_2_vip 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.image_size import ImageAspectRatio, ImageSizeTier
from ...contracts.presets import PresetDispatchPolicy, PresetFieldDispatchMode, PresetProvider, PresetRuntimeConfig, UnsupportedSizePreset
from ...presets.models import GptImage2ExecutionRequest, GptImage2PreparedRequest


class LaoZhangGptImage2VipPreset(BaseGptImage2Preset):
    """LaoZhangGptImage2VipPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "laozhang_gpt_image_2_vip"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai/v1"
    model = "gpt-image-2-vip"
    dispatch = PresetDispatchPolicy(
        size=PresetFieldDispatchMode.SEND,
        quality=PresetFieldDispatchMode.DROP,
        output_format=PresetFieldDispatchMode.SEND,
        background=PresetFieldDispatchMode.SEND,
        moderation=PresetFieldDispatchMode.SEND,
    )
    runtime = PresetRuntimeConfig(timeout_seconds=240.0, retry_count=1)
    unsupported_sizes: tuple[UnsupportedSizePreset, ...] = tuple(
        UnsupportedSizePreset(image_size=ImageSizeTier.SIZE_4K, aspect_ratio=aspect_ratio)
        for aspect_ratio in ImageAspectRatio
    )
    notes = (
        "LaoZhang gpt-image-2-vip supports explicit size but not quality according to archived docs.",
        "4K requests are blocked because upstream testing shows this preset cannot generate 4K images.",
    )

    def prepare_gpt_image_2_request(self, request: GptImage2ExecutionRequest) -> GptImage2PreparedRequest:
        prepared = super().prepare_gpt_image_2_request(request)
        prepared.payload.pop("output_format", None)
        prepared.payload.pop("background", None)
        prepared.payload.pop("moderation", None)
        prepared.payload.pop("n", None)
        return prepared
