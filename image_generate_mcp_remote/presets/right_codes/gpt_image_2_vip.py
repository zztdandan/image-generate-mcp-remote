"""Experimental Right Codes gpt-image-2-vip preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider, PresetStability


class RightCodesGptImage2VipPreset(BaseGptImage2Preset):
    """Right Codes VIP model is registered but remains experimental."""

    preset_id = "right_codes_gpt_image_2_vip"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    model = "gpt-image-2-vip"
    stability = PresetStability.EXPERIMENTAL
    notes = ("Model is visible but archived docs did not obtain a successful sample; do not use as default.",)
