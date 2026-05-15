"""API易 gpt-image-2 Images API preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class ApiYiGptImage2Preset(BaseGptImage2Preset):
    """API易 gpt-image-2 Images API preset."""

    preset_id = "apiyi_gpt_image_2"
    provider = PresetProvider.APIYI
    base_url = "https://api.apiyi.com/v1"
    notes = ("API易 Images API channel for gpt-image-2.",)
