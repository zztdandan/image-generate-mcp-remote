"""base 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import base64
import logging
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
from ..models.common import ActualSizeVerificationResult, ImageToolMode, ImageToolResult, ResolvedInputImage, ToolVersion, UsageInfo
from .input_images import resolve_input_image
from .models import GptImage2EditExecutionRequest, GptImage2ExecutionRequest, GptImage2GenerateExecutionRequest, GptImage2PreparedRequest, NanoBananaEditExecutionRequest, NanoBananaExecutionRequest, NanoBananaPreparedRequest, ResolvedImageToolPreset

PRESET_DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS = 180.0
PRESET_DEFAULT_TOOL_RETRY_COUNT = 3
GPT_IMAGE_GENERATIONS_PATH = "/images/generations"
GPT_IMAGE_EDITS_PATH = "/images/edits"
GPT_IMAGE_RESPONSE_EXCERPT_LIMIT = 400
NANO_BANANA_RESPONSE_EXCERPT_LIMIT = 400
RETRY_TO_TOTAL_ATTEMPTS_OFFSET = 1
logger = logging.getLogger(__name__)


class BaseImageToolPreset:
    """BaseImageToolPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

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
        """执行 default_config，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

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
        """执行 resolve，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：解析并确定最终生效配置
            - 步骤 2：合并输入来源后输出可执行结果
        """

        config = self.default_config()
        self._validate_config(config)
        return ResolvedImageToolPreset(config=config, preset_class=self.__class__.__name__)

    def validate_tool_request(
        self,
        mode: PresetModeSupport,
        image_size: ImageSizeTier,
        aspect_ratio: ImageAspectRatio,
    ) -> None:
        """执行 validate_tool_request，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：校验调用参数是否满足约束
            - 步骤 2：识别非法组合并尽早返回错误
        """

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
        """执行 prompt_with_dispatch_fallback，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

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

    def verify_actual_size(
        self,
        image_size: ImageSizeTier,
        aspect_ratio: ImageAspectRatio,
        actual_width: int,
        actual_height: int,
    ) -> ActualSizeVerificationResult:
        """执行 verify_actual_size，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：根据共享尺寸合同解析当前请求的预期尺寸
            - 步骤 2：返回实际尺寸与预期尺寸的一致性结果，不把不一致视为错误
        """

        expected_size = SupportedImageSizes.resolve(image_size, aspect_ratio).size_for_provider(self.size_provider)
        return ActualSizeVerificationResult(
            requested_image_size=image_size,
            requested_aspect_ratio=aspect_ratio,
            expected_width=expected_size.width,
            expected_height=expected_size.height,
            actual_width=actual_width,
            actual_height=actual_height,
            is_consistent=actual_width == expected_size.width and actual_height == expected_size.height,
        )


class BaseGptImage2Preset(BaseImageToolPreset):
    """BaseGptImage2Preset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "openai_gpt_image_2"
    tool_name = PresetToolName.GPT_IMAGE_2_OFFICIAL
    provider = PresetProvider.OPENAI
    protocol = PresetProtocol.OPENAI_IMAGES
    base_url = "https://api.openai.com/v1"
    model = "gpt-image-2"
    modes = (PresetModeSupport.GENERATE, PresetModeSupport.EDIT)

    def execute_gpt_image_2(self, request: GptImage2ExecutionRequest, api_key: str) -> ImageToolResult:
        """执行 execute_gpt_image_2，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

        if not api_key:
            raise ConfigError(self.tool_name.value, request.mode.value, "missing API key")
        mode = PresetModeSupport(request.mode.value)
        self.validate_tool_request(mode, request.image_size, request.aspect_ratio)
        prepared = self.prepare_gpt_image_2_request(request)
        logger.info(
            "Starting GPT image request preset=%s model=%s mode=%s image_size=%s aspect_ratio=%s timeout_seconds=%.1f retry_count=%d save_path=%s",
            self.resolve().config.preset_id,
            self.resolve().config.model,
            request.mode.value,
            request.image_size.value,
            request.aspect_ratio.value,
            self.resolve().config.runtime.timeout_seconds,
            self.resolve().config.runtime.retry_count,
            request.save_path,
        )
        started_at = time.perf_counter()
        raw_response = self.send_gpt_image_2_request(request, prepared, api_key)
        elapsed_seconds = time.perf_counter() - started_at
        return self.parse_gpt_image_2_response(request, raw_response, elapsed_seconds)

    def prepare_gpt_image_2_request(self, request: GptImage2ExecutionRequest) -> GptImage2PreparedRequest:
        """执行 prepare_gpt_image_2_request，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

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
        """执行 send_gpt_image_2_request，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：发送上游请求并收集响应内容
            - 步骤 2：按重试策略完成请求闭环
        """

        headers = {"Authorization": f"Bearer {api_key}"}
        mode = PresetModeSupport(request.mode.value)
        path = GPT_IMAGE_EDITS_PATH if mode is PresetModeSupport.EDIT else GPT_IMAGE_GENERATIONS_PATH
        endpoint = self.endpoint_for_path(path)
        last_error: httpx.RequestError | ResponseParseError | UpstreamServiceError | None = None
        total_attempts = self.resolve().config.runtime.retry_count + RETRY_TO_TOTAL_ATTEMPTS_OFFSET
        for attempt in range(1, total_attempts + 1):
            try:
                logger.info(
                    "Sending GPT image upstream request preset=%s attempt=%d/%d endpoint=%s timeout_seconds=%.1f payload_keys=%s has_files=%s",
                    self.resolve().config.preset_id,
                    attempt,
                    total_attempts,
                    endpoint,
                    self.resolve().config.runtime.timeout_seconds,
                    sorted(prepared.payload.keys()),
                    bool(prepared.files),
                )
                if mode is PresetModeSupport.EDIT:
                    response = httpx.post(endpoint, headers=headers, data={key: str(value) for key, value in prepared.payload.items()}, files=prepared.files, timeout=self.resolve().config.runtime.timeout_seconds)
                else:
                    response = httpx.post(endpoint, headers=headers, json=prepared.payload, timeout=self.resolve().config.runtime.timeout_seconds)
                logger.info(
                    "Received GPT image upstream response preset=%s attempt=%d/%d status_code=%d",
                    self.resolve().config.preset_id,
                    attempt,
                    total_attempts,
                    response.status_code,
                )
                return self.handle_gpt_image_2_upstream_response(mode, response)
            except (httpx.RequestError, ResponseParseError, UpstreamServiceError) as exc:
                last_error = exc
                logger.warning(
                    "GPT image upstream request failed preset=%s attempt=%d/%d error_type=%s will_retry=%s message=%s",
                    self.resolve().config.preset_id,
                    attempt,
                    total_attempts,
                    exc.__class__.__name__,
                    attempt < total_attempts,
                    str(exc),
                )
                if attempt == total_attempts:
                    raise
        if last_error is not None:
            raise last_error
        raise ResponseParseError(self.tool_name.value, request.mode.value, "provider request did not return a response")

    def parse_gpt_image_2_response(self, request: GptImage2ExecutionRequest, response_json: dict[str, object], elapsed_seconds: float) -> ImageToolResult:
        """执行 parse_gpt_image_2_response，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：解析输入并转换为内部可用结构
            - 步骤 2：校验格式后输出标准化结果
        """

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
        elif isinstance(source_url, str) and source_url:
            download_response = self.download_image_with_timeout(PresetModeSupport(request.mode.value), source_url)
            image_bytes = download_response.content
            mime_type = self.mime_type_from_download(download_response, request.save_path, source_url)
            provider_excerpt_source_url = source_url
        else:
            raise ResponseParseError(self.tool_name.value, request.mode.value, "response missing data[0].b64_json or data[0].url")
        from ..storage import build_image_uri, require_image_dimensions, save_image_bytes_to_path

        width, height = require_image_dimensions(self.tool_name.value, request.mode.value, image_bytes)
        actual_size_verification = self.verify_actual_size(request.image_size, request.aspect_ratio, width, height)
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
            actual_size_verification=actual_size_verification,
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
    """BaseNanoBananaPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

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
        """执行 execute_nano_banana，用于 preset 契约定义 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

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
                        actual_size_verification = self.verify_actual_size(request.image_size, request.aspect_ratio, width, height)
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
                            actual_size_verification=actual_size_verification,
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
