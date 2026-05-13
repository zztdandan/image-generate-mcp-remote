"""Backward-compatible re-export of shared size normalization helpers."""

from ..contracts.image_size import (  # noqa: F401
    SIZE_AUTO,
    ImageAspectRatio as SupportedImageAspectRatio,
    ImageSizeTier as SupportedImageSizeTier,
    SUPPORTED_IMAGE_SIZES,
    SUPPORTED_IMAGE_SIZE_MAP,
    SupportedImageSize,
    closest_supported_size,
    normalize_supported_size,
    parse_requested_size,
    resolve_supported_size,
)
