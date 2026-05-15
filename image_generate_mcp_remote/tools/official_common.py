"""official_common 模块用于正式 preset 工具的按次覆盖解析，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.presets import PresetToolName
from ..errors import ValidationError
from ..models.common import ImageToolMode
from ..presets.base import BaseImageToolPreset
from ..presets.loader import resolve_preset_for_tool


@dataclass(frozen=True)
class ResolvedPresetExecution:
    """ResolvedPresetExecution 是正式工具按次 preset 解析结果。"""

    preset: BaseImageToolPreset
    api_key: str


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def resolve_official_preset_execution(
    tool_name: PresetToolName,
    mode: ImageToolMode,
    configured_preset: str | None,
    configured_api_key: str,
    request_preset: str | None,
    request_api_key: str | None,
) -> ResolvedPresetExecution:
    """执行 resolve_official_preset_execution，用于正式 preset 工具按次覆盖解析 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：合并按次请求覆盖与环境默认值
        - 步骤 2：在需要 preset override 时强制校验 api_key 同传
    """

    normalized_preset = _normalize_optional_text(request_preset)
    normalized_api_key = _normalize_optional_text(request_api_key)
    if normalized_preset is not None and normalized_api_key is None:
        raise ValidationError(tool_name.value, mode.value, "preset override requires api_key in the same request")
    effective_preset_id = normalized_preset or configured_preset
    effective_api_key = normalized_api_key or configured_api_key
    return ResolvedPresetExecution(
        preset=resolve_preset_for_tool(tool_name, effective_preset_id),
        api_key=effective_api_key,
    )
