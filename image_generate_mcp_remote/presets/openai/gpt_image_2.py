"""Default OpenAI-compatible gpt-image-2 preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset


class OpenAIGptImage2Preset(BaseGptImage2Preset):
    """Default OpenAI-compatible gpt-image-2 preset."""

    preset_id = "openai_gpt_image_2"
    notes = ("Default OpenAI Images compatible preset.",)
