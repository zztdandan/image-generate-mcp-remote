"""image_size 模块用于尺寸档位与比例映射，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

SIZE_DELIMITER = "x"
SUPPORTED_SIZE_ITEM_DELIMITER = ", "


class ImageSizeTier(StrEnum):
    """ImageSizeTier 是 尺寸档位与比例映射 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    SIZE_1K = "1K"
    SIZE_2K = "2K"
    SIZE_4K = "4K"


class ImageAspectRatio(StrEnum):
    """ImageAspectRatio 是 尺寸档位与比例映射 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

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
    """ImageSizeProvider 是 尺寸档位与比例映射 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    GPT = "gpt"
    NANO_BANANA = "nano_banana"


@dataclass(frozen=True)
class ProviderImageSize:
    """ProviderImageSize 是 尺寸档位与比例映射 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    width: int
    height: int

    @property
    def value(self) -> str:
        return f"{self.width}{SIZE_DELIMITER}{self.height}"


@dataclass(frozen=True)
class ImageSizeKey:
    """ImageSizeKey 是 尺寸档位与比例映射 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    tier: ImageSizeTier
    aspect_ratio: ImageAspectRatio


@dataclass(frozen=True)
class SupportedImageSize:
    """SupportedImageSize 是 尺寸档位与比例映射 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    key: ImageSizeKey
    gpt_size: ProviderImageSize
    nano_banana_size: ProviderImageSize

    @property
    def tier(self) -> ImageSizeTier:
        return self.key.tier

    @property
    def aspect_ratio(self) -> ImageAspectRatio:
        return self.key.aspect_ratio

    @property
    def gpt_value(self) -> str:
        return self.gpt_size.value

    @property
    def nano_banana_value(self) -> str:
        return self.nano_banana_size.value

    @property
    def value(self) -> str:
        return self.gpt_value

    def size_for_provider(self, provider: ImageSizeProvider) -> ProviderImageSize:
        if provider is ImageSizeProvider.NANO_BANANA:
            return self.nano_banana_size
        return self.gpt_size


class SupportedImageSizes:
    """SupportedImageSizes 是 尺寸档位与比例映射 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    _BY_KEY: dict[ImageSizeKey, SupportedImageSize] = {
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.SQUARE): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.SQUARE),
            ProviderImageSize(1280, 1280),
            ProviderImageSize(1024, 1024),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_2_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_2_3),
            ProviderImageSize(848, 1280),
            ProviderImageSize(848, 1264),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PHOTO_3_2): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PHOTO_3_2),
            ProviderImageSize(1280, 848),
            ProviderImageSize(1264, 848),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_3_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.PORTRAIT_3_4),
            ProviderImageSize(960, 1280),
            ProviderImageSize(896, 1200),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.STANDARD_4_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.STANDARD_4_3),
            ProviderImageSize(1280, 960),
            ProviderImageSize(1200, 896),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.SOCIAL_4_5): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.SOCIAL_4_5),
            ProviderImageSize(1024, 1280),
            ProviderImageSize(928, 1152),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.LARGE_5_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.LARGE_5_4),
            ProviderImageSize(1280, 1024),
            ProviderImageSize(1152, 928),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.STORY_9_16): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.STORY_9_16),
            ProviderImageSize(720, 1280),
            ProviderImageSize(768, 1376),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.WIDE_16_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.WIDE_16_9),
            ProviderImageSize(1280, 720),
            ProviderImageSize(1376, 768),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.CINEMA_21_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_1K, ImageAspectRatio.CINEMA_21_9),
            ProviderImageSize(1280, 544),
            ProviderImageSize(1584, 672),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.SQUARE): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.SQUARE),
            ProviderImageSize(2048, 2048),
            ProviderImageSize(2048, 2048),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_2_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_2_3),
            ProviderImageSize(1360, 2048),
            ProviderImageSize(1696, 2528),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PHOTO_3_2): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PHOTO_3_2),
            ProviderImageSize(2048, 1360),
            ProviderImageSize(2528, 1696),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_3_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.PORTRAIT_3_4),
            ProviderImageSize(1536, 2048),
            ProviderImageSize(1792, 2400),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.STANDARD_4_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.STANDARD_4_3),
            ProviderImageSize(2048, 1536),
            ProviderImageSize(2400, 1792),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.SOCIAL_4_5): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.SOCIAL_4_5),
            ProviderImageSize(1632, 2048),
            ProviderImageSize(1856, 2304),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.LARGE_5_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.LARGE_5_4),
            ProviderImageSize(2048, 1632),
            ProviderImageSize(2304, 1856),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.STORY_9_16): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.STORY_9_16),
            ProviderImageSize(1152, 2048),
            ProviderImageSize(1536, 2752),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.WIDE_16_9),
            ProviderImageSize(2048, 1152),
            ProviderImageSize(2752, 1536),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.CINEMA_21_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_2K, ImageAspectRatio.CINEMA_21_9),
            ProviderImageSize(2048, 864),
            ProviderImageSize(3168, 1344),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.SQUARE): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.SQUARE),
            ProviderImageSize(2880, 2880),
            ProviderImageSize(4096, 4096),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_2_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_2_3),
            ProviderImageSize(2336, 3520),
            ProviderImageSize(3392, 5056),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PHOTO_3_2): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PHOTO_3_2),
            ProviderImageSize(3520, 2336),
            ProviderImageSize(5056, 3392),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_3_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.PORTRAIT_3_4),
            ProviderImageSize(2480, 3312),
            ProviderImageSize(3584, 4800),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.STANDARD_4_3): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.STANDARD_4_3),
            ProviderImageSize(3312, 2480),
            ProviderImageSize(4800, 3584),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.SOCIAL_4_5): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.SOCIAL_4_5),
            ProviderImageSize(2560, 3216),
            ProviderImageSize(3712, 4608),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.LARGE_5_4): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.LARGE_5_4),
            ProviderImageSize(3216, 2560),
            ProviderImageSize(4608, 3712),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.STORY_9_16): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.STORY_9_16),
            ProviderImageSize(2160, 3840),
            ProviderImageSize(3072, 5504),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.WIDE_16_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.WIDE_16_9),
            ProviderImageSize(3840, 2160),
            ProviderImageSize(5504, 3072),
        ),
        ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.CINEMA_21_9): SupportedImageSize(
            ImageSizeKey(ImageSizeTier.SIZE_4K, ImageAspectRatio.CINEMA_21_9),
            ProviderImageSize(3840, 1632),
            ProviderImageSize(6336, 2688),
        ),
    }
    _BY_PROVIDER_VALUE: dict[str, SupportedImageSize] = {
        size_value: preset
        for preset in _BY_KEY.values()
        for size_value in (preset.gpt_value, preset.nano_banana_value)
    }

    @classmethod
    def all(cls) -> tuple[SupportedImageSize, ...]:
        return tuple(cls._BY_KEY.values())

    @classmethod
    def resolve(cls, image_size: ImageSizeTier, aspect_ratio: ImageAspectRatio) -> SupportedImageSize:
        return cls._BY_KEY[ImageSizeKey(image_size, aspect_ratio)]

    @classmethod
    def for_tier(cls, image_size: ImageSizeTier) -> tuple[SupportedImageSize, ...]:
        return tuple(spec for spec in cls._BY_KEY.values() if spec.tier is image_size)

    @classmethod
    def from_provider_size_value(cls, size_value: str) -> SupportedImageSize | None:
        return cls._BY_PROVIDER_VALUE.get(size_value)

    @classmethod
    def closest_for_provider(cls, width: int, height: int, provider: ImageSizeProvider) -> SupportedImageSize:
        requested_ratio: float = width / height
        requested_area: int = width * height
        return min(
            cls._BY_KEY.values(),
            key=lambda preset: (
                abs(math.log(requested_ratio / (preset.size_for_provider(provider).width / preset.size_for_provider(provider).height))),
                abs(math.log(requested_area / (preset.size_for_provider(provider).width * preset.size_for_provider(provider).height))),
                abs(width - preset.size_for_provider(provider).width)
                + abs(height - preset.size_for_provider(provider).height),
            ),
        )


SUPPORTED_IMAGE_SIZES = SupportedImageSizes


def supported_image_sizes_for_tier(tier: ImageSizeTier) -> tuple[SupportedImageSize, ...]:
    """执行 supported_image_sizes_for_tier，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return SupportedImageSizes.for_tier(tier)


def supported_size_values(
    sizes: tuple[SupportedImageSize, ...],
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
) -> tuple[str, ...]:
    """执行 supported_size_values，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return tuple(sorted(preset.size_for_provider(provider).value for preset in sizes))


def format_supported_image_sizes(
    sizes: tuple[SupportedImageSize, ...],
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
    include_nano_banana_companion: bool = False,
) -> str:
    """执行 format_supported_image_sizes，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    formatted_items: list[str] = []
    for preset in sorted(sizes, key=lambda item: _sort_key(item, provider)):
        provider_value = preset.size_for_provider(provider).value
        detail_items: list[str] = [f"gpt={preset.gpt_value}"]
        if include_nano_banana_companion:
            detail_items.append(f"nano={preset.nano_banana_value}")
        elif provider is ImageSizeProvider.NANO_BANANA:
            detail_items = [f"nano={provider_value}"]
        formatted_items.append(
            f"{preset.tier.value} + {preset.aspect_ratio.value} ({', '.join(detail_items)})"
        )
    return SUPPORTED_SIZE_ITEM_DELIMITER.join(formatted_items)


def supported_image_size_error_message(
    reason: str,
    sizes: tuple[SupportedImageSize, ...] | None = None,
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
    include_nano_banana_companion: bool = False,
) -> str:
    """执行 supported_image_size_error_message，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    effective_sizes: tuple[SupportedImageSize, ...] = sizes or SupportedImageSizes.all()
    return (
        f"{reason}. Supported size presets: "
        f"{format_supported_image_sizes(effective_sizes, provider=provider, include_nano_banana_companion=include_nano_banana_companion)}"
    )


def _sort_key(preset: SupportedImageSize, provider: ImageSizeProvider) -> tuple[int, int, int]:
    provider_size = preset.size_for_provider(provider)
    return (provider_size.width * provider_size.height, provider_size.width, provider_size.height)


def parse_requested_size(size: str) -> tuple[int, int]:
    """执行 parse_requested_size，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析输入并转换为内部可用结构
        - 步骤 2：校验格式后输出标准化结果
    """

    parts: list[str] = size.split(SIZE_DELIMITER)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(supported_image_size_error_message("size must use the format <width>x<height>"))

    width: int = int(parts[0])
    height: int = int(parts[1])
    if width <= 0 or height <= 0:
        raise ValueError(supported_image_size_error_message("width and height must be positive integers"))
    return width, height


def provider_size_value(
    image_size: ImageSizeTier,
    aspect_ratio: ImageAspectRatio,
    provider: ImageSizeProvider = ImageSizeProvider.GPT,
) -> str:
    """执行 provider_size_value，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return SupportedImageSizes.resolve(image_size, aspect_ratio).size_for_provider(provider).value


def resolve_supported_size_selection(image_size: ImageSizeTier, aspect_ratio: ImageAspectRatio) -> SupportedImageSize:
    """执行 resolve_supported_size_selection，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析并确定最终生效配置
        - 步骤 2：合并输入来源后输出可执行结果
    """

    return SupportedImageSizes.resolve(image_size, aspect_ratio)


def resolve_supported_size(size: str, provider: ImageSizeProvider = ImageSizeProvider.GPT) -> SupportedImageSize:
    """执行 resolve_supported_size，用于 尺寸档位与比例映射 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析并确定最终生效配置
        - 步骤 2：合并输入来源后输出可执行结果
    """

    preset = SupportedImageSizes.from_provider_size_value(size)
    if preset is not None:
        return preset

    width, height = parse_requested_size(size)
    return SupportedImageSizes.closest_for_provider(width, height, provider)
