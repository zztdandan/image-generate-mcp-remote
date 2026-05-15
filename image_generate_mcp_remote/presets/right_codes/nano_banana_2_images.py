"""Right Codes nano-banana-2 Images API preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class RightCodesNanoBanana2ImagesPreset(BaseGptImage2Preset):
    """OpenAI Images protocol preset for Right Codes nano-banana-2."""

    preset_id = "right_codes_nano_banana_2_images"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    model = "nano-banana-2"
    notes = ("Uses OpenAI Images style endpoint despite the nano-banana-2 model name.",)
