"""LaoZhang gpt-image-2-vip preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetDispatchPolicy, PresetFieldDispatchMode, PresetProvider


class LaoZhangGptImage2VipPreset(BaseGptImage2Preset):
    """VIP model supports explicit size while dropping unsupported quality."""

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
    notes = ("LaoZhang gpt-image-2-vip supports explicit size but not quality according to archived docs.",)
