"""Resolve active preset classes from startup environment settings."""

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
    """Return a registered preset class or fail with an explicit preset id."""

    preset_class = PRESET_REGISTRY.get(preset_id)
    if preset_class is None:
        available = ", ".join(sorted(PRESET_REGISTRY))
        raise ValueError(f"Unknown image preset '{preset_id}'. Available presets: {available}")
    return preset_class


@lru_cache(maxsize=8)
def resolve_preset_for_tool(tool_name: PresetToolName, preset_id: str | None) -> BaseImageToolPreset:
    """Instantiate the active preset for one formal tool."""

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
    """Clear the preset cache for tests that change environment variables."""

    resolve_preset_for_tool.cache_clear()
