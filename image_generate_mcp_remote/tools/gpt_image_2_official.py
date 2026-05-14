"""Official-style OpenAI Images tool implementation."""

from __future__ import annotations

import base64
import binascii
import mimetypes
import time
from pathlib import Path
from typing import Literal

import httpx
from pydantic import field_validator, model_validator

from ..contracts.enums import ImageBackground, ImageCount, ImageModeration, ImageOutputFormat, ImageQuality
from ..contracts.requests import EditImageRequestBase, GenerateImageRequestBase
from ..contracts.image_size import (
    ImageAspectRatio,
    ImageSizeProvider,
    ImageSizeTier,
    provider_size_value,
    resolve_supported_size_selection,
)
from ..config import (
    DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
    DEFAULT_TOOL_RETRY_COUNT,
    GPT_IMAGE_2_OFFICIAL_NAME,
    ToolRuntimeConfig,
    get_settings,
)
from ..errors import ConfigError, ResponseParseError, UpstreamErrorDetail, UpstreamServiceError, ValidationError
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ResolvedInputImage, ToolVersion, UsageInfo
from ..storage import build_image_uri, decode_base64_image, require_image_dimensions, save_image_bytes_to_path

GPT_IMAGE_GENERATIONS_PATH = "/images/generations"
GPT_IMAGE_EDITS_PATH = "/images/edits"
GPT_IMAGE_SUPPORTED_EDIT_IMAGE_MAX = 16
GPT_IMAGE_RESPONSE_EXCERPT_LIMIT = 400
RETRY_TO_TOTAL_ATTEMPTS_OFFSET = 1
PROMPT_FALLBACK_HEADER = "Provider parameter fallback requirements:"


GptImageQuality = ImageQuality
GptImageOutputFormat = ImageOutputFormat
GptImageBackground = ImageBackground
GptImageModeration = ImageModeration
GptImageCount = ImageCount


class GptImageGenerateRequest(GenerateImageRequestBase):
    """Generate mode contract for gpt_image_2_official."""

    api_key: str | None = None
    base_url: str | None = None
    send_size: bool = True
    quality: GptImageQuality = GptImageQuality.AUTO
    send_quality: bool = True
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

class GptImageEditRequest(EditImageRequestBase):
    """Edit mode contract for gpt_image_2_official."""

    api_key: str | None = None
    base_url: str | None = None
    images: list[InputImage]
    mask: InputImage | None = None
    send_size: bool = True
    quality: GptImageQuality = GptImageQuality.AUTO
    send_quality: bool = True
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

def _mime_type_for_output(output_format: GptImageOutputFormat) -> str:
    return f"image/{output_format.value}"


def _mime_type_from_download(download_response: httpx.Response, save_path: str, image_url: str) -> str:
    header_mime_type = download_response.headers.get("Content-Type", "").split(";", maxsplit=1)[0].strip()
    if header_mime_type.startswith("image/"):
        return header_mime_type

    guessed_from_path, _ = mimetypes.guess_type(save_path)
    if guessed_from_path:
        return guessed_from_path

    guessed_from_url, _ = mimetypes.guess_type(image_url)
    if guessed_from_url:
        return guessed_from_url

    return "image/png"


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


def _provider_excerpt(response_json: dict[str, object], source_url: str | None = None) -> dict[str, str]:
    created = response_json.get("created")
    created_text = str(created) if created is not None else ""
    excerpt: dict[str, str] = {"created": created_text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]}
    if source_url is not None:
        excerpt["source_url"] = source_url[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]
    return excerpt


def _download_image_with_timeout(mode: ImageToolMode, image_url: str, timeout_seconds: float) -> httpx.Response:
    response = httpx.get(image_url, timeout=timeout_seconds, follow_redirects=True)
    if response.is_error:
        raise UpstreamServiceError(
            GPT_IMAGE_2_OFFICIAL_NAME,
            mode.value,
            UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]),
        )
    return response


def _build_provider_prompt(
    prompt: str,
    aspect_ratio: ImageAspectRatio,
    image_size: ImageSizeTier,
    send_size: bool,
    quality: GptImageQuality,
    send_quality: bool,
) -> str:
    requirements: list[str] = []
    if not send_size:
        requirements.append(
            f"Target image size: {provider_size_value(image_size, aspect_ratio, provider=ImageSizeProvider.GPT)}."
        )
    if not send_quality and quality is not GptImageQuality.AUTO:
        requirements.append(f"Target image quality: {quality.value}.")
    if not requirements:
        return prompt
    formatted_requirements = "\n".join(f"- {item}" for item in requirements)
    return f"{prompt}\n\n{PROMPT_FALLBACK_HEADER}\n{formatted_requirements}"


def _parse_image_response(
    mode: ImageToolMode,
    response_json: dict[str, object],
    provider_model: str,
    output_format: GptImageOutputFormat,
    save_path: str,
    timeout_seconds: float,
    elapsed_seconds: float,
) -> ImageToolResult:
    data_items = response_json.get("data")
    if not isinstance(data_items, list) or not data_items:
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response.data is missing")
    first_item = data_items[0]
    if not isinstance(first_item, dict):
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response.data[0] is invalid")

    image_base64 = first_item.get("b64_json")
    source_url = first_item.get("url")
    image_bytes: bytes
    mime_type: str
    provider_excerpt_source_url: str | None = None
    if isinstance(image_base64, str) and image_base64:
        image_bytes = decode_base64_image(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, image_base64)
        mime_type = _mime_type_for_output(output_format)
    elif isinstance(source_url, str) and source_url.startswith("https://"):
        download_response = _download_image_with_timeout(mode, source_url, timeout_seconds)
        image_bytes = download_response.content
        mime_type = _mime_type_from_download(download_response, save_path, source_url)
        provider_excerpt_source_url = source_url
    else:
        raise ResponseParseError(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, "response missing data[0].b64_json or data[0].url")

    width, height = require_image_dimensions(GPT_IMAGE_2_OFFICIAL_NAME, mode.value, image_bytes)
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
        width=width,
        height=height,
        usage=_extract_usage(response_json),
        provider_response_excerpt=_provider_excerpt(response_json, provider_excerpt_source_url),
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


def _post_generate_once(
    runtime_config: ToolRuntimeConfig,
    payload: dict[str, str | int],
    timeout_seconds: float,
) -> httpx.Response:
    """Send one generate request to the upstream image endpoint."""

    return httpx.post(
        _build_endpoint(runtime_config.effective_base_url, GPT_IMAGE_GENERATIONS_PATH),
        headers=_build_headers(runtime_config),
        json=payload,
        timeout=timeout_seconds,
    )


def _post_edit_once(
    runtime_config: ToolRuntimeConfig,
    form_data: dict[str, str],
    multipart_files: list[tuple[str, tuple[str, bytes, str]]],
    timeout_seconds: float,
) -> httpx.Response:
    """Send one edit request to the upstream image endpoint."""

    return httpx.post(
        _build_endpoint(runtime_config.effective_base_url, GPT_IMAGE_EDITS_PATH),
        headers=_build_headers(runtime_config),
        data=form_data,
        files=multipart_files,
        timeout=timeout_seconds,
    )


def gpt_image_2_official_generate(
    version: ToolVersion,
    mode: Literal[ImageToolMode.GENERATE],
    prompt: str,
    save_path: str,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    send_size: bool = True,
    quality: GptImageQuality = GptImageQuality.AUTO,
    send_quality: bool = True,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
    moderation: GptImageModeration = GptImageModeration.AUTO,
    n: GptImageCount = GptImageCount.SINGLE,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
    retry_count: int = DEFAULT_TOOL_RETRY_COUNT,
) -> ImageToolResult:
    """Run the generate mode for gpt_image_2_official."""

    request = GptImageGenerateRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        send_size=send_size,
        quality=quality,
        send_quality=send_quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
        moderation=moderation,
        n=n,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
    )
    runtime_config = get_settings().gpt_image_2_official_config(
        api_key_override=request.api_key,
        base_url_override=request.base_url,
        model_override=request.model,
    )
    if request.model and request.model not in runtime_config.supported_models_effective:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    resolve_supported_size_selection(request.image_size, request.aspect_ratio)

    payload: dict[str, str | int] = {
        "prompt": _build_provider_prompt(
            request.prompt,
            request.aspect_ratio,
            request.image_size,
            request.send_size,
            request.quality,
            request.send_quality,
        ),
        "model": request.model or runtime_config.effective_model,
        "output_format": request.output_format.value,
        "background": request.background.value,
        "moderation": request.moderation.value,
        "n": int(request.n),
    }
    if request.send_quality:
        payload["quality"] = request.quality.value
    if request.send_size:
        payload["size"] = provider_size_value(request.image_size, request.aspect_ratio, provider=ImageSizeProvider.GPT)
    if request.output_compression is not None:
        payload["output_compression"] = request.output_compression

    total_attempts: int = request.retry_count + RETRY_TO_TOTAL_ATTEMPTS_OFFSET
    started_at: float = time.perf_counter()
    last_error: httpx.RequestError | ResponseParseError | UpstreamServiceError | None = None
    response_json: dict[str, object] | None = None
    for attempt in range(1, total_attempts + 1):
        try:
            response = _post_generate_once(runtime_config, payload, request.timeout_seconds)
            response_json = _handle_upstream_response(request.mode, response)
            break
        except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
            last_error = exc
            if attempt == total_attempts:
                raise

    if response_json is None:
        assert last_error is not None
        raise last_error

    elapsed_seconds: float = time.perf_counter() - started_at
    return _parse_image_response(
        request.mode,
        response_json,
        payload["model"],
        request.output_format,
        request.save_path,
        request.timeout_seconds,
        elapsed_seconds,
    )


def gpt_image_2_official_edit(
    version: ToolVersion,
    mode: Literal[ImageToolMode.EDIT],
    prompt: str,
    save_path: str,
    images: list[InputImage],
    mask: InputImage | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE,
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K,
    send_size: bool = True,
    quality: GptImageQuality = GptImageQuality.AUTO,
    send_quality: bool = True,
    output_format: GptImageOutputFormat = GptImageOutputFormat.PNG,
    output_compression: int | None = None,
    background: GptImageBackground = GptImageBackground.AUTO,
    timeout_seconds: float = DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
    retry_count: int = DEFAULT_TOOL_RETRY_COUNT,
) -> ImageToolResult:
    """Run the edit mode for gpt_image_2_official."""

    request = GptImageEditRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        api_key=api_key,
        base_url=base_url,
        model=model,
        images=images,
        mask=mask,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        send_size=send_size,
        quality=quality,
        send_quality=send_quality,
        output_format=output_format,
        output_compression=output_compression,
        background=background,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
    )
    runtime_config = get_settings().gpt_image_2_official_config(
        api_key_override=request.api_key,
        base_url_override=request.base_url,
        model_override=request.model,
    )
    if request.model and request.model not in runtime_config.supported_models_effective:
        raise ValidationError(GPT_IMAGE_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    resolve_supported_size_selection(request.image_size, request.aspect_ratio)

    form_data: dict[str, str] = {
        "prompt": _build_provider_prompt(
            request.prompt,
            request.aspect_ratio,
            request.image_size,
            request.send_size,
            request.quality,
            request.send_quality,
        ),
        "model": request.model or runtime_config.effective_model,
        "output_format": request.output_format.value,
        "background": request.background.value,
    }
    if request.send_quality:
        form_data["quality"] = request.quality.value
    if request.send_size:
        form_data["size"] = provider_size_value(request.image_size, request.aspect_ratio, provider=ImageSizeProvider.GPT)
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

    total_attempts: int = request.retry_count + RETRY_TO_TOTAL_ATTEMPTS_OFFSET
    started_at: float = time.perf_counter()
    last_error: httpx.RequestError | ResponseParseError | UpstreamServiceError | None = None
    response_json: dict[str, object] | None = None
    for attempt in range(1, total_attempts + 1):
        try:
            response = _post_edit_once(runtime_config, form_data, multipart_files, request.timeout_seconds)
            response_json = _handle_upstream_response(request.mode, response)
            break
        except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
            last_error = exc
            if attempt == total_attempts:
                raise

    if response_json is None:
        assert last_error is not None
        raise last_error

    elapsed_seconds: float = time.perf_counter() - started_at
    return _parse_image_response(
        request.mode,
        response_json,
        form_data["model"],
        request.output_format,
        request.save_path,
        request.timeout_seconds,
        elapsed_seconds,
    )
