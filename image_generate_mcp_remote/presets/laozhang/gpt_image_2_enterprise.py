"""LaoZhang GPTImage2 Enterprise gpt-image-2 preset."""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class LaoZhangGptImage2EnterprisePreset(BaseGptImage2Preset):
    """Enterprise token group with pure official-key routing."""

    preset_id = "laozhang_gpt_image_2_enterprise"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai/v1"
    notes = ("LaoZhang GPTImage2 Enterprise group is a pure official-key route with official parameter support.",)
