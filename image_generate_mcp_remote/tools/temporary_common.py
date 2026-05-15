"""Maximum-compatible output extraction for temporary image provider tools."""

from __future__ import annotations

import base64
import re

import httpx

from ..models.common import ImageToolMode, ImageToolResult, ToolVersion, UsageInfo
from ..storage import build_image_uri, decode_base64_image, require_image_dimensions, save_image_bytes_to_path

TEMPORARY_RESPONSE_EXCERPT_LIMIT = 400
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\((https://[^)]+)\)")
HTTPS_URL_PATTERN = re.compile(r"https://\S+")
DATA_URL_PATTERN = re.compile(r"data:(image/[^;]+);base64,([A-Za-z0-9+/=\s]+)")


def extract_json_image_output(payload: dict[str, object]) -> tuple[str | None, str | None]:
    """Return the first base64 payload or URL from common image provider responses."""

    data_items = payload.get("data")
    if isinstance(data_items, list):
        for item in data_items:
            if isinstance(item, dict):
                b64_json = item.get("b64_json")
                if isinstance(b64_json, str) and b64_json:
                    return b64_json, None
                url = item.get("url")
                if isinstance(url, str) and url.startswith("https://"):
                    return None, url

    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                inline_data = part.get("inlineData")
                if not isinstance(inline_data, dict):
                    inline_data = part.get("inline_data")
                if isinstance(inline_data, dict):
                    data = inline_data.get("data")
                    if isinstance(data, str) and data:
                        return data, None
                text = part.get("text")
                if isinstance(text, str):
                    scanned = extract_text_image_output(text)
                    if scanned != (None, None):
                        return scanned
    return None, None


def extract_text_image_output(text: str) -> tuple[str | None, str | None]:
    """Scan markdown, data URL, and plain URL text for a usable image output."""

    data_url_match = DATA_URL_PATTERN.search(text)
    if data_url_match is not None:
        return data_url_match.group(2), None
    markdown_match = MARKDOWN_IMAGE_PATTERN.search(text)
    if markdown_match is not None:
        return None, markdown_match.group(1)
    url_match = HTTPS_URL_PATTERN.search(text)
    if url_match is not None:
        return None, url_match.group(0).rstrip(").,]")
    return None, None


def persist_temporary_output(
    tool_name: str,
    response_json: dict[str, object],
    save_path: str,
    timeout_seconds: float,
    elapsed_seconds: float,
    provider_model: str,
) -> ImageToolResult:
    """Persist a temporary tool response after scanning common image output shapes."""

    image_base64, image_url = extract_json_image_output(response_json)
    mime_type = "image/png"
    if image_base64 is not None:
        image_bytes = decode_base64_image(tool_name, ImageToolMode.GENERATE.value, image_base64)
    elif image_url is not None:
        download_response = httpx.get(image_url, timeout=timeout_seconds, follow_redirects=True)
        download_response.raise_for_status()
        image_bytes = download_response.content
        header_mime_type = download_response.headers.get("Content-Type", "").split(";", maxsplit=1)[0].strip()
        if header_mime_type.startswith("image/"):
            mime_type = header_mime_type
    else:
        raise ValueError("temporary provider response did not contain a recognizable image output")

    width, height = require_image_dimensions(tool_name, ImageToolMode.GENERATE.value, image_bytes)
    file_path = save_image_bytes_to_path(image_bytes, save_path)
    return ImageToolResult(
        tool_name=tool_name,
        tool_version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        provider_model=provider_model,
        file_path=str(file_path),
        image_uri=build_image_uri(file_path),
        mime_type=mime_type,
        elapsed_seconds=elapsed_seconds,
        width=width,
        height=height,
        usage=UsageInfo(),
        provider_response_excerpt={"temporary": "true"},
    )


def data_url_from_bytes(mime_type: str, image_bytes: bytes) -> str:
    """Build a data URL for tests and temporary providers that return text."""

    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
