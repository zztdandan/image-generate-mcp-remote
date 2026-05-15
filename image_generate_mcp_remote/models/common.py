"""common 模块用于跨工具通用数据模型，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field

from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..contracts.presets import (
    ParameterGuidance,
    PresetModeSupport,
    PresetProtocol,
    PresetProvider,
    PresetStability,
    PresetToolName,
    ToolKind,
)

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONMap: TypeAlias = dict[str, JSONValue]


class ToolVersion(StrEnum):
    """ToolVersion 是 跨工具通用数据模型 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    V1 = "v1"


class ImageToolMode(StrEnum):
    """ImageToolMode 是 跨工具通用数据模型 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    GENERATE = "generate"
    EDIT = "edit"


class ImageToolStatus(StrEnum):
    """ImageToolStatus 是 跨工具通用数据模型 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    OK = "ok"


class InputImageSourceType(StrEnum):
    """InputImageSourceType 是 跨工具通用数据模型 的枚举集合，作用范围为本模块对外与对内的有限取值。
    
    职责：
        - 统一该领域字段的允许值并约束调用方输入
        - 为请求组装与响应解析提供稳定语义锚点
    """

    PATH = "path"
    BASE64 = "base64"
    DATA_URL = "data_url"


class InputImageFromPath(BaseModel):
    """InputImageFromPath 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    source_type: Literal[InputImageSourceType.PATH] = InputImageSourceType.PATH
    path: str
    filename: str | None = None
    mime_type: str | None = None


class InputImageFromBase64(BaseModel):
    """InputImageFromBase64 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    source_type: Literal[InputImageSourceType.BASE64] = InputImageSourceType.BASE64
    data_base64: str
    filename: str
    mime_type: str


class InputImageFromDataUrl(BaseModel):
    """InputImageFromDataUrl 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    source_type: Literal[InputImageSourceType.DATA_URL] = InputImageSourceType.DATA_URL
    data_url: str
    filename: str | None = None


InputImage: TypeAlias = Annotated[
    InputImageFromPath | InputImageFromBase64 | InputImageFromDataUrl,
    Field(discriminator="source_type"),
]


class ResolvedInputImage(BaseModel):
    """ResolvedInputImage 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    mime_type: str
    filename: str
    data: bytes


class UsageInfo(BaseModel):
    """UsageInfo 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ActualSizeVerificationResult(BaseModel):
    """ActualSizeVerificationResult 是 实际尺寸核对结果 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 表达请求尺寸合同与实际返回尺寸之间的一致性结果
        - 仅返回核对事实，不把不一致强制升级为 warning 或 error
    """

    requested_image_size: ImageSizeTier
    requested_aspect_ratio: ImageAspectRatio
    expected_width: int
    expected_height: int
    actual_width: int
    actual_height: int
    is_consistent: bool


class ImageToolResult(BaseModel):
    """ImageToolResult 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    status: ImageToolStatus = Field(default=ImageToolStatus.OK)
    tool_name: str
    tool_version: ToolVersion
    mode: ImageToolMode
    provider_model: str
    file_path: str
    image_uri: str
    mime_type: str
    elapsed_seconds: float
    width: int | None = None
    height: int | None = None
    actual_size_verification: ActualSizeVerificationResult | None = None
    usage: UsageInfo | None = None
    provider_response_excerpt: dict[str, str] | None = None
    text_output: str | None = None


class ToolEnvValuesNonSecret(BaseModel):
    """ToolEnvValuesNonSecret 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    base_url: str
    base_url_source: str
    model: str
    model_source: str
    supported_models: list[str]
    supported_models_source: str
    output_dir: str
    request_timeout_seconds: float
    request_timeout_source: str
    retry_count: int
    retry_count_source: str


class ToolCatalogEntry(BaseModel):
    """ToolCatalogEntry 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    tool_name: str
    tool_version: ToolVersion
    title: str
    tool_kind: ToolKind = ToolKind.PRESET
    modes: list[ImageToolMode]
    active_preset_id: str | None = None
    active_preset_class: str | None = None
    stability: PresetStability
    provider: str
    protocol: str
    base_url: str
    model: str
    model_parameter: ParameterGuidance
    api_key_configured: bool
    supported_size_presets: list[str]
    unsupported_size_presets: list[str]
    parameter_guidance: dict[str, ParameterGuidance]
    invalid_call_examples: list[str]
    env_vars: list[str]
    env_values_non_secret: ToolEnvValuesNonSecret
    notes: list[str]


class ToolCatalogResponse(BaseModel):
    """ToolCatalogResponse 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    service_name: str
    service_version: str
    tools: list[ToolCatalogEntry]


class PresetCatalogEntry(BaseModel):
    """PresetCatalogEntry 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。

    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    preset_id: str
    preset_class: str
    tool_name: PresetToolName
    provider: PresetProvider
    protocol: PresetProtocol
    default_model: str
    supported_models: list[str]
    base_url: str
    modes: list[PresetModeSupport]
    stability: PresetStability


class PresetCatalogResponse(BaseModel):
    """PresetCatalogResponse 是 跨工具通用数据模型 的结构模型，作用范围为本模块数据边界与调用契约。

    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    service_name: str
    service_version: str
    presets: list[PresetCatalogEntry]
