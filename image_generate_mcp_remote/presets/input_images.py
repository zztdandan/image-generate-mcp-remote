"""Input image normalization shared by preset implementations."""

from __future__ import annotations

import base64
import binascii
import mimetypes
from pathlib import Path

from ..errors import ValidationError
from ..models.common import InputImage, InputImageFromBase64, InputImageFromDataUrl, InputImageFromPath, ResolvedInputImage


def resolve_input_image(tool_name: str, input_image: InputImage) -> ResolvedInputImage:
    """Normalize supported input image sources into bytes plus mime metadata."""

    if isinstance(input_image, InputImageFromPath):
        path_input = input_image
        file_path = Path(path_input.path)
        data = file_path.read_bytes()
        guessed_mime_type, _ = mimetypes.guess_type(file_path.name)
        mime_type = path_input.mime_type or guessed_mime_type or "image/png"
        return ResolvedInputImage(
            mime_type=mime_type,
            filename=path_input.filename or file_path.name,
            data=data,
        )

    if isinstance(input_image, InputImageFromBase64):
        base64_input = input_image
        try:
            decoded = base64.b64decode(base64_input.data_base64)
        except binascii.Error as exc:
            raise ValidationError(tool_name, "edit", "input image base64 is invalid") from exc
        return ResolvedInputImage(
            mime_type=base64_input.mime_type,
            filename=base64_input.filename,
            data=decoded,
        )

    if not isinstance(input_image, InputImageFromDataUrl):
        raise ValidationError(tool_name, "edit", "unsupported input image source type")
    data_url_input = input_image
    prefix, _, payload = data_url_input.data_url.partition(",")
    if not prefix.startswith("data:") or ";base64" not in prefix or not payload:
        raise ValidationError(tool_name, "edit", "data_url input is invalid")
    mime_type = prefix[5:].split(";", maxsplit=1)[0]
    try:
        decoded = base64.b64decode(payload)
    except binascii.Error as exc:
        raise ValidationError(tool_name, "edit", "data_url base64 payload is invalid") from exc
    file_extension = mimetypes.guess_extension(mime_type) or ".bin"
    return ResolvedInputImage(
        mime_type=mime_type,
        filename=data_url_input.filename or f"upload{file_extension}",
        data=decoded,
    )
