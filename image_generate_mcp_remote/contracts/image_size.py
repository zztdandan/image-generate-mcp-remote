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


class ImageSizeProvider(StrEnum):
    """Provider-specific size matrix selectors."""

    GPT = "gpt"
    NANO_BANANA = "nano_banana"


@dataclass(frozen=True)
class ProviderImageSize:
    """One concrete pixel size used by a specific provider."""

    width: int
    height: int

    @property
    def value(self) -> str:
        return f"{self.width}{SIZE_DELIMITER}{self.height}"


@dataclass(frozen=True)
class SupportedImageSize:
    """Shared size preset with provider-specific concrete pixel sizes."""

    tier: ImageSizeTier
    aspect_ratio: ImageAspectRatio
    gpt_size: ProviderImageSize
    nano_banana_size: ProviderImageSize

    @property
    def width(self) -> int:
        return self.gpt_size.width

    @property
    def height(self) -> int:
        return self.gpt_size.height

    @property
    def value(self) -> str:
        return self.gpt_size.value

    @property
    def gpt_value(self) -> str:
        return self.gpt_size.value

    @property
    def nano_banana_value(self) -> str:
        return self.nano_banana_size.value

    def size_for_provider(self, provider: ImageSizeProvider) -> ProviderImageSize:
        if provider is ImageSizeProvider.NANO_BANANA:
            return self.nano_banana_size
        return self.gpt_size


SUPPORTED_IMAGE_SIZES: tuple[SupportedImageSize, ...] = (
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.SQUARE, ProviderImageSize(1280, 1280), ProviderImageSize(1024, 1024)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_2_3, ProviderImageSize(848, 1280), ProviderImageSize(848, 1264)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PHOTO_3_2, ProviderImageSize(1280, 848), ProviderImageSize(1264, 848)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_3_4, ProviderImageSize(960, 1280), ProviderImageSize(896, 1200)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.STANDARD_4_3, ProviderImageSize(1280, 960), ProviderImageSize(1200, 896)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.SOCIAL_4_5, ProviderImageSize(1024, 1280), ProviderImageSize(928, 1152)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.LARGE_5_4, ProviderImageSize(1280, 1024), ProviderImageSize(1152, 928)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.STORY_9_16, ProviderImageSize(720, 1280), ProviderImageSize(768, 1376)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.WIDE_16_9, ProviderImageSize(1280, 720), ProviderImageSize(1376, 768)),
    SupportedImageSize(ImageSizeTier.SIZE_1K, ImageAspectRatio.CINEMA_21_9, ProviderImageSize(1280, 544), ProviderImageSize(1584, 672)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.SQUARE, ProviderImageSize(2048, 2048), ProviderImageSize(2048, 2048)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_2_3, ProviderImageSize(1360, 2048), ProviderImageSize(1696, 2528)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PHOTO_3_2, ProviderImageSize(2048, 1360), ProviderImageSize(2528, 1696)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_3_4, ProviderImageSize(1536, 2048), ProviderImageSize(1792, 2400)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.STANDARD_4_3, ProviderImageSize(2048, 1536), ProviderImageSize(2400, 1792)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.SOCIAL_4_5, ProviderImageSize(1632, 2048), ProviderImageSize(1856, 2304)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.LARGE_5_4, ProviderImageSize(2048, 1632), ProviderImageSize(2304, 1856)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.STORY_9_16, ProviderImageSize(1152, 2048), ProviderImageSize(1536, 2752)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9, ProviderImageSize(2048, 1152), ProviderImageSize(2752, 1536)),
    SupportedImageSize(ImageSizeTier.SIZE_2K, ImageAspectRatio.CINEMA_21_9, ProviderImageSize(2048, 864), ProviderImageSize(3168, 1344)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.SQUARE, ProviderImageSize(2880, 2880), ProviderImageSize(4096, 4096)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_2_3, ProviderImageSize(2336, 3520), ProviderImageSize(3392, 5056)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PHOTO_3_2, ProviderImageSize(3520, 2336), ProviderImageSize(5056, 3392)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_3_4, ProviderImageSize(2480, 3312), ProviderImageSize(3584, 4800)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.STANDARD_4_3, ProviderImageSize(3312, 2480), ProviderImageSize(4800, 3584)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.SOCIAL_4_5, ProviderImageSize(2560, 3216), ProviderImageSize(3712, 4608)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.LARGE_5_4, ProviderImageSize(3216, 2560), ProviderImageSize(4608, 3712)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.STORY_9_16, ProviderImageSize(2160, 3840), ProviderImageSize(3072, 5504)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.WIDE_16_9, ProviderImageSize(3840, 2160), ProviderImageSize(5504, 3072)),
    SupportedImageSize(ImageSizeTier.SIZE_4K, ImageAspectRatio.CINEMA_21_9, ProviderImageSize(3840, 1632), ProviderImageSize(6336, 2688)),
)

SUPPORTED_IMAGE_SIZE_MAP: dict[str, SupportedImageSize] = {
    size_value: preset
    for preset in SUPPORTED_IMAGE_SIZES
    for size_value in (preset.gpt_value, preset.nano_banana_value)
}


def supported_image_sizes_for_tier(tier: ImageSizeTier) -> tuple[SupportedImageSize, ...]:
    """Return the canonical presets for one named resolution tier."""

    return tuple(preset for preset in SUPPORTED_IMAGE_SIZES if preset.tier is tier)


def supported_size_values(sizes: tuple[SupportedImageSize, ...], provider: ImageSizeProvider = ImageSizeProvider.GPT) -> tuple[str, ...]:
    """Return sorted `<width>x<height>` values for human-readable validation messages."""

    return tuple(sorted(preset.size_for_provider(provider).value for preset in sizes))


def format_supported_image_sizes(
    sizes: tuple[SupportedImageSize, ...],
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
    include_nano_banana_companion: bool = False,
) -> str:
    """Format presets with their tier and aspect ratio so callers can pick the right value."""

    formatted_items: list[str] = []
    for preset in sorted(sizes, key=lambda item: _sort_key(item, provider)):
        provider_value = preset.size_for_provider(provider).value
        companion_text = ""
        if include_nano_banana_companion:
            companion_text = f", nano={preset.nano_banana_value}"
        formatted_items.append(f"{provider_value} ({preset.tier.value}, {preset.aspect_ratio.value}{companion_text})")
    return SUPPORTED_SIZE_ITEM_DELIMITER.join(formatted_items)


def supported_image_size_error_message(
    reason: str,
    sizes: tuple[SupportedImageSize, ...] = SUPPORTED_IMAGE_SIZES,
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
    include_nano_banana_companion: bool = False,
) -> str:
    """Build a size validation error that always includes discoverable supported presets."""

    return (
        f"{reason}. Supported size presets: "
        f"{format_supported_image_sizes(sizes, provider=provider, include_nano_banana_companion=include_nano_banana_companion)}"
    )


def _sort_key(preset: SupportedImageSize, provider: ImageSizeProvider) -> tuple[int, int, int]:
    provider_size = preset.size_for_provider(provider)
    return (provider_size.width * provider_size.height, provider_size.width, provider_size.height)


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


def normalize_supported_size(size: str, provider: ImageSizeProvider = ImageSizeProvider.GPT) -> str:
    """Normalize arbitrary positive sizes to the nearest supported preset."""

    if size == SIZE_AUTO:
        return size
    return resolve_supported_size(size, provider=provider).size_for_provider(provider).value


def resolve_supported_size(size: str, provider: ImageSizeProvider = ImageSizeProvider.GPT) -> SupportedImageSize:
    """Resolve any explicit size into its canonical supported preset."""

    preset = SUPPORTED_IMAGE_SIZE_MAP.get(size)
    if preset is not None:
        return preset

    width, height = parse_requested_size(size)
    return closest_supported_size(width, height, provider=provider)


def closest_supported_size(width: int, height: int, provider: ImageSizeProvider = ImageSizeProvider.GPT) -> SupportedImageSize:
    """Choose the nearest preset using aspect ratio first, then scale."""

    requested_ratio: float = width / height
    requested_area: int = width * height
    return min(
        SUPPORTED_IMAGE_SIZES,
        key=lambda preset: (
            abs(math.log(requested_ratio / (preset.size_for_provider(provider).width / preset.size_for_provider(provider).height))),
            abs(math.log(requested_area / (preset.size_for_provider(provider).width * preset.size_for_provider(provider).height))),
            abs(width - preset.size_for_provider(provider).width) + abs(height - preset.size_for_provider(provider).height),
        ),
    )
