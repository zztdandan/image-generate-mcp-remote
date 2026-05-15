"""Experimental CopperAI gpt-image-2 preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetDispatchPolicy, PresetFieldDispatchMode, PresetProvider, PresetStability


class CopperAIGptImage2Preset(BaseGptImage2Preset):
    """CopperAI preset with conservative dispatch until model-level docs are verified."""

    preset_id = "copperai_gpt_image_2"
    provider = PresetProvider.COPPERAI
    base_url = "https://api.copperai.dev/v1"
    stability = PresetStability.EXPERIMENTAL
    dispatch = PresetDispatchPolicy(
        size=PresetFieldDispatchMode.PROMPT_FALLBACK,
        quality=PresetFieldDispatchMode.DROP,
        output_format=PresetFieldDispatchMode.DROP,
        background=PresetFieldDispatchMode.DROP,
        moderation=PresetFieldDispatchMode.DROP,
    )
    notes = ("Provider guide has platform-level details only; model parameter support is not fully verified.",)
