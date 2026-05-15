"""server 模块用于MCP 工具入口编排，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import argparse
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS, DEFAULT_TOOL_RETRY_COUNT, SERVICE_NAME, get_settings
from .contracts.image_size import ImageAspectRatio, ImageSizeTier
from .models.common import ImageToolMode, InputImage, ToolVersion
from .tools.catalog import list_image_tools_catalog
from .tools.gpt_image_2_temporary import gpt_image_2_temporary_generate
from .tools.gpt_image_2_official import (
    GptImageBackground,
    GptImageCount,
    GptImageModeration,
    GptImageOutputFormat,
    GptImageQuality,
    gpt_image_2_official_edit,
    gpt_image_2_official_generate,
)
from .tools.nano_banana_2_temporary import nano_banana_2_temporary_generate
from .tools.nano_banana_2_official import (
    NanoBananaAspectRatio,
    NanoBananaImageSize,
    NanoBananaThinkingLevel,
    ResponseModality,
    nano_banana_2_official_edit,
    nano_banana_2_official_generate,
)
from .tools.gpt_image_2_url import gpt_image_2_url_generate

logger = logging.getLogger(__name__)
mcp = FastMCP(name="Image Generate MCP Remote")


def configure_logging(level: str) -> None:
    """执行 configure_logging，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def parse_args() -> argparse.Namespace:
    """执行 parse_args，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析输入并转换为内部可用结构
        - 步骤 2：校验格式后输出标准化结果
    """

    parser = argparse.ArgumentParser(description="Remote MCP server for image generation")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="streamable-http",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3001)
    return parser.parse_args()


@mcp.tool(title="Image Tools Catalog", description="List image tool defaults and effective config")
def list_image_tools_catalog_tool(version: ToolVersion) -> dict[str, object]:
    """执行 list_image_tools_catalog_tool，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：汇总可用工具信息并对外返回
        - 步骤 2：遍历配置后生成统一目录结构
    """

    return list_image_tools_catalog(version).model_dump(mode="json")


@mcp.tool(
    title="GPT Image 2 Official",
    description=(
        "Generate or edit images via the OpenAI Images compatible gateway. "
        "The active startup preset owns provider, model, timeout, retry, and field dispatch behavior. "
        "Select image_size plus aspect_ratio from the catalog enums to derive the provider size preset. "
        "Call list_image_tools_catalog first when you need the current supported size presets."
    ),
)
def gpt_image_2_official(
    version: ToolVersion,
    mode: ImageToolMode,
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
    images: list[InputImage] | None = None,
    mask: InputImage | None = None,
) -> dict[str, object]:
    """执行 gpt_image_2_official，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    if mode is ImageToolMode.GENERATE:
        return gpt_image_2_official_generate(
            version=version,
            mode=ImageToolMode.GENERATE,
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
        ).model_dump(mode="json")
    return gpt_image_2_official_edit(
        version=version,
            mode=ImageToolMode.EDIT,
            prompt=prompt,
            save_path=save_path,
            images=images or [],
            mask=mask,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            quality=quality,
            output_format=output_format,
            output_compression=output_compression,
            background=background,
        ).model_dump(mode="json")


@mcp.tool(
    title="Nano Banana 2 Official",
    description=(
        "Generate or edit images via the Gemini compatible gateway. "
        "The active startup preset owns provider, model, timeout, retry, and field dispatch behavior. "
        "Use image_size plus aspect_ratio from the shared catalog enums. "
        "Invalid size errors include the supported preset list."
    ),
)
def nano_banana_2_official(
    version: ToolVersion,
    mode: ImageToolMode,
    prompt: str,
    save_path: str,
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
    input_images: list[InputImage] | None = None,
) -> dict[str, object]:
    """执行 nano_banana_2_official，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    if mode is ImageToolMode.GENERATE:
        return nano_banana_2_official_generate(
            version=version,
            mode=ImageToolMode.GENERATE,
            prompt=prompt,
            save_path=save_path,
            response_modalities=response_modalities,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            thinking_level=thinking_level,
            include_thoughts=include_thoughts,
        ).model_dump(mode="json")
    return nano_banana_2_official_edit(
        version=version,
        mode=ImageToolMode.EDIT,
        prompt=prompt,
        save_path=save_path,
        input_images=input_images or [],
        response_modalities=response_modalities,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    ).model_dump(mode="json")


@mcp.tool(
    title="GPT Image 2 Temporary",
    description=(
        "Temporary OpenAI Images-compatible exploration tool. "
        "Allows per-call api_key, base_url, model, and timeout, but sends only conservative fields by default."
    ),
)
def gpt_image_2_temporary(
    version: ToolVersion,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    save_path: str,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    quality: GptImageQuality = GptImageQuality.AUTO,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    background: GptImageBackground = GptImageBackground.AUTO,
    moderation: GptImageModeration = GptImageModeration.AUTO,
    send_quality: bool = False,
    send_output_format: bool = False,
    send_background: bool = False,
    send_moderation: bool = False,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """执行 gpt_image_2_temporary，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return gpt_image_2_temporary_generate(
        version=version,
        api_key=api_key,
        base_url=base_url,
        model=model,
        prompt=prompt,
        save_path=save_path,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        output_format=output_format,
        background=background,
        moderation=moderation,
        send_quality=send_quality,
        send_output_format=send_output_format,
        send_background=send_background,
        send_moderation=send_moderation,
        timeout_seconds=timeout_seconds,
    ).model_dump(mode="json")


@mcp.tool(
    title="Nano Banana 2 Temporary",
    description=(
        "Temporary Gemini generateContent-compatible exploration tool. "
        "Allows per-call api_key, base_url, model, and timeout for unknown providers."
    ),
)
def nano_banana_2_temporary(
    version: ToolVersion,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    save_path: str,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    response_modalities: list[ResponseModality] | None = None,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """执行 nano_banana_2_temporary，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return nano_banana_2_temporary_generate(
        version=version,
        api_key=api_key,
        base_url=base_url,
        model=model,
        prompt=prompt,
        save_path=save_path,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        response_modalities=response_modalities,
        timeout_seconds=timeout_seconds,
    ).model_dump(mode="json")


@mcp.tool(
    name="gpt-image-2-url",
    title="GPT Image 2 URL",
    description=(
        "Generate images through the right.codes draw-compatible endpoint. "
        "This tool asks upstream for response_format=url, then downloads that returned image URL and saves it to save_path; "
        "callers do not need to download the URL themselves. "
        "The image parameter is an optional list of reference image URLs, not an output URL. "
        "Use image_size plus aspect_ratio from the shared catalog enums; only benchmark-verified combinations are accepted. "
        "Call list_image_tools_catalog first to inspect supported_size_presets and image_http_timeout_seconds."
    ),
)
def gpt_image_2_url(
    version: ToolVersion,
    prompt: str,
    save_path: str,
    model: str | None = None,
    image: list[str] | None = None,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
    retry_count: int = DEFAULT_TOOL_RETRY_COUNT,

) -> dict[str, object]:
    """执行 gpt_image_2_url，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return gpt_image_2_url_generate(
        version=version,
        prompt=prompt,
        save_path=save_path,
        model=model,
        image=image,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
    ).model_dump(mode="json")


def main() -> None:
    """执行 main，用于 MCP 工具入口编排 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    args = parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)

    if args.transport in {"sse", "streamable-http"}:
        mcp.settings.host = args.host
        mcp.settings.port = args.port

    try:
        logger.info("Starting %s", SERVICE_NAME)
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as exc:
        logger.error("Server failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
