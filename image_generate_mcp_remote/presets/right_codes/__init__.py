"""__init__ 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from .gpt_image_2 import RightCodesGptImage2Preset
from .gpt_image_2_vip import RightCodesGptImage2VipPreset
from .nano_banana_2_images import RightCodesNanoBanana2ImagesPreset

__all__ = [
    "RightCodesGptImage2Preset",
    "RightCodesGptImage2VipPreset",
    "RightCodesNanoBanana2ImagesPreset",
]
