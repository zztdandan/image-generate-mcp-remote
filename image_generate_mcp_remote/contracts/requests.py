"""Shared request contract bases for image tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..config import DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS, DEFAULT_TOOL_RETRY_COUNT
from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..models.common import ImageToolMode, ToolVersion


class PromptedImageRequestBase(BaseModel):
    """Common fields shared by generate-like image requests."""

    version: ToolVersion
    prompt: str
    save_path: str
    model: str | None = None
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    timeout_seconds: float = Field(default=DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS, ge=1.0)
    retry_count: int = Field(default=DEFAULT_TOOL_RETRY_COUNT, ge=0)


class GenerateImageRequestBase(PromptedImageRequestBase):
    """Common fields shared by tool generate requests."""

    mode: Literal[ImageToolMode.GENERATE]


class EditImageRequestBase(PromptedImageRequestBase):
    """Common fields shared by tool edit requests."""

    mode: Literal[ImageToolMode.EDIT]
