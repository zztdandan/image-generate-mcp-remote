"""Main MCP server implementation."""

from __future__ import annotations

import argparse
import base64
import binascii
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

from .config import Settings

logger = logging.getLogger(__name__)
settings = Settings()
mcp = FastMCP(name="Image Generate MCP Remote")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remote MCP server for image generation")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3001)
    return parser.parse_args()


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def _output_dir() -> Path:
    path = Path(settings.image_output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_base64_image(image_base64: str) -> Path:
    try:
        content = base64.b64decode(image_base64)
    except binascii.Error as exc:
        raise RuntimeError("OpenAI did not return valid base64 image data") from exc

    file_path = _output_dir() / f"img_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}.png"
    file_path.write_bytes(content)
    return file_path


def _public_uri(path: Path) -> str:
    if settings.image_base_url:
        return f"{settings.image_base_url.rstrip('/')}/{path.name}"
    return path.resolve().as_uri()


@mcp.tool(title="Health Check", description="Check whether the server is ready")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "image-generate-mcp-remote",
        "model": settings.image_model,
        "output_dir": str(_output_dir()),
    }


@mcp.tool(title="Generate Image", description="Generate an image from a prompt")
def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    background: str = "auto",
) -> dict[str, str]:
    client = _client()
    result = client.images.generate(
        model=settings.image_model,
        prompt=prompt,
        size=size,
        quality=quality,
        background=background,
    )

    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("OpenAI did not return image content")

    file_path = _save_base64_image(result.data[0].b64_json)
    return {
        "status": "ok",
        "model": settings.image_model,
        "prompt": prompt,
        "file_path": str(file_path),
        "image_uri": _public_uri(file_path),
    }


def main() -> None:
    args = parse_args()
    configure_logging(settings.log_level)

    if args.transport in {"sse", "streamable-http"}:
        mcp.settings.host = args.host
        mcp.settings.port = args.port

    try:
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as exc:
        logger.error("Server failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
