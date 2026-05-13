"""URL-returning GPT image tool implementation."""

from __future__ import annotations

import mimetypes
import time
from pathlib import Path

import httpx
from pydantic import Field, field_validator

from ..config import GPT_IMAGE_2_URL_NAME, ToolRuntimeConfig, get_settings
from ..contracts.requests import PromptedImageRequestBase
from ..contracts.image_size import SUPPORTED_IMAGE_SIZE_MAP
from ..errors import ConfigError, ResponseParseError, UpstreamErrorDetail, UpstreamServiceError, ValidationError
from ..models.common import ImageToolMode, ImageToolResult, ToolVersion, UsageInfo
from ..storage import build_image_uri, save_image_bytes_to_path

GPT_IMAGE_2_URL_GENERATIONS_PATH = "/images/generations"
GPT_IMAGE_2_URL_RESPONSE_EXCERPT_LIMIT = 400
GPT_IMAGE_2_URL_RESPONSE_FORMAT_URL = "url"
GPT_IMAGE_2_URL_MAX_ATTEMPTS = 3
GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL: frozenset[str] = frozenset(
    {
        "960x1280",
        "1280x720",
        "1360x2048",
        "2048x1152",
        "2048x864",
        "3520x2336",
        "2480x3312",
        "3312x2480",
        "2160x3840",
        "3840x2160",
        "3840x1632",
    }
)


class GptImage2UrlGenerateRequest(PromptedImageRequestBase):
    """Generate mode contract for the URL-returning gpt-image tool."""

    image: list[str] = Field(default_factory=list)
    size: str | None = None

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in SUPPORTED_IMAGE_SIZE_MAP:
            raise ValueError("size must be one of the shared supported image size presets")
        if value not in GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL:
            allowed_sizes = ", ".join(sorted(GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL))
            raise ValueError(f"size is not in the verified gpt-image-2-url size pool: {allowed_sizes}")
        return value


def _build_endpoint(base_url: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith(GPT_IMAGE_2_URL_GENERATIONS_PATH):
        return normalized_base_url
    return f"{normalized_base_url}{GPT_IMAGE_2_URL_GENERATIONS_PATH}"


def _build_headers(runtime_config: ToolRuntimeConfig) -> dict[str, str]:
    if not runtime_config.api_key:
        raise ConfigError(runtime_config.tool_name, "generate", "missing API key")
    return {
        "Authorization": f"Bearer {runtime_config.api_key}",
        "Content-Type": "application/json",
    }


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


def _provider_excerpt(response_json: dict[str, object], image_url: str) -> dict[str, str]:
    created = response_json.get("created")
    created_text = str(created) if created is not None else ""
    return {
        "created": created_text[:GPT_IMAGE_2_URL_RESPONSE_EXCERPT_LIMIT],
        "source_url": image_url[:GPT_IMAGE_2_URL_RESPONSE_EXCERPT_LIMIT],
    }


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


def _handle_upstream_response(response: httpx.Response) -> dict[str, object]:
    if response.is_error:
        raise UpstreamServiceError(
            GPT_IMAGE_2_URL_NAME,
            ImageToolMode.GENERATE.value,
            UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_2_URL_RESPONSE_EXCERPT_LIMIT]),
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise ResponseParseError(GPT_IMAGE_2_URL_NAME, ImageToolMode.GENERATE.value, "provider response is not a JSON object")
    return payload


def _extract_image_url(response_json: dict[str, object]) -> str:
    data_items = response_json.get("data")
    if not isinstance(data_items, list) or not data_items:
        raise ResponseParseError(GPT_IMAGE_2_URL_NAME, ImageToolMode.GENERATE.value, "response.data is missing")
    first_item = data_items[0]
    if not isinstance(first_item, dict):
        raise ResponseParseError(GPT_IMAGE_2_URL_NAME, ImageToolMode.GENERATE.value, "response.data[0] is invalid")
    image_url = first_item.get("url")
    if not isinstance(image_url, str) or not image_url.startswith("https://"):
        raise ResponseParseError(GPT_IMAGE_2_URL_NAME, ImageToolMode.GENERATE.value, "response missing data[0].url")
    return image_url


def _download_image(image_url: str) -> httpx.Response:
    response = httpx.get(image_url, timeout=get_settings().image_http_timeout_seconds, follow_redirects=True)
    if response.is_error:
        raise UpstreamServiceError(
            GPT_IMAGE_2_URL_NAME,
            ImageToolMode.GENERATE.value,
            UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_2_URL_RESPONSE_EXCERPT_LIMIT]),
    )
    return response


def _generate_and_download_once(runtime_config: ToolRuntimeConfig, request: GptImage2UrlGenerateRequest) -> tuple[dict[str, object], str, httpx.Response]:
    response = httpx.post(
        _build_endpoint(runtime_config.effective_base_url),
        headers=_build_headers(runtime_config),
        json={
            "model": request.model or runtime_config.effective_model,
            "prompt": request.prompt,
            "image": list(request.image),
            "response_format": GPT_IMAGE_2_URL_RESPONSE_FORMAT_URL,
            **({"size": request.size} if request.size is not None else {}),
        },
        timeout=get_settings().image_http_timeout_seconds,
    )
    response_json = _handle_upstream_response(response)
    image_url = _extract_image_url(response_json)
    download_response = _download_image(image_url)
    return response_json, image_url, download_response


def gpt_image_2_url_generate(
    version: ToolVersion,
    prompt: str,
    save_path: str,
    model: str | None = None,
    image: list[str] | None = None,
    size: str | None = None,
) -> ImageToolResult:
    """Run the URL-returning image endpoint and persist the downloaded image."""

    request = GptImage2UrlGenerateRequest(
        version=version,
        prompt=prompt,
        save_path=save_path,
        model=model,
        image=list(image or []),
        size=size,
    )
    runtime_config = get_settings().gpt_image_2_url_config()
    if request.model and request.model not in runtime_config.supported_models_effective:
        raise ValidationError(GPT_IMAGE_2_URL_NAME, ImageToolMode.GENERATE.value, "requested model is not supported")

    started_at: float = time.perf_counter()
    last_error: Exception | None = None
    for attempt in range(1, GPT_IMAGE_2_URL_MAX_ATTEMPTS + 1):
        try:
            response_json, image_url, download_response = _generate_and_download_once(runtime_config, request)
            elapsed_seconds: float = time.perf_counter() - started_at
            file_path = save_image_bytes_to_path(download_response.content, request.save_path)
            mime_type = _mime_type_from_download(download_response, request.save_path, image_url)
            return ImageToolResult(
                tool_name=GPT_IMAGE_2_URL_NAME,
                tool_version=ToolVersion.V1,
                mode=ImageToolMode.GENERATE,
                provider_model=request.model or runtime_config.effective_model,
                file_path=str(file_path),
                image_uri=build_image_uri(Path(file_path)),
                mime_type=mime_type,
                elapsed_seconds=elapsed_seconds,
                usage=_extract_usage(response_json),
                provider_response_excerpt=_provider_excerpt(response_json, image_url),
            )
        except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
            last_error = exc
            if attempt == GPT_IMAGE_2_URL_MAX_ATTEMPTS:
                raise

    assert last_error is not None
    raise last_error
