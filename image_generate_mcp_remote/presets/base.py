"""Base preset classes with default merging and request validation."""

from __future__ import annotations

import base64
import time
import mimetypes

import httpx

from ..contracts.enums import ImageOutputFormat, ImageResponseModality
from ..contracts.image_size import (
    ImageAspectRatio,
    ImageSizeProvider,
    ImageSizeTier,
    SupportedImageSize,
    SupportedImageSizes,
    provider_size_value,
    supported_image_size_error_message,
)
from ..contracts.presets import (
    ImageToolPresetConfig,
    PresetDispatchPolicy,
    PresetFieldDispatchMode,
    PresetModeSupport,
    PresetProtocol,
    PresetProvider,
    PresetRuntimeConfig,
    PresetStability,
    PresetToolName,
    UnsupportedSizePreset,
)
from ..errors import ConfigError, ResponseParseError, UpstreamErrorDetail, UpstreamServiceError, ValidationError
from ..models.common import ImageToolMode, ImageToolResult, ResolvedInputImage, ToolVersion, UsageInfo
from .input_images import resolve_input_image
from .models import GptImage2EditExecutionRequest, GptImage2ExecutionRequest, GptImage2GenerateExecutionRequest, GptImage2PreparedRequest, NanoBananaEditExecutionRequest, NanoBananaExecutionRequest, NanoBananaPreparedRequest, ResolvedImageToolPreset

PRESET_DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS = 180.0
PRESET_DEFAULT_TOOL_RETRY_COUNT = 3
GPT_IMAGE_GENERATIONS_PATH = "/images/generations"
GPT_IMAGE_EDITS_PATH = "/images/edits"
GPT_IMAGE_RESPONSE_EXCERPT_LIMIT = 400
NANO_BANANA_RESPONSE_EXCERPT_LIMIT = 400
RETRY_TO_TOTAL_ATTEMPTS_OFFSET = 1


class BaseImageToolPreset:
    """Common defaults and validation shared by all formal image presets."""

    preset_id: str = "base_image_tool"
    tool_name: PresetToolName = PresetToolName.GPT_IMAGE_2_OFFICIAL
    provider: PresetProvider = PresetProvider.CUSTOM
    protocol: PresetProtocol = PresetProtocol.OPENAI_IMAGES
    base_url: str = ""
    model: str = ""
    modes: tuple[PresetModeSupport, ...] = (PresetModeSupport.GENERATE,)
    stability: PresetStability = PresetStability.STABLE
    notes: tuple[str, ...] = ()
    unsupported_sizes: tuple[UnsupportedSizePreset, ...] = ()
    dispatch: PresetDispatchPolicy = PresetDispatchPolicy(
        size=PresetFieldDispatchMode.SEND,
        quality=PresetFieldDispatchMode.SEND,
        output_format=PresetFieldDispatchMode.SEND,
        background=PresetFieldDispatchMode.SEND,
        moderation=PresetFieldDispatchMode.SEND,
    )
    runtime: PresetRuntimeConfig = PresetRuntimeConfig(
        timeout_seconds=PRESET_DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
        retry_count=PRESET_DEFAULT_TOOL_RETRY_COUNT,
    )

    def default_config(self) -> ImageToolPresetConfig:
        """Return the effective config declared by this preset class."""

        return ImageToolPresetConfig(
            preset_id=self.preset_id,
            tool_name=self.tool_name,
            provider=self.provider,
            protocol=self.protocol,
            base_url=self.base_url,
            model=self.model,
            modes=list(self.modes),
            dispatch=self.dispatch,
            runtime=self.runtime,
            unsupported_sizes=list(self.unsupported_sizes),
            notes=list(self.notes),
            stability=self.stability,
        )

    def resolve(self) -> ResolvedImageToolPreset:
        """Resolve class defaults into a runtime object consumed by tools and catalog."""

        config = self.default_config()
        self._validate_config(config)
        return ResolvedImageToolPreset(config=config, preset_class=self.__class__.__name__)

    def validate_tool_request(
        self,
        mode: PresetModeSupport,
        image_size: ImageSizeTier,
        aspect_ratio: ImageAspectRatio,
    ) -> None:
        """Reject requests unsupported by the active preset before calling upstream."""

        resolved = self.resolve()
        if mode not in resolved.config.modes:
            raise ValidationError(resolved.config.tool_name.value, mode.value, "active preset does not support this mode")
        if (image_size, aspect_ratio) in resolved.unsupported_size_keys:
            raise ValidationError(
                resolved.config.tool_name.value,
                mode.value,
                supported_image_size_error_message(
                    "image_size plus aspect_ratio is not supported by the active preset",
                    resolved.supported_sizes,
                    provider=self.size_provider,
                ),
            )

    @property
    def size_provider(self) -> ImageSizeProvider:
        return ImageSizeProvider.GPT

    def prompt_with_dispatch_fallback(
        self,
        prompt: str,
        image_size: ImageSizeTier,
        aspect_ratio: ImageAspectRatio,
        quality: str | None,
    ) -> str:
        """Move fields into prompt text only when the preset policy requires it."""

        requirements: list[str] = []
        resolved = self.resolve()
        if resolved.requires_prompt_fallback("size"):
            requirements.append(f"Target image size: {provider_size_value(image_size, aspect_ratio, provider=self.size_provider)}.")
        if resolved.requires_prompt_fallback("quality") and quality and quality != "auto":
            requirements.append(f"Target image quality: {quality}.")
        if not requirements:
            return prompt
        formatted_requirements = "\n".join(f"- {item}" for item in requirements)
        return f"{prompt}\n\nProvider parameter fallback requirements:\n{formatted_requirements}"

    def _validate_config(self, config: ImageToolPresetConfig) -> None:
        if not config.modes:
            raise ValueError(f"Preset {config.preset_id} must support at least one mode")
        unsupported_keys = [(item.image_size, item.aspect_ratio) for item in config.unsupported_sizes]
        if len(unsupported_keys) != len(set(unsupported_keys)):
            raise ValueError(f"Preset {config.preset_id} has duplicate unsupported size entries")
        if len(unsupported_keys) >= len(config.unsupported_sizes) + len(self.resolve_supported_sizes(config)):
            raise ValueError(f"Preset {config.preset_id} disables every shared size")

    def resolve_supported_sizes(self, config: ImageToolPresetConfig) -> tuple[SupportedImageSize, ...]:
        unsupported_keys = {(item.image_size, item.aspect_ratio) for item in config.unsupported_sizes}
        return tuple(item for item in SupportedImageSizes.all() if (item.tier, item.aspect_ratio) not in unsupported_keys)


class BaseGptImage2Preset(BaseImageToolPreset):
    """OpenAI Images compatible preset family for gpt_image_2_official."""

    preset_id = "openai_gpt_image_2"
    tool_name = PresetToolName.GPT_IMAGE_2_OFFICIAL
    provider = PresetProvider.OPENAI
    protocol = PresetProtocol.OPENAI_IMAGES
    base_url = "https://api.openai.com/v1"
    model = "gpt-image-2"
    modes = (PresetModeSupport.GENERATE, PresetModeSupport.EDIT)

    def execute_gpt_image_2(self, request: GptImage2ExecutionRequest, api_key: str) -> ImageToolResult:
        """Execute a GPT Image 2 request using this preset's OpenAI Images behavior."""

        if not api_key:
            raise ConfigError(self.tool_name.value, request.mode.value, "missing API key")
        mode = PresetModeSupport(request.mode.value)
        self.validate_tool_request(mode, request.image_size, request.aspect_ratio)
        prepared = self.prepare_gpt_image_2_request(request)
        started_at = time.perf_counter()
        raw_response = self.send_gpt_image_2_request(request, prepared, api_key)
        elapsed_seconds = time.perf_counter() - started_at
        return self.parse_gpt_image_2_response(request, raw_response, elapsed_seconds)

    def prepare_gpt_image_2_request(self, request: GptImage2ExecutionRequest) -> GptImage2PreparedRequest:
        """Build JSON or multipart payload according to this preset's dispatch policy."""

        resolved = self.resolve()
        mode = PresetModeSupport(request.mode.value)
        prompt = self.prompt_with_dispatch_fallback(request.prompt, request.image_size, request.aspect_ratio, request.quality.value)
        payload: dict[str, str | int] = {"prompt": prompt, "model": resolved.config.model}
        if mode is PresetModeSupport.GENERATE and isinstance(request, GptImage2GenerateExecutionRequest):
            payload["n"] = int(request.n)
        if resolved.config.dispatch.output_format is PresetFieldDispatchMode.SEND:
            payload["output_format"] = request.output_format.value
        if resolved.config.dispatch.background is PresetFieldDispatchMode.SEND:
            payload["background"] = request.background.value
        if isinstance(request, GptImage2GenerateExecutionRequest) and resolved.config.dispatch.moderation is PresetFieldDispatchMode.SEND:
            payload["moderation"] = request.moderation.value
        if resolved.config.dispatch.quality is PresetFieldDispatchMode.SEND:
            payload["quality"] = request.quality.value
        if resolved.config.dispatch.size is PresetFieldDispatchMode.SEND:
            payload["size"] = provider_size_value(request.image_size, request.aspect_ratio, provider=ImageSizeProvider.GPT)
        if request.output_compression is not None:
            payload["output_compression"] = request.output_compression

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        if isinstance(request, GptImage2EditExecutionRequest):
            for image in request.images:
                resolved_image = resolve_input_image(self.tool_name.value, image)
                files.append(("image[]", (resolved_image.filename, resolved_image.data, resolved_image.mime_type)))
            if request.mask is not None:
                resolved_mask = resolve_input_image(self.tool_name.value, request.mask)
                files.append(("mask", (resolved_mask.filename, resolved_mask.data, resolved_mask.mime_type)))
        return GptImage2PreparedRequest(payload=payload, files=files)

    def send_gpt_image_2_request(self, request: GptImage2ExecutionRequest, prepared: GptImage2PreparedRequest, api_key: str) -> dict[str, object]:
        """Send one or more OpenAI Images compatible attempts."""

        headers = {"Authorization": f"Bearer {api_key}"}
        mode = PresetModeSupport(request.mode.value)
        path = GPT_IMAGE_EDITS_PATH if mode is PresetModeSupport.EDIT else GPT_IMAGE_GENERATIONS_PATH
        endpoint = self.endpoint_for_path(path)
        last_error: httpx.RequestError | ResponseParseError | UpstreamServiceError | None = None
        total_attempts = self.resolve().config.runtime.retry_count + RETRY_TO_TOTAL_ATTEMPTS_OFFSET
        for attempt in range(1, total_attempts + 1):
            try:
                if mode is PresetModeSupport.EDIT:
                    response = httpx.post(endpoint, headers=headers, data={key: str(value) for key, value in prepared.payload.items()}, files=prepared.files, timeout=self.resolve().config.runtime.timeout_seconds)
                else:
                    response = httpx.post(endpoint, headers=headers, json=prepared.payload, timeout=self.resolve().config.runtime.timeout_seconds)
                return self.handle_gpt_image_2_upstream_response(mode, response)
            except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
                last_error = exc
                if attempt == total_attempts:
                    raise
        if last_error is not None:
            raise last_error
        raise ResponseParseError(self.tool_name.value, request.mode.value, "provider request did not return a response")

    def parse_gpt_image_2_response(self, request: GptImage2ExecutionRequest, response_json: dict[str, object], elapsed_seconds: float) -> ImageToolResult:
        """Accept b64_json, url, or mixed OpenAI-compatible data entries."""

        data_items = response_json.get("data")
        if not isinstance(data_items, list) or not data_items:
            raise ResponseParseError(self.tool_name.value, request.mode.value, "response.data is missing")
        first_item = data_items[0]
        if not isinstance(first_item, dict):
            raise ResponseParseError(self.tool_name.value, request.mode.value, "response.data[0] is invalid")
        image_base64 = first_item.get("b64_json")
        source_url = first_item.get("url")
        provider_excerpt_source_url: str | None = None
        if isinstance(image_base64, str) and image_base64:
            from ..storage import decode_base64_image

            image_bytes = decode_base64_image(self.tool_name.value, request.mode.value, self.normalize_provider_base64(image_base64))
            mime_type = self.mime_type_for_output(request.output_format)
        elif isinstance(source_url, str) and source_url.startswith("https://"):
            download_response = self.download_image_with_timeout(PresetModeSupport(request.mode.value), source_url)
            image_bytes = download_response.content
            mime_type = self.mime_type_from_download(download_response, request.save_path, source_url)
            provider_excerpt_source_url = source_url
        else:
            raise ResponseParseError(self.tool_name.value, request.mode.value, "response missing data[0].b64_json or data[0].url")
        from ..storage import build_image_uri, require_image_dimensions, save_image_bytes_to_path

        width, height = require_image_dimensions(self.tool_name.value, request.mode.value, image_bytes)
        file_path = save_image_bytes_to_path(image_bytes, request.save_path)
        return ImageToolResult(
            tool_name=self.tool_name.value,
            tool_version=ToolVersion.V1,
            mode=ImageToolMode(request.mode.value),
            provider_model=self.resolve().config.model,
            file_path=str(file_path),
            image_uri=build_image_uri(file_path),
            mime_type=mime_type,
            elapsed_seconds=elapsed_seconds,
            width=width,
            height=height,
            usage=self.extract_openai_usage(response_json),
            provider_response_excerpt=self.gpt_provider_excerpt(response_json, provider_excerpt_source_url),
        )

    def endpoint_for_path(self, path: str) -> str:
        normalized_base_url = self.resolve().config.base_url.rstrip("/")
        if normalized_base_url.endswith("/v1"):
            return f"{normalized_base_url}{path}"
        return f"{normalized_base_url}/v1{path}"

    def handle_gpt_image_2_upstream_response(self, mode: PresetModeSupport, response: httpx.Response) -> dict[str, object]:
        if response.is_error:
            raise UpstreamServiceError(self.tool_name.value, mode.value, UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]))
        payload = response.json()
        if not isinstance(payload, dict):
            raise ResponseParseError(self.tool_name.value, mode.value, "provider response is not a JSON object")
        return payload

    def download_image_with_timeout(self, mode: PresetModeSupport, image_url: str) -> httpx.Response:
        response = httpx.get(image_url, timeout=self.resolve().config.runtime.timeout_seconds, follow_redirects=True)
        if response.is_error:
            raise UpstreamServiceError(self.tool_name.value, mode.value, UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]))
        return response

    def normalize_provider_base64(self, value: str) -> str:
        _, separator, payload = value.partition(",")
        normalized = payload if separator and value.startswith("data:") else value
        return normalized + "=" * ((4 - len(normalized) % 4) % 4)

    def mime_type_for_output(self, output_format: ImageOutputFormat) -> str:
        return f"image/{output_format.value}"

    def mime_type_from_download(self, download_response: httpx.Response, save_path: str, image_url: str) -> str:
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

    def extract_openai_usage(self, response_json: dict[str, object]) -> UsageInfo | None:
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

    def gpt_provider_excerpt(self, response_json: dict[str, object], source_url: str | None = None) -> dict[str, str]:
        created = response_json.get("created")
        created_text = str(created) if created is not None else ""
        excerpt = {"created": created_text[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]}
        if source_url is not None:
            excerpt["source_url"] = source_url[:GPT_IMAGE_RESPONSE_EXCERPT_LIMIT]
        return excerpt


class BaseNanoBananaPreset(BaseImageToolPreset):
    """Gemini generateContent compatible preset family for nano_banana_2_official."""

    preset_id = "google_nano_banana"
    tool_name = PresetToolName.NANO_BANANA_2_OFFICIAL
    provider = PresetProvider.GOOGLE
    protocol = PresetProtocol.GEMINI_GENERATE_CONTENT
    base_url = "https://generativelanguage.googleapis.com"
    model = "gemini-3.1-flash-image-preview"
    modes = (PresetModeSupport.GENERATE, PresetModeSupport.EDIT)
    dispatch = PresetDispatchPolicy(
        size=PresetFieldDispatchMode.SEND,
        quality=PresetFieldDispatchMode.DROP,
        output_format=PresetFieldDispatchMode.SEND,
        background=PresetFieldDispatchMode.DROP,
        moderation=PresetFieldDispatchMode.DROP,
    )

    @property
    def size_provider(self) -> ImageSizeProvider:
        return ImageSizeProvider.NANO_BANANA

    def execute_nano_banana(self, request: NanoBananaExecutionRequest, api_key: str) -> ImageToolResult:
        """Execute a Nano Banana request using this preset's Gemini behavior."""

        if not api_key:
            raise ConfigError(self.tool_name.value, request.mode.value, "missing API key")
        mode = PresetModeSupport(request.mode.value)
        self.validate_tool_request(mode, request.image_size, request.aspect_ratio)
        prepared = self.prepare_nano_banana_request(request)
        started_at = time.perf_counter()
        raw_response = self.send_nano_banana_request(request, prepared, api_key)
        elapsed_seconds = time.perf_counter() - started_at
        return self.parse_nano_banana_response(request, raw_response, elapsed_seconds)

    def prepare_nano_banana_request(self, request: NanoBananaExecutionRequest) -> NanoBananaPreparedRequest:
        input_images = request.input_images if isinstance(request, NanoBananaEditExecutionRequest) else []
        inline_images = [resolve_input_image(self.tool_name.value, image) for image in input_images]
        parts: list[dict[str, object]] = [{"text": request.prompt}]
        for input_image in inline_images:
            parts.append(self.nano_image_part(input_image))
        payload: dict[str, object] = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": [modality.value for modality in request.response_modalities],
                "imageConfig": {"aspectRatio": request.aspect_ratio.value, "imageSize": request.image_size.value},
            },
            "thinkingConfig": {"thinkingLevel": request.thinking_level.value, "includeThoughts": request.include_thoughts},
        }
        return NanoBananaPreparedRequest(payload=payload, inline_images=inline_images)

    def nano_image_part(self, resolved_image: ResolvedInputImage) -> dict[str, object]:
        return {"inlineData": {"mimeType": resolved_image.mime_type, "data": base64.b64encode(resolved_image.data).decode("utf-8")}}

    def send_nano_banana_request(self, request: NanoBananaExecutionRequest, prepared: NanoBananaPreparedRequest, api_key: str) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "x-goog-api-key": api_key}
        endpoint = f"{self.resolve().config.base_url.rstrip('/')}/v1beta/models/{self.resolve().config.model}:generateContent"
        total_attempts = self.resolve().config.runtime.retry_count + RETRY_TO_TOTAL_ATTEMPTS_OFFSET
        last_error: httpx.RequestError | ResponseParseError | UpstreamServiceError | None = None
        for attempt in range(1, total_attempts + 1):
            try:
                response = httpx.post(endpoint, headers=headers, json=prepared.payload, timeout=self.resolve().config.runtime.timeout_seconds)
                return self.handle_nano_banana_upstream_response(PresetModeSupport(request.mode.value), response)
            except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
                last_error = exc
                if attempt == total_attempts:
                    raise
        if last_error is not None:
            raise last_error
        raise ResponseParseError(self.tool_name.value, request.mode.value, "provider request did not return a response")

    def parse_nano_banana_response(self, request: NanoBananaExecutionRequest, response_json: dict[str, object], elapsed_seconds: float) -> ImageToolResult:
        candidates = response_json.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ResponseParseError(self.tool_name.value, request.mode.value, "response.candidates is missing")
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
                if not isinstance(inline_data, dict):
                    inline_data = part.get("inline_data")
                if isinstance(inline_data, dict):
                    mime_type_value = inline_data.get("mimeType")
                    if not isinstance(mime_type_value, str):
                        mime_type_value = inline_data.get("mime_type")
                    data = inline_data.get("data")
                    if isinstance(mime_type_value, str) and isinstance(data, str) and data:
                        image_bytes = base64.b64decode(data)
                        from ..storage import build_image_uri, require_image_dimensions, save_image_bytes_to_path

                        width, height = require_image_dimensions(self.tool_name.value, request.mode.value, image_bytes)
                        file_path = save_image_bytes_to_path(image_bytes, request.save_path)
                        return ImageToolResult(
                            tool_name=self.tool_name.value,
                            tool_version=ToolVersion.V1,
                            mode=ImageToolMode(request.mode.value),
                            provider_model=self.resolve().config.model,
                            file_path=str(file_path),
                            image_uri=build_image_uri(file_path),
                            mime_type=mime_type_value,
                            elapsed_seconds=elapsed_seconds,
                            width=width,
                            height=height,
                            usage=self.nano_usage_info(response_json),
                            provider_response_excerpt=self.nano_provider_excerpt(response_json),
                            text_output="\n".join(text_fragments) if ImageResponseModality.TEXT in request.response_modalities and text_fragments else None,
                        )
                text_value = part.get("text")
                if ImageResponseModality.TEXT in request.response_modalities and isinstance(text_value, str) and text_value:
                    text_fragments.append(text_value)
        raise ResponseParseError(self.tool_name.value, request.mode.value, "response missing candidates[].content.parts[].inlineData.data")

    def handle_nano_banana_upstream_response(self, mode: PresetModeSupport, response: httpx.Response) -> dict[str, object]:
        if response.is_error:
            raise UpstreamServiceError(self.tool_name.value, mode.value, UpstreamErrorDetail(status_code=response.status_code, body_excerpt=response.text[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT]))
        payload = response.json()
        if not isinstance(payload, dict):
            raise ResponseParseError(self.tool_name.value, mode.value, "provider response is not a JSON object")
        return payload

    def nano_usage_info(self, response_json: dict[str, object]) -> UsageInfo | None:
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

    def nano_provider_excerpt(self, response_json: dict[str, object]) -> dict[str, str]:
        model_version = response_json.get("modelVersion")
        response_id = response_json.get("responseId")
        return {
            "modelVersion": str(model_version)[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT] if model_version is not None else "",
            "responseId": str(response_id)[:NANO_BANANA_RESPONSE_EXCERPT_LIMIT] if response_id is not None else "",
        }
