"""Thin MCP-boundary wrapper for the active GPT Image 2 preset."""

from __future__ import annotations

from typing import Literal

from ..config import get_settings
from ..contracts.enums import ImageBackground, ImageCount, ImageModeration, ImageOutputFormat, ImageQuality
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..contracts.presets import PresetToolName
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ToolVersion
from ..presets.base import BaseGptImage2Preset
from ..presets.loader import resolve_preset_for_tool
from ..presets.models import GptImage2EditExecutionRequest, GptImage2GenerateExecutionRequest

GptImageQuality = ImageQuality
GptImageOutputFormat = ImageOutputFormat
GptImageBackground = ImageBackground
GptImageModeration = ImageModeration
GptImageCount = ImageCount

def _active_gpt_image_2_preset() -> BaseGptImage2Preset:
    """Resolve the startup-selected GPT Image 2 preset for this process."""

    settings = get_settings()
    preset = resolve_preset_for_tool(PresetToolName.GPT_IMAGE_2_OFFICIAL, settings.gpt_image_2_official_preset)
    if not isinstance(preset, BaseGptImage2Preset):
        raise TypeError("active gpt_image_2_official preset must inherit BaseGptImage2Preset")
    return preset


def gpt_image_2_official_generate(
    version: ToolVersion,
    mode: Literal[ImageToolMode.GENERATE],
    prompt: str,
    save_path: str,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    quality: GptImageQuality = GptImageQuality.AUTO,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
    moderation: GptImageModeration = GptImageModeration.AUTO,
    n: GptImageCount = GptImageCount.SINGLE,
) -> ImageToolResult:
    """Run generate mode through the active preset runtime."""

    execution_request = GptImage2GenerateExecutionRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
        moderation=moderation,
        n=n,
    )
    return _active_gpt_image_2_preset().execute_gpt_image_2(execution_request, get_settings().gpt_image_2_official_api_key)


def gpt_image_2_official_edit(
    version: ToolVersion,
    mode: Literal[ImageToolMode.EDIT],
    prompt: str,
    save_path: str,
    images: list[InputImage],
    mask: InputImage | None = None,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    quality: GptImageQuality = GptImageQuality.AUTO,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
) -> ImageToolResult:
    """Run edit mode through the active preset runtime."""

    execution_request = GptImage2EditExecutionRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        images=images,
        mask=mask,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
    )
    return _active_gpt_image_2_preset().execute_gpt_image_2(execution_request, get_settings().gpt_image_2_official_api_key)
