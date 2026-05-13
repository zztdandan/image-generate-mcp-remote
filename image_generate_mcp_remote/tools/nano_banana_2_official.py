"""Official-style Gemini generateContent image tool implementation."""

from __future__ import annotations

import base64
import time
from enum import StrEnum
from typing import Literal

import httpx
from pydantic import BaseModel, model_validator

from ..config import NANO_BANANA_2_OFFICIAL_NAME, ToolRuntimeConfig, get_settings
from ..errors import ConfigError, ResponseParseError, UpstreamErrorDetail, UpstreamServiceError, ValidationError
from ..models.common import ImageToolMode, ImageToolResult, InputImage, ResolvedInputImage, ToolVersion, UsageInfo
from ..storage import build_image_uri, save_image_bytes_to_path
from .gpt_image_2_official import _resolve_input_image

NANO_BANANA_RESPONSE_EXCERPT_LIMIT = 400


class ResponseModality(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"


class NanoBananaAspectRatio(StrEnum):
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    CLASSIC = "4:3"
    TALL = "3:4"


class NanoBananaImageSize(StrEnum):
    SIZE_1K = "1K"
    SIZE_2K = "2K"


class NanoBananaThinkingLevel(StrEnum):
    MINIMAL = "minimal"
    HIGH = "High"


class NanoBananaGenerateRequest(BaseModel):
    """Generate mode contract for nano_banana_2_official."""

    version: ToolVersion
    mode: Literal[ImageToolMode.GENERATE]
    prompt: str
    save_path: str
    model: str | None = None
    response_modalities: list[ResponseModality] = [ResponseModality.IMAGE]
    aspect_ratio: NanoBananaAspectRatio | None = NanoBananaAspectRatio.SQUARE
    image_size: NanoBananaImageSize | None = NanoBananaImageSize.SIZE_1K
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL
    include_thoughts: bool = False

    @model_validator(mode="after")
    def validate_modalities(self) -> "NanoBananaGenerateRequest":
        _validate_response_modalities(self.response_modalities)
        return self


class NanoBananaEditRequest(BaseModel):
    """Edit mode contract for nano_banana_2_official."""

    version: ToolVersion
    mode: Literal[ImageToolMode.EDIT]
    prompt: str
    save_path: str
    input_images: list[InputImage]
    model: str | None = None
    response_modalities: list[ResponseModality] = [ResponseModality.IMAGE]
    aspect_ratio: NanoBananaAspectRatio | None = NanoBananaAspectRatio.SQUARE
    image_size: NanoBananaImageSize | None = NanoBananaImageSize.SIZE_1K
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL
    include_thoughts: bool = False

    @model_validator(mode="after")
    def validate_contract(self) -> "NanoBananaEditRequest":
        _validate_response_modalities(self.response_modalities)
        if not self.input_images:
            raise ValueError("input_images must contain at least one item")
        return self


def _build_endpoint(runtime_config: ToolRuntimeConfig, model_name: str) -> str:
    return f"{runtime_config.effective_base_url.rstrip('/')}/v1beta/models/{model_name}:generateContent"


def _build_headers(runtime_config: ToolRuntimeConfig) -> dict[str, str]:
    if not runtime_config.api_key:
        raise ConfigError(runtime_config.tool_name, "config", "missing API key")
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": runtime_config.api_key,
    }


def _validate_response_modalities(response_modalities: list[ResponseModality]) -> None:
    if ResponseModality.IMAGE not in response_modalities:
        raise ValueError("response_modalities must include IMAGE")


def _image_part(resolved_image: ResolvedInputImage) -> dict[str, dict[str, str]]:
    return {
        "inlineData": {
            "mimeType": resolved_image.mime_type,
            "data": base64.b64encode(resolved_image.data).decode("utf-8"),
        }
    }


def _payload(
    prompt: str,
    response_modalities: list[ResponseModality],
    aspect_ratio: NanoBananaAspectRatio | None,
    image_size: NanoBananaImageSize | None,
    thinking_level: NanoBananaThinkingLevel,
    include_thoughts: bool,
    inline_images: list[ResolvedInputImage],
) -> dict[str, object]:
    parts: list[dict[str, object]] = [{"text": prompt}]
    for input_image in inline_images:
        parts.append(_image_part(input_image))

    image_config: dict[str, str] = {}
    if aspect_ratio is not None:
        image_config["aspectRatio"] = aspect_ratio.value
    if image_size is not None:
        image_config["imageSize"] = image_size.value

    payload: dict[str, object] = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": [modality.value for modality in response_modalities],
            "imageConfig": image_config,
        },
        "thinkingConfig": {
            "thinkingLevel": thinking_level.value,
            "includeThoughts": include_thoughts,
        },
    }
    return payload


def _usage_info(response_json: dict[str, object]) -> UsageInfo | None:
    usage_metadata = response_json.get("usageMetadata")
    if not isinstance(usage_metadata, dict):
        return None
    prompt_token_count = usage_metadata.get("promptTokenCount")
    candidates_token_count = usage_metadata.get("candidatesTokenCount")
    total_token_count = usage_metadata.get("totalTokenCount")
    return UsageInfo(
        input_tokens=prompt_token_count if isinstance(prompt_token_count, int) else None,
        output_tokens=candidates_token_count if isinstance(candidates_token_count, int) else None,
        total_tokens=total_token_count if isinstance(total_token_count, int) else None,
    )


def _provider_excerpt(response_json: dict[str, object]) -> dict[str, str]:
    model_version = response_json.get("modelVersion")
    response_id = response_json.get("responseId")
    return {
        "modelVersion": str(model_version)[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT] if model_version is not None else "",
        "responseId": str(response_id)[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT] if response_id is not None else "",
    }


def _parse_response(
    mode: ImageToolMode,
    response_json: dict[str, object],
    provider_model: str,
    include_text_output: bool,
    save_path: str,
    elapsed_seconds: float,
) -> ImageToolResult:
    candidates = response_json.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ResponseParseError(NANO_BANANA_2_OFFICIAL_NAME, mode.value, "response.candidates is missing")

    text_fragments: list[str] = []
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
            if isinstance(inline_data, dict):
                mime_type = inline_data.get("mimeType")
                data = inline_data.get("data")
                if isinstance(mime_type, str) and isinstance(data, str) and data:
                    image_bytes = base64.b64decode(data)
                    file_path = save_image_bytes_to_path(image_bytes, save_path)
                    return ImageToolResult(
                        tool_name=NANO_BANANA_2_OFFICIAL_NAME,
                        tool_version=ToolVersion.V1,
                        mode=mode,
                        provider_model=provider_model,
                        file_path=str(file_path),
                        image_uri=build_image_uri(file_path),
                        mime_type=mime_type,
                        elapsed_seconds=elapsed_seconds,
                        usage=_usage_info(response_json),
                        provider_response_excerpt=_provider_excerpt(response_json),
                        text_output="\n".join(text_fragments) if include_text_output and text_fragments else None,
                    )
            text_value = part.get("text")
            if include_text_output and isinstance(text_value, str) and text_value:
                text_fragments.append(text_value)

    raise ResponseParseError(NANO_BANANA_2_OFFICIAL_NAME, mode.value, "response missing candidates[].content.parts[].inlineData.data")


def _handle_upstream_response(mode: ImageToolMode, response: httpx.Response) -> dict[str, object]:
    if response.is_error:
        raise UpstreamServiceError(
            NANO_BANANA_2_OFFICIAL_NAME,
            mode.value,
            UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT]),
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise ResponseParseError(NANO_BANANA_2_OFFICIAL_NAME, mode.value, "provider response is not a JSON object")
    return payload


def nano_banana_2_official_generate(
    version: ToolVersion,
    mode: Literal[ImageToolMode.GENERATE],
    prompt: str,
    save_path: str,
    model: str | None = None,
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio | None = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize | None = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
) -> ImageToolResult:
    """Run the generate mode for nano_banana_2_official."""

    request = NanoBananaGenerateRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        model=model,
        response_modalities=response_modalities or [ResponseModality.IMAGE],
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    )
    runtime_config = get_settings().nano_banana_2_official_config()
    provider_model: str = request.model or runtime_config.effective_model
    if provider_model not in runtime_config.supported_models_effective:
        raise ValidationError(NANO_BANANA_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    started_at: float = time.perf_counter()
    response = httpx.post(
        _build_endpoint(runtime_config, provider_model),
        headers=_build_headers(runtime_config),
        json=_payload(
            prompt=request.prompt,
            response_modalities=request.response_modalities,
            aspect_ratio=request.aspect_ratio,
            image_size=request.image_size,
            thinking_level=request.thinking_level,
            include_thoughts=request.include_thoughts,
            inline_images=[],
        ),
        timeout=get_settings().image_http_timeout_seconds,
    )
    elapsed_seconds: float = time.perf_counter() - started_at
    response_json = _handle_upstream_response(request.mode, response)
    return _parse_response(
        request.mode,
        response_json,
        provider_model,
        ResponseModality.TEXT in request.response_modalities,
        request.save_path,
        elapsed_seconds,
    )


def nano_banana_2_official_edit(
    version: ToolVersion,
    mode: Literal[ImageToolMode.EDIT],
    prompt: str,
    save_path: str,
    input_images: list[InputImage],
    model: str | None = None,
    response_modalities: list[ResponseModality] | None = None,
    aspect_ratio: NanoBananaAspectRatio | None = NanoBananaAspectRatio.SQUARE,
    image_size: NanoBananaImageSize | None = NanoBananaImageSize.SIZE_1K,
    thinking_level: NanoBananaThinkingLevel = NanoBananaThinkingLevel.MINIMAL,
    include_thoughts: bool = False,
) -> ImageToolResult:
    """Run the edit mode for nano_banana_2_official."""

    request = NanoBananaEditRequest(
        version=version,
        mode=mode,
        prompt=prompt,
        save_path=save_path,
        input_images=input_images,
        model=model,
        response_modalities=response_modalities or [ResponseModality.IMAGE],
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        thinking_level=thinking_level,
        include_thoughts=include_thoughts,
    )
    runtime_config = get_settings().nano_banana_2_official_config()
    provider_model: str = request.model or runtime_config.effective_model
    if provider_model not in runtime_config.supported_models_effective:
        raise ValidationError(NANO_BANANA_2_OFFICIAL_NAME, request.mode.value, "requested model is not supported")

    resolved_images: list[ResolvedInputImage] = [_resolve_input_image(image) for image in request.input_images]
    started_at: float = time.perf_counter()
    response = httpx.post(
        _build_endpoint(runtime_config, provider_model),
        headers=_build_headers(runtime_config),
        json=_payload(
            prompt=request.prompt,
            response_modalities=request.response_modalities,
            aspect_ratio=request.aspect_ratio,
            image_size=request.image_size,
            thinking_level=request.thinking_level,
            include_thoughts=request.include_thoughts,
            inline_images=resolved_images,
        ),
        timeout=get_settings().image_http_timeout_seconds,
    )
    elapsed_seconds: float = time.perf_counter() - started_at
    response_json = _handle_upstream_response(request.mode, response)
    return _parse_response(
        request.mode,
        response_json,
        provider_model,
        ResponseModality.TEXT in request.response_modalities,
        request.save_path,
        elapsed_seconds,
    )
