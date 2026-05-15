"""loader 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from functools import lru_cache

from ..contracts.presets import PresetToolName
from .base import BaseImageToolPreset
from .registry import PRESET_REGISTRY, PresetClass

DEFAULT_PRESET_BY_TOOL: dict[PresetToolName, str] = {
    PresetToolName.GPT_IMAGE_2_OFFICIAL: "openai_gpt_image_2",
    PresetToolName.NANO_BANANA_2_OFFICIAL: "google_nano_banana",
}


def preset_class_for_id(preset_id: str) -> PresetClass:
    """执行 preset_class_for_id，用于 preset 契约定义 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    preset_class = PRESET_REGISTRY.get(preset_id)
    if preset_class is None:
        available = ", ".join(sorted(PRESET_REGISTRY))
        raise ValueError(f"Unknown image preset '{preset_id}'. Available presets: {available}")
    return preset_class


@lru_cache(maxsize=8)
def resolve_preset_for_tool(tool_name: PresetToolName, preset_id: str | None) -> BaseImageToolPreset:
    """执行 resolve_preset_for_tool，用于 preset 契约定义 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析并确定最终生效配置
        - 步骤 2：合并输入来源后输出可执行结果
    """

    effective_preset_id = preset_id or DEFAULT_PRESET_BY_TOOL[tool_name]
    preset_class = preset_class_for_id(effective_preset_id)
    preset = preset_class()
    resolved = preset.resolve()
    if resolved.config.tool_name is not tool_name:
        raise ValueError(
            f"Preset '{effective_preset_id}' is bound to {resolved.config.tool_name.value}, not {tool_name.value}"
        )
    return preset


def clear_preset_cache() -> None:
    """执行 clear_preset_cache，用于 preset 契约定义 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    resolve_preset_for_tool.cache_clear()
