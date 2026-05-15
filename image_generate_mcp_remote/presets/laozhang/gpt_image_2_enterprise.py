"""gpt_image_2_enterprise 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from ..base import BaseGptImage2Preset
from ...contracts.presets import PresetProvider


class LaoZhangGptImage2EnterprisePreset(BaseGptImage2Preset):
    """LaoZhangGptImage2EnterprisePreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "laozhang_gpt_image_2_enterprise"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai/v1"
    notes = ("LaoZhang GPTImage2 Enterprise group is a pure official-key route with official parameter support.",)
