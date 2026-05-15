"""config 模块用于运行时环境配置装配，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .contracts.presets import PresetToolName
from .models.common import ImageToolMode, ToolVersion

load_dotenv()

GPT_IMAGE_2_OFFICIAL_NAME = "gpt_image_2_official"
NANO_BANANA_2_OFFICIAL_NAME = "nano_banana_2_official"
SERVICE_NAME = "image-generate-mcp-remote"
SERVICE_VERSION = "0.9.6"

DEFAULT_OUTPUT_DIR = Path("storage/images")
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS = 180.0
DEFAULT_TOOL_RETRY_COUNT = 3

GPT_IMAGE_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY"
GPT_IMAGE_2_OFFICIAL_PRESET_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET"

NANO_BANANA_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY"
NANO_BANANA_2_OFFICIAL_PRESET_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET"

IMAGE_OUTPUT_DIR_ENV = "IMAGE_OUTPUT_DIR"
LOG_LEVEL_ENV = "LOG_LEVEL"


class ToolEnvironmentNames(BaseModel):
    """ToolEnvironmentNames 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    api_key: str
    preset: str


class ToolRuntimeConfig(BaseModel):
    """ToolRuntimeConfig 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    tool_name: str
    tool_version: ToolVersion = Field(default=ToolVersion.V1)
    modes: list[ImageToolMode]
    effective_base_url: str
    effective_model: str
    effective_timeout_seconds: float
    effective_retry_count: int
    api_key: str
    api_key_configured: bool
    env_names: ToolEnvironmentNames
    active_preset_id: str
    active_preset_class: str
    provider: str
    protocol: str
    stability: str
    notes: list[str]


class Settings(BaseSettings):
    """Settings 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    image_output_dir: Path = Field(default=DEFAULT_OUTPUT_DIR, alias=IMAGE_OUTPUT_DIR_ENV)
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias=LOG_LEVEL_ENV)

    gpt_image_2_official_api_key: str = Field(default="", alias=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV)
    gpt_image_2_official_preset: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_PRESET_ENV)

    nano_banana_2_official_api_key: str = Field(default="", alias=NANO_BANANA_2_OFFICIAL_API_KEY_ENV)
    nano_banana_2_official_preset: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_PRESET_ENV)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """执行 validate_log_level，用于 运行时环境配置装配 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：校验调用参数是否满足约束
            - 步骤 2：识别非法组合并尽早返回错误
        """

        return value.upper()

    def gpt_image_2_official_config(self) -> ToolRuntimeConfig:
        """执行 gpt_image_2_official_config，用于 运行时环境配置装配 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

        from .presets.loader import resolve_preset_for_tool

        preset = resolve_preset_for_tool(PresetToolName.GPT_IMAGE_2_OFFICIAL, self.gpt_image_2_official_preset)
        resolved = preset.resolve()
        effective_api_key: str = self.gpt_image_2_official_api_key
        return ToolRuntimeConfig(
            tool_name=GPT_IMAGE_2_OFFICIAL_NAME,
            modes=[ImageToolMode.GENERATE, ImageToolMode.EDIT],
            effective_base_url=resolved.config.base_url,
            effective_model=resolved.config.model,
            effective_timeout_seconds=resolved.config.runtime.timeout_seconds,
            effective_retry_count=resolved.config.runtime.retry_count,
            api_key=effective_api_key,
            api_key_configured=bool(effective_api_key),
            env_names=ToolEnvironmentNames(
                api_key=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV,
                preset=GPT_IMAGE_2_OFFICIAL_PRESET_ENV,
            ),
            active_preset_id=resolved.config.preset_id,
            active_preset_class=resolved.preset_class,
            provider=resolved.config.provider.value,
            protocol=resolved.config.protocol.value,
            stability=resolved.config.stability.value,
            notes=list(resolved.config.notes),
        )

    def nano_banana_2_official_config(self) -> ToolRuntimeConfig:
        """执行 nano_banana_2_official_config，用于 运行时环境配置装配 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

        from .presets.loader import resolve_preset_for_tool

        preset = resolve_preset_for_tool(PresetToolName.NANO_BANANA_2_OFFICIAL, self.nano_banana_2_official_preset)
        resolved = preset.resolve()
        effective_api_key: str = self.nano_banana_2_official_api_key
        return ToolRuntimeConfig(
            tool_name=NANO_BANANA_2_OFFICIAL_NAME,
            modes=[ImageToolMode.GENERATE, ImageToolMode.EDIT],
            effective_base_url=resolved.config.base_url,
            effective_model=resolved.config.model,
            effective_timeout_seconds=resolved.config.runtime.timeout_seconds,
            effective_retry_count=resolved.config.runtime.retry_count,
            api_key=effective_api_key,
            api_key_configured=bool(effective_api_key),
            env_names=ToolEnvironmentNames(
                api_key=NANO_BANANA_2_OFFICIAL_API_KEY_ENV,
                preset=NANO_BANANA_2_OFFICIAL_PRESET_ENV,
            ),
            active_preset_id=resolved.config.preset_id,
            active_preset_class=resolved.preset_class,
            provider=resolved.config.provider.value,
            protocol=resolved.config.protocol.value,
            stability=resolved.config.stability.value,
            notes=list(resolved.config.notes),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """执行 get_settings，用于 运行时环境配置装配 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    return Settings()


def clear_runtime_caches() -> None:
    """执行 clear_runtime_caches，用于 运行时环境配置装配 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    from .presets.loader import clear_preset_cache

    get_settings.cache_clear()
    clear_preset_cache()
