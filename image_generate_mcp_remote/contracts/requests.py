"""Shared request contract bases for image tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ..models.common import ImageToolMode, ToolVersion


class PromptedImageRequestBase(BaseModel):
    """Common fields shared by generate-like image requests."""

    version: ToolVersion
    prompt: str
    save_path: str
    model: str | None = None
    size: str | None = None


class GenerateImageRequestBase(PromptedImageRequestBase):
    """Common fields shared by tool generate requests."""

    mode: Literal[ImageToolMode.GENERATE]


class EditImageRequestBase(PromptedImageRequestBase):
    """Common fields shared by tool edit requests."""

    mode: Literal[ImageToolMode.EDIT]
