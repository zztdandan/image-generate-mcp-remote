"""Common structured models shared across image tools."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONMap: TypeAlias = dict[str, JSONValue]


class ToolVersion(StrEnum):
    """Supported request contract versions."""

    V1 = "v1"


class ImageToolMode(StrEnum):
    """Shared operation modes exposed by image tools."""

    GENERATE = "generate"
    EDIT = "edit"


class ImageToolStatus(StrEnum):
    """Top-level tool execution status."""

    OK = "ok"


class InputImageSourceType(StrEnum):
    """Ways a caller can provide an input image."""

    PATH = "path"
    BASE64 = "base64"
    DATA_URL = "data_url"


class InputImageFromPath(BaseModel):
    """Image reference pointing at a local file path."""

    source_type: Literal[InputImageSourceType.PATH] = InputImageSourceType.PATH
    path: str
    filename: str | None = None
    mime_type: str | None = None


class InputImageFromBase64(BaseModel):
    """Image payload provided as raw base64 content."""

    source_type: Literal[InputImageSourceType.BASE64] = InputImageSourceType.BASE64
    data_base64: str
    filename: str
    mime_type: str


class InputImageFromDataUrl(BaseModel):
    """Image payload provided as a data URL."""

    source_type: Literal[InputImageSourceType.DATA_URL] = InputImageSourceType.DATA_URL
    data_url: str
    filename: str | None = None


InputImage: TypeAlias = Annotated[
    InputImageFromPath | InputImageFromBase64 | InputImageFromDataUrl,
    Field(discriminator="source_type"),
]


class ResolvedInputImage(BaseModel):
    """Normalized image content used internally by tool implementations."""

    mime_type: str
    filename: str
    data: bytes


class UsageInfo(BaseModel):
    """Optional usage metadata returned by an upstream provider."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ImageToolResult(BaseModel):
    """Uniform high-level image tool result for MCP clients."""

    status: ImageToolStatus = Field(default=ImageToolStatus.OK)
    tool_name: str
    tool_version: ToolVersion
    mode: ImageToolMode
    provider_model: str
    file_path: str
    image_uri: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    usage: UsageInfo | None = None
    provider_response_excerpt: dict[str, str] | None = None
    text_output: str | None = None


class ToolEnvValuesNonSecret(BaseModel):
    """Catalog-safe, non-secret effective values for one tool."""

    base_url: str
    base_url_source: str
    model: str
    model_source: str
    supported_models: list[str]
    supported_models_source: str
    output_dir: str
    image_base_url: str
    image_base_url_source: str


class ToolCatalogEntry(BaseModel):
    """One catalog row describing a single tool contract."""

    tool_name: str
    tool_version: ToolVersion
    modes: list[ImageToolMode]
    protocol_style: str
    default_base_url: str
    effective_base_url: str
    default_model: str
    effective_model: str
    supported_models_default: list[str]
    supported_models_effective: list[str]
    env_vars: list[str]
    env_values_non_secret: ToolEnvValuesNonSecret
    api_key_configured: bool
    notes: list[str]


class ToolCatalogResponse(BaseModel):
    """Catalog tool response covering the whole MCP image service."""

    service_name: str
    service_version: str
    tools: list[ToolCatalogEntry]
