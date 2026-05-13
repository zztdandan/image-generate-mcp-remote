"""Main MCP server implementation for image-only tools."""

from __future__ import annotations

import argparse
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import SERVICE_NAME, get_settings
from .models.common import ImageToolMode, InputImage, ToolVersion
from .tools.catalog import list_image_tools_catalog
from .tools.gpt_image_2_official import (
    GptImageBackground,
    GptImageCount,
    GptImageModeration,
    GptImageOutputFormat,
    GptImageQuality,
    gpt_image_2_official_edit,
    gpt_image_2_official_generate,
)
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
    """Configure root logging for CLI startup."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for supported MCP transports."""

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
    """Expose image tool catalog as an MCP tool."""

    return list_image_tools_catalog(version).model_dump(mode="json")


@mcp.tool(
    title="GPT Image 2 Official",
    description=(
        "Generate or edit images via the OpenAI Images compatible gateway. "
        "The size parameter accepts auto or a '<width>x<height>' value; invalid size errors include the supported preset list. "
        "Call list_image_tools_catalog first when you need the current supported size presets."
    ),
)
def gpt_image_2_official(
    version: ToolVersion,
    mode: ImageToolMode,
    prompt: str,
    save_path: str,
    model: str | None = None,
    size: str | None = "auto",
    quality: GptImageQuality = GptImageQuality.AUTO,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
    moderation: GptImageModeration = GptImageModeration.AUTO,
    n: GptImageCount = GptImageCount.SINGLE,
    images: list[InputImage] | None = None,
    mask: InputImage | None = None,
) -> dict[str, object]:
    """Expose generate/edit behavior behind one product-level tool."""

    if mode is ImageToolMode.GENERATE:
        return gpt_image_2_official_generate(
            version=version,
            mode=ImageToolMode.GENERATE,
            prompt=prompt,
            save_path=save_path,
            model=model,
            size=size,
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
        model=model,
        images=images or [],
        mask=mask,
        size=size,
        quality=quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
    ).model_dump(mode="json")


@mcp.tool(
    title="Nano Banana 2 Official",
    description=(
        "Generate or edit images via the Gemini compatible gateway. "
        "Prefer aspect_ratio plus image_size, or pass size as '<width>x<height>' to map to the nearest shared preset. "
        "Invalid size errors include the supported preset list."
    ),
)
def nano_banana_2_official(
    version: ToolVersion,
    mode: ImageToolMode,
    prompt: str,
    save_path: str,
    model: str | None = None,
    size: str | None = None,
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio | None = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize | None = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
    input_images: list[InputImage] | None = None,
) -> dict[str, object]:
    """Expose generate/edit behavior behind one product-level tool."""

    if mode is ImageToolMode.GENERATE:
        return nano_banana_2_official_generate(
            version=version,
            mode=ImageToolMode.GENERATE,
            prompt=prompt,
            save_path=save_path,
            model=model,
            size=size,
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
        model=model,
        size=size,
        response_modalities=response_modalities,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    ).model_dump(mode="json")


@mcp.tool(
    name="gpt-image-2-url",
    title="GPT Image 2 URL",
    description=(
        "Generate images through the right.codes draw-compatible endpoint. "
        "This tool asks upstream for response_format=url, then downloads that returned image URL and saves it to save_path; "
        "callers do not need to download the URL themselves. "
        "The image parameter is an optional list of reference image URLs, not an output URL. "
        "The size parameter must be one supported '<width>x<height>' preset; invalid size errors include the supported list. "
        "Call list_image_tools_catalog first to inspect supported_size_presets and image_http_timeout_seconds."
    ),
)
def gpt_image_2_url(
    version: ToolVersion,
    prompt: str,
    save_path: str,
    model: str | None = None,
    image: list[str] | None = None,
    size: str | None = None,

) -> dict[str, object]:
    """Expose the URL-returning image gateway as an MCP tool."""

    return gpt_image_2_url_generate(
        version=version,
        prompt=prompt,
        save_path=save_path,
        model=model,
        image=image,
        size=size,
    ).model_dump(mode="json")


def main() -> None:
    """Start the MCP server using the selected transport."""

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
