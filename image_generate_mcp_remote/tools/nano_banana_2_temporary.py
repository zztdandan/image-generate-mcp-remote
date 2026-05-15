"""nano_banana_2_temporary 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import time

import httpx

from ..config import DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS
from ..contracts.enums import ImageResponseModality
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..models.common import ImageToolResult, ToolVersion
from .temporary_common import persist_temporary_output

NANO_BANANA_2_TEMPORARY_NAME = "nano_banana_2_temporary"


def nano_banana_2_temporary_generate(
    version: ToolVersion,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    save_path: str,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    response_modalities: list[ImageResponseModality] | None = None,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
) -> ImageToolResult:
    """执行 nano_banana_2_temporary_generate，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行图片生成调用并产出结果
        - 步骤 2：准备请求后调用上游并归一化返回
    """

    if version is not ToolVersion.V1:
        raise ValueError("only version v1 is supported")
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    modalities = response_modalities or [ImageResponseModality.IMAGE]
    payload: dict[str, object] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": [item.value for item in modalities],
            "imageConfig": {"aspectRatio": aspect_ratio.value, "imageSize": image_size.value},
        },
    }

    started_at = time.perf_counter()
    response = httpx.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "x-goog-api-key": api_key},
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    response_json = response.json()
    if not isinstance(response_json, dict):
        raise ValueError("temporary provider response is not a JSON object")
    return persist_temporary_output(
        NANO_BANANA_2_TEMPORARY_NAME,
        response_json,
        save_path,
        timeout_seconds,
        time.perf_counter() - started_at,
        model,
    )
