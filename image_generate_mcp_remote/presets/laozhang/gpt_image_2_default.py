"""LaoZhang default group reverse-route gpt-image-2 preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetDispatchPolicy, PresetFieldDispatchMode, PresetProvider


class LaoZhangGptImage2DefaultPreset(BaseGptImage2Preset):
    """Default token group: reverse ChatGPT line without size or quality support."""

    preset_id = "laozhang_gpt_image_2_default"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai/v1"
    dispatch = PresetDispatchPolicy(
        size=PresetFieldDispatchMode.DROP,
        quality=PresetFieldDispatchMode.DROP,
        output_format=PresetFieldDispatchMode.SEND,
        background=PresetFieldDispatchMode.SEND,
        moderation=PresetFieldDispatchMode.SEND,
    )
    notes = (
        "LaoZhang default token group is a reverse ChatGPT route.",
        "Provider docs say size and quality are unsupported for this group, so the preset drops them.",
    )
