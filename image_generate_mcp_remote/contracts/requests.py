"""requests 模块用于工具请求基类约束，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..contracts.image_size import ImageAspectRatio, ImageSizeTier
from ..models.common import ImageToolMode, ToolVersion

DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS = 180.0
DEFAULT_TOOL_RETRY_COUNT = 3


class PromptedImageRequestBase(BaseModel):
    """PromptedImageRequestBase 是 工具请求基类约束 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    version: ToolVersion
    prompt: str
    save_path: str
    model: str | None = None
    aspect_ratio: ImageAspectRatio = ImageAspectRatio.SQUARE
    image_size: ImageSizeTier = ImageSizeTier.SIZE_1K
    timeout_seconds: float = Field(default=DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS, ge=1.0)
    retry_count: int = Field(default=DEFAULT_TOOL_RETRY_COUNT, ge=0)


class GenerateImageRequestBase(PromptedImageRequestBase):
    """GenerateImageRequestBase 是 工具请求基类约束 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    mode: Literal[ImageToolMode.GENERATE]


class EditImageRequestBase(PromptedImageRequestBase):
    """EditImageRequestBase 是 工具请求基类约束 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    mode: Literal[ImageToolMode.EDIT]
