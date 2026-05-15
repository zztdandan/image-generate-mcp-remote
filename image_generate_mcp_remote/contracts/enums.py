"""enums 模块用于跨工具枚举约束，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class ImageQuality(StrEnum):
    """ImageQuality 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImageOutputFormat(StrEnum):
    """ImageOutputFormat 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class ImageBackground(StrEnum):
    """ImageBackground 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    AUTO = "auto"
    OPAQUE = "opaque"


class ImageModeration(StrEnum):
    """ImageModeration 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    AUTO = "auto"
    LOW = "low"


class ImageCount(IntEnum):
    """ImageCount 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    SINGLE = 1


class ImageResponseModality(StrEnum):
    """ImageResponseModality 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    TEXT = "TEXT"
    IMAGE = "IMAGE"


class ImageThinkingLevel(StrEnum):
    """ImageThinkingLevel 是 跨工具枚举约束 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    MINIMAL = "minimal"
    HIGH = "High"
