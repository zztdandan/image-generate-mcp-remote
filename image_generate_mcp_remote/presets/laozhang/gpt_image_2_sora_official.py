"""LaoZhang Sora2Official gpt-image-2 preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class LaoZhangGptImage2SoraOfficialPreset(BaseGptImage2Preset):
    """Sora2Official token group with official-compatible size and quality support."""

    preset_id = "laozhang_gpt_image_2_sora_official"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai/v1"
    notes = ("LaoZhang Sora2Official token group supports official Images API size and quality fields.",)
