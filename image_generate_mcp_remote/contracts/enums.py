"""Shared enum definitions for image tool contracts."""

from __future__ import annotations

from enum import IntEnum, StrEnum


class ImageQuality(StrEnum):
    """Shared quality levels for OpenAI-compatible image tools."""

    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImageOutputFormat(StrEnum):
    """Shared output formats for downloaded or provider-returned images."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class ImageBackground(StrEnum):
    """Shared background options for image generation."""

    AUTO = "auto"
    OPAQUE = "opaque"


class ImageModeration(StrEnum):
    """Shared moderation options for compatible providers."""

    AUTO = "auto"
    LOW = "low"


class ImageCount(IntEnum):
    """Shared image count enum for single-image tools."""

    SINGLE = 1


class ImageResponseModality(StrEnum):
    """Shared output modalities used by multimodal providers."""

    TEXT = "TEXT"
    IMAGE = "IMAGE"


class ImageThinkingLevel(StrEnum):
    """Shared provider thinking levels where supported."""

    MINIMAL = "minimal"
    HIGH = "High"
