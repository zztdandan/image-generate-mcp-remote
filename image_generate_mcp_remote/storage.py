"""Image output persistence and URI generation helpers."""

from __future__ import annotations

import base64
import binascii
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .config import get_settings
from .errors import ResponseParseError

OUTPUT_EXTENSION_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpeg",
    "image/webp": ".webp",
}


def ensure_output_dir() -> Path:
    """Create the configured output directory when needed."""

    path = Path(get_settings().image_output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_image_uri(path: Path) -> str:
    """Build a public image URI or a local file URI."""

    image_base_url: str = get_settings().image_base_url
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


def decode_base64_image(tool_name: str, mode: str, image_base64: str) -> bytes:
    """Decode provider base64 output into raw bytes."""

    try:
        return base64.b64decode(image_base64)
    except binascii.Error as exc:
        raise ResponseParseError(tool_name, mode, "provider returned invalid base64 image data") from exc
