"""gpt_image_2 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class ApiYiGptImage2Preset(BaseGptImage2Preset):
    """ApiYiGptImage2Preset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "apiyi_gpt_image_2"
    provider = PresetProvider.APIYI
    base_url = "https://api.apiyi.com/v1"
    notes = ("API易 Images API channel for gpt-image-2.",)
