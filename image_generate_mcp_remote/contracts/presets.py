"""presets 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .image_size import ImageAspectRatio, ImageSizeTier


class PresetToolName(StrEnum):
    """PresetToolName 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    GPT_IMAGE_2_OFFICIAL = "gpt_image_2_official"
    NANO_BANANA_2_OFFICIAL = "nano_banana_2_official"


class PresetProvider(StrEnum):
    """PresetProvider 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    OPENAI = "openai"
    GOOGLE = "google"
    RIGHT_CODES = "right_codes"
    APIYI = "apiyi"
    LAOZHANG = "laozhang"
    COPPERAI = "copperai"
    CUSTOM = "custom"


class PresetProtocol(StrEnum):
    """PresetProtocol 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    OPENAI_IMAGES = "openai_images"
    GEMINI_GENERATE_CONTENT = "gemini_generate_content"


class PresetRequestField(StrEnum):
    """PresetRequestField 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    SIZE = "size"
    QUALITY = "quality"
    OUTPUT_FORMAT = "output_format"
    BACKGROUND = "background"
    MODERATION = "moderation"


class PresetModeSupport(StrEnum):
    """PresetModeSupport 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    GENERATE = "generate"
    EDIT = "edit"


class PresetFieldDispatchMode(StrEnum):
    """PresetFieldDispatchMode 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    SEND = "send"
    PROMPT_FALLBACK = "prompt_fallback"
    DROP = "drop"


class PresetStability(StrEnum):
    """PresetStability 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    STABLE = "stable"
    EXPERIMENTAL = "experimental"


class ToolKind(StrEnum):
    """ToolKind 是 preset 契约定义 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    PRESET = "preset"
    TEMPORARY = "temporary"
    COMPATIBILITY = "compatibility"


class PresetRuntimeConfig(BaseModel):
    """PresetRuntimeConfig 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    timeout_seconds: float
    retry_count: int


class PresetDispatchPolicy(BaseModel):
    """PresetDispatchPolicy 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    size: PresetFieldDispatchMode
    quality: PresetFieldDispatchMode
    output_format: PresetFieldDispatchMode
    background: PresetFieldDispatchMode
    moderation: PresetFieldDispatchMode


class UnsupportedSizePreset(BaseModel):
    """UnsupportedSizePreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio


class ImageToolPresetConfig(BaseModel):
    """ImageToolPresetConfig 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id: str
    tool_name: PresetToolName
    provider: PresetProvider
    protocol: PresetProtocol
    base_url: str
    model: str
    modes: list[PresetModeSupport]
    dispatch: PresetDispatchPolicy
    runtime: PresetRuntimeConfig
    unsupported_sizes: list[UnsupportedSizePreset]
    notes: list[str]
    stability: PresetStability = PresetStability.STABLE


class ParameterGuidance(BaseModel):
    """ParameterGuidance 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    accepted_by_mcp: bool
    allowed_by_preset: bool
    guidance: str
    upstream_behavior: PresetFieldDispatchMode | None = None
    locked_value: str | None = None
    allowed_values: list[str] | None = None
    must_pair_with: str | None = None


class SizePresetCatalogItem(BaseModel):
    """SizePresetCatalogItem 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    gpt_size: str
    nano_banana_size: str


class PresetExecutionContext(BaseModel):
    """PresetExecutionContext 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    prompt: str
    mode: PresetModeSupport
    quality: str | None
    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    save_path: str
    request_id: str
    tool_name: PresetToolName


class PresetExecutionResult(BaseModel):
    """PresetExecutionResult 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    image_urls: list[str]
    image_base64_items: list[str]
    warnings: list[str]
