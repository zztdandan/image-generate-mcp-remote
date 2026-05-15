"""Thin MCP-boundary wrapper for the active Nano Banana preset."""

from __future__ import annotations

from typing import Literal

from ..contracts.enums import ImageResponseModality, ImageThinkingLevel
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..contracts.presets import PresetToolName
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ToolVersion
from ..presets.base import BaseNanoBananaPreset
from ..presets.loader import resolve_preset_for_tool
from ..presets.models import NanoBananaEditExecutionRequest, NanoBananaGenerateExecutionRequest
from ..config import get_settings

ResponseModality = ImageResponseModality
NanoBananaAspectRatio = ImageAspectRatio
NanoBananaImageSize = ImageSizeTier
NanoBananaThinkingLevel = ImageThinkingLevel

def _validate_response_modalities(response_modalities: list[ResponseModality]) -> None:
    if ResponseModality.IMAGE not in response_modalities:
        raise ValueError("response_modalities must include IMAGE")


def _active_nano_banana_preset() -> BaseNanoBananaPreset:
    """Resolve the startup-selected Nano Banana preset for this process."""

    settings = get_settings()
    preset = resolve_preset_for_tool(PresetToolName.NANO_BANANA_2_OFFICIAL, settings.nano_banana_2_official_preset)
    if not isinstance(preset, BaseNanoBananaPreset):
        raise TypeError("active nano_banana_2_official preset must inherit BaseNanoBananaPreset")
    return preset


def nano_banana_2_official_generate(
    version: ToolVersion,
    mode: Literal[ImageToolMode.GENERATE],
    prompt: str,
    save_path: str,
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
) -> ImageToolResult:
    """Run generate mode through the active preset runtime."""

    execution_request = NanoBananaGenerateExecutionRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        response_modalities=response_modalities or [ResponseModality.IMAGE],
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    )
    _validate_response_modalities(execution_request.response_modalities)
    return _active_nano_banana_preset().execute_nano_banana(execution_request, get_settings().nano_banana_2_official_api_key)


def nano_banana_2_official_edit(
    version: ToolVersion,
    mode: Literal[ImageToolMode.EDIT],
    prompt: str,
    save_path: str,
    input_images: list[InputImage],
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
) -> ImageToolResult:
    """Run edit mode through the active preset runtime."""

    execution_request = NanoBananaEditExecutionRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        input_images=input_images,
        response_modalities=response_modalities or [ResponseModality.IMAGE],
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    )
    _validate_response_modalities(execution_request.response_modalities)
    if not execution_request.input_images:
        raise ValueError("input_images must contain at least one item")
    return _active_nano_banana_preset().execute_nano_banana(execution_request, get_settings().nano_banana_2_official_api_key)
