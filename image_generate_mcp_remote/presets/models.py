"""Preset runtime models and merge helpers."""

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
    """Optional override values supplied by concrete preset classes."""

    base_url: str | None = None
    model: str | None = None
    runtime: PresetRuntimeConfig | None = None
    dispatch_updates: dict[str, PresetFieldDispatchMode] | None = None
    unsupported_sizes: list[UnsupportedSizePreset] | None = None
    notes: list[str] | None = None


class ResolvedImageToolPreset(BaseModel):
    """Effective preset configuration after all class defaults are merged."""

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
    """Validated GPT Image 2 generate request passed into the active preset."""

    quality: ImageQuality = ImageQuality.AUTO
    output_format: ImageOutputFormat = ImageOutputFormat.PNG
    output_compression: int | None = None
    background: ImageBackground = ImageBackground.AUTO
    moderation: ImageModeration = ImageModeration.AUTO
    n: ImageCount = ImageCount.SINGLE


class GptImage2EditExecutionRequest(EditImageRequestBase):
    """Validated GPT Image 2 edit request passed into the active preset."""

    images: list[InputImage]
    mask: InputImage | None = None
    quality: ImageQuality = ImageQuality.AUTO
    output_format: ImageOutputFormat = ImageOutputFormat.PNG
    output_compression: int | None = None
    background: ImageBackground = ImageBackground.AUTO


GptImage2ExecutionRequest = GptImage2GenerateExecutionRequest | GptImage2EditExecutionRequest


class NanoBananaGenerateExecutionRequest(GenerateImageRequestBase):
    """Validated Nano Banana generate request passed into the active preset."""

    response_modalities: list[ImageResponseModality] = Field(default_factory=lambda: [ImageResponseModality.IMAGE])
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    thinking_level: ImageThinkingLevel = ImageThinkingLevel.MINIMAL
    include_thoughts: bool = False
    input_images: list[InputImage] = Field(default_factory=list)


class NanoBananaEditExecutionRequest(EditImageRequestBase):
    """Validated Nano Banana edit request passed into the active preset."""

    input_images: list[InputImage]
    response_modalities: list[ImageResponseModality] = Field(default_factory=lambda: [ImageResponseModality.IMAGE])
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    thinking_level: ImageThinkingLevel = ImageThinkingLevel.MINIMAL
    include_thoughts: bool = False


NanoBananaExecutionRequest = NanoBananaGenerateExecutionRequest | NanoBananaEditExecutionRequest


class LegacyGptImage2ExecutionRequest(BaseModel):
    """Deprecated compatibility alias kept out of tool wrappers."""

    version: str
    mode: PresetModeSupport
    prompt: str
    save_path: str
    aspect_ratio: ImageAspectRatio
    image_size: ImageSizeTier
    images: list[InputImage] = Field(default_factory=list)
    mask: InputImage | None = None


class GptImage2PreparedRequest(BaseModel):
    """OpenAI Images payload prepared by the active preset."""

    payload: dict[str, str | int]
    files: list[tuple[str, tuple[str, bytes, str]]] = Field(default_factory=list)


class NanoBananaPreparedRequest(BaseModel):
    """Gemini generateContent payload prepared by the active preset."""

    payload: dict[str, object]
    inline_images: list[ResolvedInputImage] = Field(default_factory=list)
