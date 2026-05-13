"""Shared image size contracts and normalization helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

SIZE_DELIMITER = "x"
SIZE_AUTO = "auto"
SUPPORTED_SIZE_ITEM_DELIMITER = ", "


class ImageSizeTier(StrEnum):
    """Named resolution tiers supported across providers."""

    SIZE_1K = "1K"
    SIZE_2K = "2K"
    SIZE_4K = "4K"


class ImageAspectRatio(StrEnum):
    """Aspect ratio keys shared across provider adapters."""

    SQUARE = "1:1"
    PORTRAIT_2_3 = "2:3"
    PHOTO_3_2 = "3:2"
    PORTRAIT_3_4 = "3:4"
    STANDARD_4_3 = "4:3"
    SOCIAL_4_5 = "4:5"
    LARGE_5_4 = "5:4"
    STORY_9_16 = "9:16"
    WIDE_16_9 = "16:9"
    CINEMA_21_9 = "21:9"


@dataclass(frozen=True)
class SupportedImageSize:
    """Canonical size preset with shared metadata."""

    tier: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    width: int
    height: int

    @property
    def value(self) -> str:
        return f"{self.width}{SIZE_DELIMITER}{self.height}"


SUPPORTED_IMAGE_SIZES: tuple[SupportedImageSize, ...] = (
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.SQUARE, 1280, 1280),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_2_3, 848, 1280),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PHOTO_3_2, 1280, 848),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_3_4, 960, 1280),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.STANDARD_4_3, 1280, 960),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.SOCIAL_4_5, 1024, 1280),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.LARGE_5_4, 1280, 1024),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.STORY_9_16, 720, 1280),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.WIDE_16_9, 1280, 720),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.CINEMA_21_9, 1280, 544),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.SQUARE, 2048, 2048),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_2_3, 1360, 2048),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PHOTO_3_2, 2048, 1360),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_3_4, 1536, 2048),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.STANDARD_4_3, 2048, 1536),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.SOCIAL_4_5, 1632, 2048),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.LARGE_5_4, 2048, 1632),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.STORY_9_16, 1152, 2048),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9, 2048, 1152),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.CINEMA_21_9, 2048, 864),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.SQUARE, 2880, 2880),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_2_3, 2336, 3520),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PHOTO_3_2, 3520, 2336),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_3_4, 2480, 3312),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.STANDARD_4_3, 3312, 2480),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.SOCIAL_4_5, 2560, 3216),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.LARGE_5_4, 3216, 2560),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.STORY_9_16, 2160, 3840),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.WIDE_16_9, 3840, 2160),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.CINEMA_21_9, 3840, 1632),
)

SUPPORTED_IMAGE_SIZE_MAP: dict[str, SupportedImageSize] = {preset.value: preset for preset in SUPPORTED_IMAGE_SIZES}


def supported_image_sizes_for_tier(tier: ImageSizeTier) -> tuple[SupportedImageSize, ...]:
    """Return the canonical presets for one named resolution tier."""

    return tuple(preset for preset in SUPPORTED_IMAGE_SIZES if preset.tier is tier)


def supported_size_values(sizes: tuple[SupportedImageSize, ...]) -> tuple[str, ...]:
    """Return sorted `<width>x<height>` values for human-readable validation messages."""

    return tuple(sorted(preset.value for preset in sizes))


def format_supported_image_sizes(sizes: tuple[SupportedImageSize, ...]) -> str:
    """Format presets with their tier and aspect ratio so callers can pick the right value."""

    formatted_items: list[str] = [f"{preset.value} ({preset.tier.value}, {preset.aspect_ratio.value})" for preset in sorted(sizes, key=_sort_key)]
    return SUPPORTED_SIZE_ITEM_DELIMITER.join(formatted_items)


def supported_image_size_error_message(reason: str, sizes: tuple[SupportedImageSize, ...] = SUPPORTED_IMAGE_SIZES) -> str:
    """Build a size validation error that always includes discoverable supported presets."""

    return f"{reason}. Supported size presets: {format_supported_image_sizes(sizes)}"


def _sort_key(preset: SupportedImageSize) -> tuple[int, int, int]:
    return (preset.width * preset.height, preset.width, preset.height)


def parse_requested_size(size: str) -> tuple[int, int]:
    """Parse a `<width>x<height>` size string into positive integers."""

    parts: list[str] = size.split(SIZE_DELIMITER)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(supported_image_size_error_message("size must use the format <width>x<height>"))

    width: int = int(parts[0])
    height: int = int(parts[1])
    if width <= 0 or height <= 0:
        raise ValueError(supported_image_size_error_message("width and height must be positive integers"))
    return width, height


def normalize_supported_size(size: str) -> str:
    """Normalize arbitrary positive sizes to the nearest supported preset."""

    if size == SIZE_AUTO:
        return size
    return resolve_supported_size(size).value


def resolve_supported_size(size: str) -> SupportedImageSize:
    """Resolve any explicit size into its canonical supported preset."""

    preset = SUPPORTED_IMAGE_SIZE_MAP.get(size)
    if preset is not None:
        return preset

    width, height = parse_requested_size(size)
    return closest_supported_size(width, height)


def closest_supported_size(width: int, height: int) -> SupportedImageSize:
    """Choose the nearest preset using aspect ratio first, then scale."""

    requested_ratio: float = width / height
    requested_area: int = width * height
    return min(
        SUPPORTED_IMAGE_SIZES,
        key=lambda preset: (
            abs(math.log(requested_ratio / (preset.width / preset.height))),
            abs(math.log(requested_area / (preset.width * preset.height))),
            abs(width - preset.width) + abs(height - preset.height),
        ),
    )
