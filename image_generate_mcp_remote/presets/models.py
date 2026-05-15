"""models 模块用于preset 契约定义，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..contracts.enums import ImageBackground, ImageCount, ImageModeration, ImageOutputFormat, ImageQuality, ImageResponseModality, ImageThinkingLevel
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier, SupportedImageSize, SupportedImageSizes
from ..contracts.presets import (
    ImageToolPresetConfig,
    PresetFieldDispatchMode,
    PresetRuntimeConfig,
    PresetModeSupport,
    UnsupportedSizePreset,
)
from ..contracts.requests import EditImageRequestBase, GenerateImageRequestBase
from ..models.common import InputImage, ResolvedInputImage


class PresetConfigOverrides(BaseModel):
    """PresetConfigOverrides 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    base_url: str | None = None
    model: str | None = None
    runtime: PresetRuntimeConfig | None = None
    dispatch_updates: dict[str, PresetFieldDispatchMode] | None = None
    unsupported_sizes: list[UnsupportedSizePreset] | None = None
    notes: list[str] | None = None


class ResolvedImageToolPreset(BaseModel):
    """ResolvedImageToolPreset 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    config: ImageToolPresetConfig
    preset_class: str

    @property
    def supported_sizes(self) -> tuple[SupportedImageSize, ...]:
        unsupported_keys = {
            (item.image_size, item.aspect_ratio)
            for item in self.config.unsupported_sizes
        }
        return tuple(
            item
            for item in SupportedImageSizes.all()
            if (item.tier, item.aspect_ratio) not in unsupported_keys
        )

    @property
    def unsupported_size_keys(self) -> frozenset[tuple[ImageSizeTier, ImageAspectRatio]]:
        return frozenset((item.image_size, item.aspect_ratio) for item in self.config.unsupported_sizes)

    def requires_prompt_fallback(self, field_name: str) -> bool:
        return getattr(self.config.dispatch, field_name) is PresetFieldDispatchMode.PROMPT_FALLBACK

    def sends_field(self, field_name: str) -> bool:
        return getattr(self.config.dispatch, field_name) is PresetFieldDispatchMode.SEND


class GptImage2GenerateExecutionRequest(GenerateImageRequestBase):
    """GptImage2GenerateExecutionRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    quality: ImageQuality = ImageQuality.AUTO
    output_format: ImageOutputFormat = ImageOutputFormat.PNG
    output_compression: int | None = None
    background: ImageBackground = ImageBackground.AUTO
    moderation: ImageModeration = ImageModeration.AUTO
    n: ImageCount = ImageCount.SINGLE


class GptImage2EditExecutionRequest(EditImageRequestBase):
    """GptImage2EditExecutionRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    images: list[InputImage]
    mask: InputImage | None = None
    quality: ImageQuality = ImageQuality.AUTO
    output_format: ImageOutputFormat = ImageOutputFormat.PNG
    output_compression: int | None = None
    background: ImageBackground = ImageBackground.AUTO


GptImage2ExecutionRequest = GptImage2GenerateExecutionRequest | GptImage2EditExecutionRequest


class NanoBananaGenerateExecutionRequest(GenerateImageRequestBase):
    """NanoBananaGenerateExecutionRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    response_modalities: list[ImageResponseModality] = Field(default_factory=lambda: [ImageResponseModality.IMAGE])
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    thinking_level: ImageThinkingLevel = ImageThinkingLevel.MINIMAL
    include_thoughts: bool = False
    input_images: list[InputImage] = Field(default_factory=list)


class NanoBananaEditExecutionRequest(EditImageRequestBase):
    """NanoBananaEditExecutionRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    input_images: list[InputImage]
    response_modalities: list[ImageResponseModality] = Field(default_factory=lambda: [ImageResponseModality.IMAGE])
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    thinking_level: ImageThinkingLevel = ImageThinkingLevel.MINIMAL
    include_thoughts: bool = False


NanoBananaExecutionRequest = NanoBananaGenerateExecutionRequest | NanoBananaEditExecutionRequest


class LegacyGptImage2ExecutionRequest(BaseModel):
    """LegacyGptImage2ExecutionRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    version: str
    mode: PresetModeSupport
    prompt: str
    save_path: str
    aspect_ratio: ImageAspectRatio
    image_size: ImageSizeTier
    images: list[InputImage] = Field(default_factory=list)
    mask: InputImage | None = None


class GptImage2PreparedRequest(BaseModel):
    """GptImage2PreparedRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    payload: dict[str, str | int]
    files: list[tuple[str, tuple[str, bytes, str]]] = Field(default_factory=list)


class NanoBananaPreparedRequest(BaseModel):
    """NanoBananaPreparedRequest 是 preset 契约定义 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    payload: dict[str, object]
    inline_images: list[ResolvedInputImage] = Field(default_factory=list)
