"""nano_banana_2_official 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from typing import Literal

from ..contracts.enums import ImageResponseModality, ImageThinkingLevel
from ..config import get_settings
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..contracts.presets import PresetToolName
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ToolVersion
from ..presets.base import BaseNanoBananaPreset
from ..presets.models import NanoBananaEditExecutionRequest, NanoBananaGenerateExecutionRequest
from .official_common import resolve_official_preset_execution

ResponseModality = ImageResponseModality
NanoBananaAspectRatio = ImageAspectRatio
NanoBananaImageSize = ImageSizeTier
NanoBananaThinkingLevel = ImageThinkingLevel

def _validate_response_modalities(response_modalities: list[ResponseModality]) -> None:
    if ResponseModality.IMAGE not in response_modalities:
        raise ValueError("response_modalities must include IMAGE")


def _active_nano_banana_preset(
    mode: ImageToolMode,
    preset: str | None,
    api_key: str | None,
) -> tuple[BaseNanoBananaPreset, str]:
    """执行 _active_nano_banana_preset，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    settings = get_settings()
    resolved_execution = resolve_official_preset_execution(
        tool_name=PresetToolName.NANO_BANANA_2_OFFICIAL,
        mode=mode,
        configured_preset=settings.nano_banana_2_official_preset,
        configured_api_key=settings.nano_banana_2_official_api_key,
        request_preset=preset,
        request_api_key=api_key,
    )
    if not isinstance(resolved_execution.preset, BaseNanoBananaPreset):
        raise TypeError("active nano_banana_2_official preset must inherit BaseNanoBananaPreset")
    return resolved_execution.preset, resolved_execution.api_key


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
    preset: str | None = None,
    api_key: str | None = None,
) -> ImageToolResult:
    """执行 nano_banana_2_official_generate，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片生成调用并产出结果
        - 步骤 2：准备请求后调用上游并归一化返回
    """

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
    active_preset, effective_api_key = _active_nano_banana_preset(mode=mode, preset=preset, api_key=api_key)
    return active_preset.execute_nano_banana(execution_request, effective_api_key)


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
    preset: str | None = None,
    api_key: str | None = None,
) -> ImageToolResult:
    """执行 nano_banana_2_official_edit，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片编辑调用并产出结果
        - 步骤 2：准备编辑载荷后调用上游并归一化返回
    """

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
    active_preset, effective_api_key = _active_nano_banana_preset(mode=mode, preset=preset, api_key=api_key)
    return active_preset.execute_nano_banana(execution_request, effective_api_key)
