"""Official-style OpenAI Images tool implementation."""

from __future__ import annotations

import base64
import binascii
import mimetypes
import time
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, field_validator, model_validator

from ..config import GPT_IMAGE_2_OFFICIAL_NAME, ToolRuntimeConfig, get_settings
from ..errors import ConfigError, ResponseParseError, UpstreamErrorDetail, UpstreamServiceError, ValidationError
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ResolvedInputImage, ToolVersion, UsageInfo
from ..storage import build_image_uri, decode_base64_image, save_image_bytes_to_path

GPT_IMAGE_GENERATIONS_PATH = "/images/generations"
GPT_IMAGE_EDITS_PATH = "/images/edits"
GPT_IMAGE_SUPPORTED_EDIT_IMAGE_MAX = 16
GPT_IMAGE_MIN_PIXELS = 655360
GPT_IMAGE_MAX_PIXELS = 8294400
GPT_IMAGE_MAX_EDGE = 3840
GPT_IMAGE_SIZE_STEP = 16
GPT_IMAGE_MAX_ASPECT_RATIO = 3
GPT_IMAGE_RESPONSE_EXCERPT_LIMIT = 400


class GptImageQuality(StrEnum):
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GptImageOutputFormat(StrEnum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class GptImageBackground(StrEnum):
    AUTO = "auto"
    OPAQUE = "opaque"


class GptImageModeration(StrEnum):
    AUTO = "auto"
    LOW = "low"


class GptImageCount(IntEnum):
    SINGLE = 1


class GptImageGenerateRequest(BaseModel):
    """Generate mode contract for gpt_image_2_official."""

    version: ToolVersion
    mode: Literal[ImageToolMode.GENERATE]
    prompt: str
    save_path: str
    model: str | None = None
    size: str | None = "auto"
    quality: GptImageQuality = GptImageQuality.AUTO
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG
    output_compression: int | None = None
    background: GptImageBackground = GptImageBackground.AUTO
    moderation: GptImageModeration = GptImageModeration.AUTO
    n: GptImageCount = GptImageCount.SINGLE

    @field_validator("output_compression")
    @classmethod
    def validate_output_compression(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 0 or value > 100:
            raise ValueError("output_compression must be within 0..100")
        return value

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_gpt_size(value)
        return value


class GptImageEditRequest(BaseModel):
    """Edit mode contract for gpt_image_2_official."""

    version: ToolVersion
    mode: Literal[ImageToolMode.EDIT]
    prompt: str
    save_path: str
    model: str | None = None
    images: list[InputImage]
    mask: InputImage | None = None
    size: str | None = "auto"
    quality: GptImageQuality = GptImageQuality.AUTO
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG
    output_compression: int | None = None
    background: GptImageBackground = GptImageBackground.AUTO

    @model_validator(mode="after")
    def validate_images_count(self) -> "GptImageEditRequest":
        image_count: int = len(self.images)
        if image_count < 1 or image_count > GPT_IMAGE_SUPPORTED_EDIT_IMAGE_MAX:
            raise ValueError("images must contain between 1 and 16 items")
        return self

    @field_validator("output_compression")
    @classmethod
    def validate_output_compression(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 0 or value > 100:
            raise ValueError("output_compression must be within 0..100")
        return value

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_gpt_size(value)
        return value


def _validate_gpt_size(size: str) -> None:
    """Apply the local size validation contract from the design spec."""

    preset_sizes: set[str] = {
        "auto",
        "1024x1024",
        "1536x1024",
        "1024x1536",
        "2048x2048",
        "2048x1152",
        "3840x2160",
        "2160x3840",
    }
    if size in preset_sizes:
        return

    parts: list[str] = size.split("x")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError("size must use the format <width>x<height>")

    width: int = int(parts[0])
    height: int = int(parts[1])
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integers")
    if max(width, height) > GPT_IMAGE_MAX_EDGE:
        raise ValueError("the longest image edge must be <= 3840")
    if width % GPT_IMAGE_SIZE_STEP != 0 or height % GPT_IMAGE_SIZE_STEP != 0:
        raise ValueError("width and height must be divisible by 16")
    if max(width, height) / min(width, height) > GPT_IMAGE_MAX_ASPECT_RATIO:
        raise ValueError("image aspect ratio must be <= 3:1")

    total_pixels: int = width * height
    if total_pixels < GPT_IMAGE_MIN_PIXELS or total_pixels > GPT_IMAGE_MAX_PIXELS:
        raise ValueError("image pixel count must stay within [655360, 8294400]")


def _mime_type_for_output(output_format: GptImageOutputFormat) -> str:
    return f"image/{output_format.value}"


def _build_endpoint(base_url: str, path: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith("/v1"):
        return f"{normalized_base_url}{path}"
    return f"{normalized_base_url}/v1{path}"


def _build_headers(runtime_config: ToolRuntimeConfig) -> dict[str, str]:
    if not runtime_config.api_key:
        raise ConfigError(runtime_config.tool_name, "config", "missing API key")
    return {
        "Authorization": f"Bearer {runtime_config.api_key}",
    }


def _resolve_input_image(input_image: InputImage) -> ResolvedInputImage:
    """Normalize supported input image sources into bytes plus mime metadata."""

    if hasattr(input_image, "path"):
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

    if hasattr(input_image, "data_base64"):
        base64_input = input_image
        try:
            decoded = base64.b64decode(base64_input.data_base64)
        except binascii.Error as exc:
            raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, "edit", "input image base64 is invalid") from exc
        return ResolvedInputImage(
            mime_type=base64_input.mime_type,
            filename=base64_input.filename,
            data=decoded,
        )

    data_url_input = input_image
    prefix, _, payload = data_url_input.data_url.partition(",")
    if not prefix.startswith("data:") or ";base64" not in prefix or not payload:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, "edit", "data_url input is invalid")
    mime_type = prefix[5:].split(";", maxsplit=1)[0]
    try:
        decoded = base64.b64decode(payload)
    except binascii.Error as exc:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, "edit", "data_url base64 payload is invalid") from exc
    file_extension: str = mimetypes.guess_extension(mime_type) or ".bin"
    return ResolvedInputImage(
        mime_type=mime_type,
        filename=data_url_input.filename or f"upload{file_extension}",
        data=decoded,
    )


def _extract_usage(response_json: dict[str, object]) -> UsageInfo | None:
    usage_object = response_json.get("usage")
    if not isinstance(usage_object, dict):
        return None
    input_tokens = usage_object.get("input_tokens")
    output_tokens = usage_object.get("output_tokens")
    total_tokens = usage_object.get("total_tokens")
    return UsageInfo(
        input_tokens=input_tokens if isinstance(input_tokens, int) else None,
        output_tokens=output_tokens if isinstance(output_tokens, int) else None,
        total_tokens=total_tokens if isinstance(total_tokens, int) else None,
    )


def _provider_excerpt(response_json: dict[str, object]) -> dict[str, str]:
    created = response_json.get("created")
    created_text = str(created) if created is not None else ""
    return {"created": created_text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]}


def _parse_image_response(
    mode: ImageToolMode,
    response_json: dict[str, object],
    provider_model: str,
    output_format: GptImageOutputFormat,
    save_path: str,
    elapsed_seconds: float,
) -> ImageToolResult:
    data_items = response_json.get("data")
    if not isinstance(data_items, list) or not data_items:
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response.data is missing")
    first_item = data_items[0]
    if not isinstance(first_item, dict):
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response.data[0] is invalid")

    image_base64 = first_item.get("b64_json")
    if not isinstance(image_base64, str) or not image_base64:
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response missing data[0].b64_json")

    image_bytes = decode_base64_image(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, image_base64)
    mime_type = _mime_type_for_output(output_format)
    file_path = save_image_bytes_to_path(image_bytes, save_path)
    return ImageToolResult(
        tool_name=GPT_IMAGE_2_OFFICIAL_NAME,
        tool_version=ToolVersion.V1,
        mode=mode,
        provider_model=provider_model,
        file_path=str(file_path),
        image_uri=build_image_uri(file_path),
        mime_type=mime_type,
        elapsed_seconds=elapsed_seconds,
        usage=_extract_usage(response_json),
        provider_response_excerpt=_provider_excerpt(response_json),
    )


def _handle_upstream_response(mode: ImageToolMode, response: httpx.Response) -> dict[str, object]:
    if response.is_error:
        raise UpstreamServiceError(
            GPT_IMAGE_2_OFFICIAL_NAME,
            mode.value,
            UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]),
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "provider response is not a JSON object")
    return payload


def gpt_image_2_official_generate(
    version: ToolVersion,
    mode: Literal[ImageToolMode.GENERATE],
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
) -> ImageToolResult:
    """Run the generate mode for gpt_image_2_official."""

    request = GptImageGenerateRequest(
        version=version,
        mode=mode,
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
    )
    runtime_config = get_settings().gpt_image_2_official_config()
    if request.model and request.model not in runtime_config.supported_models_effective:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    payload: dict[str, str | int] = {
        "prompt": request.prompt,
        "model": request.model or runtime_config.effective_model,
        "quality": request.quality.value,
        "output_format": request.output_format.value,
        "background": request.background.value,
        "moderation": request.moderation.value,
        "n": int(request.n),
    }
    if request.size is not None:
        payload["size"] = request.size
    if request.output_compression is not None:
        payload["output_compression"] = request.output_compression

    started_at: float = time.perf_counter()
    response = httpx.post(
        _build_endpoint(runtime_config.effective_base_url, GPT_IMAGE_GENERATIONS_PATH),
        headers=_build_headers(runtime_config),
        json=payload,
        timeout=get_settings().image_http_timeout_seconds,
    )
    elapsed_seconds: float = time.perf_counter() - started_at
    response_json = _handle_upstream_response(request.mode, response)
    return _parse_image_response(
        request.mode,
        response_json,
        payload["model"],
        request.output_format,
        request.save_path,
        elapsed_seconds,
    )


def gpt_image_2_official_edit(
    version: ToolVersion,
    mode: Literal[ImageToolMode.EDIT],
    prompt: str,
    save_path: str,
    images: list[InputImage],
    mask: InputImage | None = None,
    model: str | None = None,
    size: str | None = "auto",
    quality: GptImageQuality = GptImageQuality.AUTO,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
) -> ImageToolResult:
    """Run the edit mode for gpt_image_2_official."""

    request = GptImageEditRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        model=model,
        images=images,
        mask=mask,
        size=size,
        quality=quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
    )
    runtime_config = get_settings().gpt_image_2_official_config()
    if request.model and request.model not in runtime_config.supported_models_effective:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    form_data: dict[str, str] = {
        "prompt": request.prompt,
        "model": request.model or runtime_config.effective_model,
        "quality": request.quality.value,
        "output_format": request.output_format.value,
        "background": request.background.value,
    }
    if request.size is not None:
        form_data["size"] = request.size
    if request.output_compression is not None:
        form_data["output_compression"] = str(request.output_compression)

    multipart_files: list[tuple[str, tuple[str, bytes, str]]] = []
    for image in request.images:
        resolved_image = _resolve_input_image(image)
        multipart_files.append(
            ("image[]", (resolved_image.filename, resolved_image.data, resolved_image.mime_type))
        )
    if request.mask is not None:
        resolved_mask = _resolve_input_image(request.mask)
        multipart_files.append(("mask", (resolved_mask.filename, resolved_mask.data, resolved_mask.mime_type)))

    started_at: float = time.perf_counter()
    response = httpx.post(
        _build_endpoint(runtime_config.effective_base_url, GPT_IMAGE_EDITS_PATH),
        headers=_build_headers(runtime_config),
        data=form_data,
        files=multipart_files,
        timeout=get_settings().image_http_timeout_seconds,
    )
    elapsed_seconds: float = time.perf_counter() - started_at
    response_json = _handle_upstream_response(request.mode, response)
    return _parse_image_response(
        request.mode,
        response_json,
        form_data["model"],
        request.output_format,
        request.save_path,
        elapsed_seconds,
    )
