"""Structured contracts for startup-selected image tool presets."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .image_size import ImageAspectRatio, ImageSizeTier


class PresetToolName(StrEnum):
    """Formal tools that can bind to a startup preset."""

    GPT_IMAGE_2_OFFICIAL = "gpt_image_2_official"
    NANO_BANANA_2_OFFICIAL = "nano_banana_2_official"


class PresetProvider(StrEnum):
    """Known upstream provider identities for preset catalog guidance."""

    OPENAI = "openai"
    GOOGLE = "google"
    RIGHT_CODES = "right_codes"
    APIYI = "apiyi"
    LAOZHANG = "laozhang"
    COPPERAI = "copperai"
    CUSTOM = "custom"


class PresetProtocol(StrEnum):
    """Upstream request protocol families used by image presets."""

    OPENAI_IMAGES = "openai_images"
    GEMINI_GENERATE_CONTENT = "gemini_generate_content"


class PresetRequestField(StrEnum):
    """Provider-owned fields whose upstream dispatch varies by preset."""

    SIZE = "size"
    QUALITY = "quality"
    OUTPUT_FORMAT = "output_format"
    BACKGROUND = "background"
    MODERATION = "moderation"


class PresetModeSupport(StrEnum):
    """Modes a preset allows for its bound tool."""

    GENERATE = "generate"
    EDIT = "edit"


class PresetFieldDispatchMode(StrEnum):
    """How a stable MCP parameter is handled for the upstream request."""

    SEND = "send"
    PROMPT_FALLBACK = "prompt_fallback"
    DROP = "drop"


class PresetStability(StrEnum):
    """Whether a preset is production-ready or documented as experimental."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"


class ToolKind(StrEnum):
    """Catalog-visible tool implementation kind."""

    PRESET = "preset"
    TEMPORARY = "temporary"
    COMPATIBILITY = "compatibility"


class PresetRuntimeConfig(BaseModel):
    """Runtime limits owned by a preset for one service process."""

    timeout_seconds: float
    retry_count: int


class PresetDispatchPolicy(BaseModel):
    """Upstream dispatch policy for provider-owned request fields."""

    size: PresetFieldDispatchMode
    quality: PresetFieldDispatchMode
    output_format: PresetFieldDispatchMode
    background: PresetFieldDispatchMode
    moderation: PresetFieldDispatchMode


class UnsupportedSizePreset(BaseModel):
    """One shared image-size pair disabled by a concrete preset."""

    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio


class ImageToolPresetConfig(BaseModel):
    """Effective class-declared config for one image tool preset."""

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
    """Catalog guidance for one callable parameter under the active preset."""

    accepted_by_mcp: bool
    allowed_by_preset: bool
    guidance: str
    upstream_behavior: PresetFieldDispatchMode | None = None
    locked_value: str | None = None
    allowed_values: list[str] | None = None
    must_pair_with: str | None = None


class SizePresetCatalogItem(BaseModel):
    """Catalog-friendly representation of one shared size pair."""

    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    gpt_size: str
    nano_banana_size: str


class PresetExecutionContext(BaseModel):
    """Normalized arguments passed from a formal tool into its preset."""

    prompt: str
    mode: PresetModeSupport
    quality: str | None
    image_size: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    save_path: str
    request_id: str
    tool_name: PresetToolName


class PresetExecutionResult(BaseModel):
    """Provider response normalized by preset execution."""

    image_urls: list[str]
    image_base64_items: list[str]
    warnings: list[str]
