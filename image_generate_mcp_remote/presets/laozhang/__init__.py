"""__init__ 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from .gpt_image_2_default import LaoZhangGptImage2DefaultPreset
from .gpt_image_2_enterprise import LaoZhangGptImage2EnterprisePreset
from .gpt_image_2_sora_official import LaoZhangGptImage2SoraOfficialPreset
from .gpt_image_2_vip import LaoZhangGptImage2VipPreset

__all__ = [
    "LaoZhangGptImage2DefaultPreset",
    "LaoZhangGptImage2EnterprisePreset",
    "LaoZhangGptImage2SoraOfficialPreset",
    "LaoZhangGptImage2VipPreset",
]
