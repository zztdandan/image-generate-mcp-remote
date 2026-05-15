"""gpt_image_2_official 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

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
    """执行 _active_gpt_image_2_preset，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

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
    """执行 gpt_image_2_official_generate，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片生成调用并产出结果
        - 步骤 2：准备请求后调用上游并归一化返回
    """

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
    """执行 gpt_image_2_official_edit，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片编辑调用并产出结果
        - 步骤 2：准备编辑载荷后调用上游并归一化返回
    """

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
