from image_generate_mcp_remote.contracts.image_size import (
    ImageAspectRatio,
    ImageSizeKey,
    ImageSizeTier,
    ProviderImageSize,
    SupportedImageSize,
    SupportedImageSizes,
    resolve_supported_size_selection,
    resolve_supported_size,
    supported_image_sizes_for_tier,
)


def test_supported_image_size_exposes_gpt_and_nano_banana_values():
    preset = next(
        item
        for item in supported_image_sizes_for_tier(ImageSizeTier.SIZE_2K)
        if item.aspect_ratio is ImageAspectRatio.WIDE_16_9
    )

    assert preset.gpt_size == ProviderImageSize(2048, 1152)
    assert preset.nano_banana_size == ProviderImageSize(2752, 1536)
    assert preset.gpt_value == "2048x1152"
    assert preset.nano_banana_value == "2752x1536"


def test_resolve_supported_size_accepts_exact_nano_banana_size():
    preset: SupportedImageSize = resolve_supported_size("2752x1536")

    assert preset.tier is ImageSizeTier.SIZE_2K
    assert preset.aspect_ratio is ImageAspectRatio.WIDE_16_9


def test_supported_image_sizes_registry_resolves_enum_pair():
    preset = resolve_supported_size_selection(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9)

    assert preset == SupportedImageSizes.resolve(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9)
    assert preset.key == ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9)
