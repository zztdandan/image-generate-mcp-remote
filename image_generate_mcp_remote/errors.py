"""errors 模块用于统一错误建模，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from pydantic import BaseModel


class UpstreamErrorDetail(BaseModel):
    """UpstreamErrorDetail 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    status_code: int
    body_excerpt: str


class ImageToolError(RuntimeError):
    """ImageToolError 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    def __init__(self, tool_name: str, mode: str, failure_kind: str, message: str) -> None:
        self.tool_name: str = tool_name
        self.mode: str = mode
        self.failure_kind: str = failure_kind
        super().__init__(f"{tool_name}[{mode}] {failure_kind}: {message}")


class ConfigError(ImageToolError):
    """ConfigError 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "configuration error", message)


class ValidationError(ImageToolError):
    """ValidationError 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "local validation failed", message)


class UpstreamServiceError(ImageToolError):
    """UpstreamServiceError 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    def __init__(self, tool_name: str, mode: str, detail: UpstreamErrorDetail) -> None:
        super().__init__(
            tool_name,
            mode,
            "upstream request failed",
            f"status={detail.status_code}, excerpt={detail.body_excerpt}",
        )
        self.detail: UpstreamErrorDetail = detail


class ResponseParseError(ImageToolError):
    """ResponseParseError 是 统一错误建模 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "response parse failed", message)
