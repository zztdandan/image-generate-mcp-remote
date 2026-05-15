"""Image output persistence and URI generation helpers."""

from __future__ import annotations

import base64
import binascii
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .errors import ResponseParseError

OUTPUT_EXTENSION_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpeg",
    "image/webp": ".webp",
}
IMAGE_OUTPUT_DIR_ENV = "IMAGE_OUTPUT_DIR"
IMAGE_BASE_URL_ENV = "IMAGE_BASE_URL"
DEFAULT_OUTPUT_DIR = "storage/images"


def ensure_output_dir() -> Path:
    """Create the configured output directory when needed."""

    path = Path(os.getenv(IMAGE_OUTPUT_DIR_ENV, DEFAULT_OUTPUT_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_image_uri(path: Path) -> str:
    """Build a public image URI or a local file URI."""

    image_base_url = os.getenv(IMAGE_BASE_URL_ENV, "")
    if image_base_url:
        return f"{image_base_url.rstrip('/')}/{path.name}"
    return path.resolve().as_uri()


def _build_filename(mime_type: str) -> str:
    """Generate a stable output filename using mime type as extension."""

    extension: str = OUTPUT_EXTENSION_BY_MIME.get(mime_type, ".bin")
    timestamp: str = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"img_{timestamp}_{uuid4().hex[:8]}{extension}"


def save_image_bytes(image_bytes: bytes, mime_type: str) -> Path:
    """Persist image bytes to the configured output directory."""

    file_path = ensure_output_dir() / _build_filename(mime_type)
    file_path.write_bytes(image_bytes)
    return file_path


def save_image_bytes_to_path(image_bytes: bytes, save_path: str) -> Path:
    """Persist image bytes to a caller-provided path."""

    file_path = Path(save_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(image_bytes)
    return file_path


def decode_base64_image(tool_name: str, mode: str, image_base64: str) -> bytes:
    """Decode provider base64 output into raw bytes."""

    try:
        return base64.b64decode(image_base64)
    except binascii.Error as exc:
        raise ResponseParseError(tool_name, mode, "provider returned invalid base64 image data") from exc


def _png_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    png_signature = b"\x89PNG\r\n\x1a\n"
    if len(image_bytes) < 24 or not image_bytes.startswith(png_signature):
        return None
    if image_bytes[12:16] != b"IHDR":
        return None
    width = int.from_bytes(image_bytes[16:20], byteorder="big")
    height = int.from_bytes(image_bytes[20:24], byteorder="big")
    if width <= 0 or height <= 0:
        return None
    return width, height


def _jpeg_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    if len(image_bytes) < 4 or not image_bytes.startswith(b"\xff\xd8"):
        return None

    offset = 2
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset + 1 < len(image_bytes):
        if image_bytes[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(image_bytes) and image_bytes[offset] == 0xFF:
            offset += 1
        if offset >= len(image_bytes):
            return None
        marker = image_bytes[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(image_bytes):
            return None
        segment_length = int.from_bytes(image_bytes[offset : offset + 2], byteorder="big")
        if segment_length < 2 or offset + segment_length > len(image_bytes):
            return None
        if marker in sof_markers:
            if offset + 7 > len(image_bytes):
                return None
            height = int.from_bytes(image_bytes[offset + 3 : offset + 5], byteorder="big")
            width = int.from_bytes(image_bytes[offset + 5 : offset + 7], byteorder="big")
            if width <= 0 or height <= 0:
                return None
            return width, height
        offset += segment_length
    return None


def _webp_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    if len(image_bytes) < 30 or not image_bytes.startswith(b"RIFF") or image_bytes[8:12] != b"WEBP":
        return None

    chunk_type = image_bytes[12:16]
    if chunk_type == b"VP8X" and len(image_bytes) >= 30:
        width = int.from_bytes(image_bytes[24:27], byteorder="little") + 1
        height = int.from_bytes(image_bytes[27:30], byteorder="little") + 1
        if width <= 0 or height <= 0:
            return None
        return width, height

    if chunk_type == b"VP8L" and len(image_bytes) >= 25:
        packed = int.from_bytes(image_bytes[21:25], byteorder="little")
        width = (packed & 0x3FFF) + 1
        height = ((packed >> 14) & 0x3FFF) + 1
        if width <= 0 or height <= 0:
            return None
        return width, height

    if chunk_type == b"VP8 ":
        signature = b"\x9d\x01\x2a"
        signature_index = image_bytes.find(signature)
        if signature_index == -1 or signature_index + 7 > len(image_bytes):
            return None
        width = int.from_bytes(image_bytes[signature_index + 3 : signature_index + 5], byteorder="little") & 0x3FFF
        height = int.from_bytes(image_bytes[signature_index + 5 : signature_index + 7], byteorder="little") & 0x3FFF
        if width <= 0 or height <= 0:
            return None
        return width, height

    return None


def extract_image_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    """Extract image dimensions from common image byte formats."""

    for detector in (_png_dimensions, _jpeg_dimensions, _webp_dimensions):
        dimensions = detector(image_bytes)
        if dimensions is not None:
            return dimensions
    return None


def require_image_dimensions(tool_name: str, mode: str, image_bytes: bytes) -> tuple[int, int]:
    """Extract image dimensions or fail when the payload cannot be parsed."""

    dimensions = extract_image_dimensions(image_bytes)
    if dimensions is None:
        raise ResponseParseError(tool_name, mode, "provider returned an image with unreadable dimensions")
    return dimensions
