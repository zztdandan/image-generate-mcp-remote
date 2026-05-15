"""gpt_image_2 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class RightCodesGptImage2Preset(BaseGptImage2Preset):
    """RightCodesGptImage2Preset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "right_codes_gpt_image_2"
    provider = PresetProvider.RIGHT_CODES
    base_url = "https://www.right.codes/draw/v1"
    notes = (
        "Right Codes Images API returns data[0].url in verified generation and edit flows.",
        "response_format=b64_json may still return URL, so parsing must accept both b64_json and url.",
    )
