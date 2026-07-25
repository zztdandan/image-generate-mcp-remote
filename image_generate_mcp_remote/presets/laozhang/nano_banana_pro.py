"""nano_banana_pro 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import httpx

from ...contracts.presets import PresetModeSupport, PresetProvider, PresetRuntimeConfig
from ..base import BaseNanoBananaPreset
from ..models import NanoBananaExecutionRequest, NanoBananaPreparedRequest


class LaoZhangNanoBananaProPreset(BaseNanoBananaPreset):
    """LaoZhangNanoBananaProPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。

    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id = "laozhang_nano_banana_pro"
    provider = PresetProvider.LAOZHANG
    base_url = "https://api.laozhang.ai"
    model = "gemini-3-pro-image-preview"
    runtime = PresetRuntimeConfig(timeout_seconds=300.0, retry_count=0)
    notes = (
        "LaoZhang Nano Banana Pro maps to gemini-3-pro-image-preview over the Gemini generateContent endpoint.",
        "Archived provider docs show this route uses Authorization only and does not require x-goog-api-key headers.",
        "The current shared MCP contract already matches the documented 1K/2K/4K tiers and common 10 aspect ratios, so no size remapping override is needed.",
        "Response parsing, image recovery, and save flow reuse the shared BaseNanoBananaPreset logic because the provider returns inline base64 image data in Gemini candidates[].content.parts[].inlineData.",
    )

    def send_nano_banana_request(
        self,
        request: NanoBananaExecutionRequest,
        prepared: NanoBananaPreparedRequest,
        api_key: str,
    ) -> dict[str, object]:
        """执行 send_nano_banana_request，用于 preset 契约定义 场景下的当前步骤处理。

        处理流程：
            - 步骤 1：按老张 Gemini 兼容文档组装 generateContent 请求头
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
