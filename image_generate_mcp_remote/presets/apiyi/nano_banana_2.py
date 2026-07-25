"""nano_banana_2 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import httpx

from ...contracts.presets import PresetModeSupport, PresetProvider, PresetRuntimeConfig
from ..base import BaseNanoBananaPreset
from ..models import NanoBananaExecutionRequest, NanoBananaPreparedRequest


class ApiYiNanoBanana2Preset(BaseNanoBananaPreset):
    """ApiYiNanoBanana2Preset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。

    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "apiyi_nano_banana_2"
    provider = PresetProvider.APIYI
    base_url = "https://api.apiyi.com"
    model = "gemini-3.1-flash-image-preview"
    runtime = PresetRuntimeConfig(timeout_seconds=300.0, retry_count=0)
    notes = (
        "API易 Nano Banana 2 uses the Gemini generateContent compatible endpoint.",
        "This preset sends Authorization only and does not require Google-specific x-goog-api-key headers.",
        "Provider docs mention extra 512px output and four additional aspect ratios, but the current MCP shared contract still exposes 1K/2K/4K and the common 10 aspect ratios only.",
    )

    def send_nano_banana_request(
        self,
        request: NanoBananaExecutionRequest,
        prepared: NanoBananaPreparedRequest,
        api_key: str,
    ) -> dict[str, object]:
        """执行 send_nano_banana_request，用于 preset 契约定义 场景下的当前步骤处理。

        处理流程：
            - 步骤 1：按 API易 文档要求组装 generateContent 请求头
            - 步骤 2：只发送一次请求并返回已校验的 JSON 响应
        """

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        endpoint = f"{self.resolve().config.base_url.rstrip('/')}/v1beta/models/{self.resolve().config.model}:generateContent"
        response = httpx.post(
            endpoint,
            headers=headers,
            json=prepared.payload,
            timeout=self.resolve().config.runtime.timeout_seconds,
        )
        return self.handle_nano_banana_upstream_response(PresetModeSupport(request.mode.value), response)
