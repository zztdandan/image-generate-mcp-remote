"""registry 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from .base import BaseImageToolPreset
from .apiyi import ApiYiGptImage2Preset
from .copperai import CopperAIGptImage2Preset
from .google import GoogleNanoBananaPreset
from .laozhang import (
    LaoZhangGptImage2DefaultPreset,
    LaoZhangGptImage2EnterprisePreset,
    LaoZhangGptImage2SoraOfficialPreset,
    LaoZhangGptImage2VipPreset,
)
from .openai import OpenAIGptImage2Preset
from .right_codes import RightCodesGptImage2Preset, RightCodesGptImage2VipPreset, RightCodesNanoBanana2ImagesPreset

PresetClass = type[BaseImageToolPreset]

PRESET_REGISTRY: dict[str, PresetClass] = {
    OpenAIGptImage2Preset.preset_id: OpenAIGptImage2Preset,
    ApiYiGptImage2Preset.preset_id: ApiYiGptImage2Preset,
    LaoZhangGptImage2DefaultPreset.preset_id: LaoZhangGptImage2DefaultPreset,
    LaoZhangGptImage2SoraOfficialPreset.preset_id: LaoZhangGptImage2SoraOfficialPreset,
    LaoZhangGptImage2EnterprisePreset.preset_id: LaoZhangGptImage2EnterprisePreset,
    LaoZhangGptImage2VipPreset.preset_id: LaoZhangGptImage2VipPreset,
    RightCodesGptImage2Preset.preset_id: RightCodesGptImage2Preset,
    RightCodesGptImage2VipPreset.preset_id: RightCodesGptImage2VipPreset,
    RightCodesNanoBanana2ImagesPreset.preset_id: RightCodesNanoBanana2ImagesPreset,
    CopperAIGptImage2Preset.preset_id: CopperAIGptImage2Preset,
    GoogleNanoBananaPreset.preset_id: GoogleNanoBananaPreset,
}
