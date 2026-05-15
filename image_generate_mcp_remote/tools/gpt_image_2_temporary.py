"""gpt_image_2_temporary 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import time

import httpx

from ..config import DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS
from ..contracts.enums import ImageBackground, ImageModeration, ImageOutputFormat, ImageQuality
from ..contracts.image_size import ImageAspectRatio, ImageSizeProvider, ImageSizeTier, provider_size_value
from ..models.common import ImageToolResult, ToolVersion
from .temporary_common import persist_temporary_output

GPT_IMAGE_2_TEMPORARY_NAME = "gpt_image_2_temporary"


def gpt_image_2_temporary_generate(
    version: ToolVersion,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    save_path: str,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    quality: ImageQuality = ImageQuality.AUTO,
    output_format: ImageOutputFormat = ImageOutputFormat.PNG,
    background: ImageBackground = ImageBackground.AUTO,
    moderation: ImageModeration = ImageModeration.AUTO,
    send_quality: bool = False,
    send_output_format: bool = False,
    send_background: bool = False,
    send_moderation: bool = False,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
) -> ImageToolResult:
    """执行 gpt_image_2_temporary_generate，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片生成调用并产出结果
        - 步骤 2：准备请求后调用上游并归一化返回
    """

    if version is not ToolVersion.V1:
        raise ValueError("only version v1 is supported")
    endpoint = f"{base_url.rstrip('/')}/images/generations"
    payload: dict[str, str] = {
        "model": model,
        "prompt": prompt,
        "size": provider_size_value(image_size, aspect_ratio, provider=ImageSizeProvider.GPT),
    }
    if send_quality:
        payload["quality"] = quality.value
    if send_output_format:
        payload["output_format"] = output_format.value
    if send_background:
        payload["background"] = background.value
    if send_moderation:
        payload["moderation"] = moderation.value

    started_at = time.perf_counter()
    response = httpx.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    response_json = response.json()
    if not isinstance(response_json, dict):
        raise ValueError("temporary provider response is not a JSON object")
    return persist_temporary_output(
        GPT_IMAGE_2_TEMPORARY_NAME,
        response_json,
        save_path,
        timeout_seconds,
        time.perf_counter() - started_at,
        model,
    )
