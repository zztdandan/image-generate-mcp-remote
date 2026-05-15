"""Right Codes draw Images API preset for gpt-image-2."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class RightCodesGptImage2Preset(BaseGptImage2Preset):
    """Right Codes draw Images API preset for gpt-image-2."""

    preset_id = "right_codes_gpt_image_2"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    notes = (
        "Right Codes Images API returns data[0].url in verified generation and edit flows.",
        "response_format=b64_json may still return URL, so parsing must accept both b64_json and url.",
    )
