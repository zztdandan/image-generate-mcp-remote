"""Shared error types for image generation tools."""

from __future__ import annotations

from pydantic import BaseModel


class UpstreamErrorDetail(BaseModel):
    """Truncated upstream error detail for safe reporting."""

    status_code: int
    body_excerpt: str


class ImageToolError(RuntimeError):
    """Structured exception with tool and mode context."""

    def __init__(self, tool_name: str, mode: str, failure_kind: str, message: str) -> None:
        self.tool_name: str = tool_name
        self.mode: str = mode
        self.failure_kind: str = failure_kind
        super().__init__(f"{tool_name}[{mode}] {failure_kind}: {message}")


class ConfigError(ImageToolError):
    """Raised when local configuration is invalid or incomplete."""

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "configuration error", message)


class ValidationError(ImageToolError):
    """Raised when local request validation fails."""

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "local validation failed", message)


class UpstreamServiceError(ImageToolError):
    """Raised when an upstream HTTP call fails."""

    def __init__(self, tool_name: str, mode: str, detail: UpstreamErrorDetail) -> None:
        super().__init__(
            tool_name,
            mode,
            "upstream request failed",
            f"status={detail.status_code}, excerpt={detail.body_excerpt}",
        )
        self.detail: UpstreamErrorDetail = detail


class ResponseParseError(ImageToolError):
    """Raised when upstream returned an unexpected payload shape."""

    def __init__(self, tool_name: str, mode: str, message: str) -> None:
        super().__init__(tool_name, mode, "response parse failed", message)
