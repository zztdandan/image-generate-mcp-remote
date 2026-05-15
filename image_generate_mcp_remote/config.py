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
GPT_IMAGE_2_URL_NAME = "gpt-image-2-url"
SERVICE_NAME = "image-generate-mcp-remote"
SERVICE_VERSION = "0.9.6"

GPT_IMAGE_2_OFFICIAL_DEFAULT_BASE_URL = "https://api.openai.com/v1"
GPT_IMAGE_2_OFFICIAL_DEFAULT_MODEL = "gpt-image-2"
GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT = ["gpt-image-2", "gpt-image-2-vip"]

NANO_BANANA_2_OFFICIAL_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
NANO_BANANA_2_OFFICIAL_DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT = ["gemini-3.1-flash-image-preview"]

GPT_IMAGE_2_URL_DEFAULT_BASE_URL = "https://www.right.codes/draw/v1"
GPT_IMAGE_2_URL_DEFAULT_MODEL = "gpt-image-2-vip"
GPT_IMAGE_2_URL_SUPPORTED_MODELS_DEFAULT = ["gpt-image-2-vip"]

DEFAULT_OUTPUT_DIR = Path("storage/images")
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS = 180.0
DEFAULT_TOOL_RETRY_COUNT = 3

GPT_IMAGE_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY"
GPT_IMAGE_2_OFFICIAL_PRESET_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET"
GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL"
GPT_IMAGE_2_OFFICIAL_MODEL_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL"
GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS"

NANO_BANANA_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY"
NANO_BANANA_2_OFFICIAL_PRESET_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET"
NANO_BANANA_2_OFFICIAL_BASE_URL_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL"
NANO_BANANA_2_OFFICIAL_MODEL_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL"
NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS"

GPT_IMAGE_2_URL_API_KEY_ENV = "IMG_GEN_GPT_IMAGE_2_URL_API_KEY"
GPT_IMAGE_2_URL_BASE_URL_ENV = "IMG_GEN_GPT_IMAGE_2_URL_BASE_URL"
GPT_IMAGE_2_URL_MODEL_ENV = "IMG_GEN_GPT_IMAGE_2_URL_MODEL"
GPT_IMAGE_2_URL_SUPPORTED_MODELS_ENV = "IMG_GEN_GPT_IMAGE_2_URL_SUPPORTED_MODELS"

IMAGE_OUTPUT_DIR_ENV = "IMAGE_OUTPUT_DIR"
IMAGE_BASE_URL_ENV = "IMAGE_BASE_URL"
LOG_LEVEL_ENV = "LOG_LEVEL"
IMAGE_HTTP_TIMEOUT_SECONDS_ENV = "IMAGE_HTTP_TIMEOUT_SECONDS"


class ToolEnvironmentNames(BaseModel):
    """ToolEnvironmentNames 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    api_key: str
    preset: str
    base_url: str
    model: str
    supported_models: str


class ToolRuntimeConfig(BaseModel):
    """ToolRuntimeConfig 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    tool_name: str
    tool_version: ToolVersion = Field(default=ToolVersion.V1)
    modes: list[ImageToolMode]
    protocol_style: str
    default_base_url: str
    effective_base_url: str
    base_url_source: str
    default_model: str
    effective_model: str
    model_source: str
    supported_models_default: list[str]
    supported_models_effective: list[str]
    supported_models_source: str
    api_key: str
    api_key_configured: bool
    env_names: ToolEnvironmentNames
    active_preset_id: str
    active_preset_class: str
    provider: str
    protocol: str
    stability: str
    notes: list[str]


def _parse_supported_models(raw_value: str | None, env_name: str) -> tuple[list[str], str]:
    """执行 _parse_supported_models，用于 运行时环境配置装配 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：解析输入并转换为内部可用结构
        - 步骤 2：校验格式后输出标准化结果
    """

    if raw_value is None:
        return [], "default"

    values: list[str] = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not values:
        message = f"Environment variable {env_name} produced an empty supported_models list"
        raise ValueError(message)
    return values, "env"


class Settings(BaseSettings):
    """Settings 是 运行时环境配置装配 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    image_output_dir: Path = Field(default=DEFAULT_OUTPUT_DIR, alias=IMAGE_OUTPUT_DIR_ENV)
    image_base_url: str = Field(default="", alias=IMAGE_BASE_URL_ENV)
    image_http_timeout_seconds: float = Field(default=DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS, alias=IMAGE_HTTP_TIMEOUT_SECONDS_ENV)
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias=LOG_LEVEL_ENV)

    gpt_image_2_official_api_key: str = Field(default="", alias=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV)
    gpt_image_2_official_preset: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_PRESET_ENV)
    gpt_image_2_official_base_url: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV)
    gpt_image_2_official_model: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_MODEL_ENV)
    gpt_image_2_official_supported_models_raw: str | None = Field(
        default=None,
        alias=GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV,
    )

    nano_banana_2_official_api_key: str = Field(default="", alias=NANO_BANANA_2_OFFICIAL_API_KEY_ENV)
    nano_banana_2_official_preset: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_PRESET_ENV)
    nano_banana_2_official_base_url: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_BASE_URL_ENV)
    nano_banana_2_official_model: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_MODEL_ENV)
    nano_banana_2_official_supported_models_raw: str | None = Field(
        default=None,
        alias=NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV,
    )

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
            protocol_style=resolved.config.protocol.value,
            default_base_url=resolved.config.base_url,
            effective_base_url=resolved.config.base_url,
            base_url_source="preset",
            default_model=resolved.config.model,
            effective_model=resolved.config.model,
            model_source="preset",
            supported_models_default=[resolved.config.model],
            supported_models_effective=[resolved.config.model],
            supported_models_source="preset",
            api_key=effective_api_key,
            api_key_configured=bool(effective_api_key),
            env_names=ToolEnvironmentNames(
                api_key=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV,
                preset=GPT_IMAGE_2_OFFICIAL_PRESET_ENV,
                base_url=GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV,
                model=GPT_IMAGE_2_OFFICIAL_MODEL_ENV,
                supported_models=GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV,
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
            protocol_style=resolved.config.protocol.value,
            default_base_url=resolved.config.base_url,
            effective_base_url=resolved.config.base_url,
            base_url_source="preset",
            default_model=resolved.config.model,
            effective_model=resolved.config.model,
            model_source="preset",
            supported_models_default=[resolved.config.model],
            supported_models_effective=[resolved.config.model],
            supported_models_source="preset",
            api_key=effective_api_key,
            api_key_configured=bool(effective_api_key),
            env_names=ToolEnvironmentNames(
                api_key=NANO_BANANA_2_OFFICIAL_API_KEY_ENV,
                preset=NANO_BANANA_2_OFFICIAL_PRESET_ENV,
                base_url=NANO_BANANA_2_OFFICIAL_BASE_URL_ENV,
                model=NANO_BANANA_2_OFFICIAL_MODEL_ENV,
                supported_models=NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV,
            ),
            active_preset_id=resolved.config.preset_id,
            active_preset_class=resolved.preset_class,
            provider=resolved.config.provider.value,
            protocol=resolved.config.protocol.value,
            stability=resolved.config.stability.value,
            notes=list(resolved.config.notes),
        )

    gpt_image_2_url_api_key: str = Field(default="", alias=GPT_IMAGE_2_URL_API_KEY_ENV)
    gpt_image_2_url_base_url: str | None = Field(default=None, alias=GPT_IMAGE_2_URL_BASE_URL_ENV)
    gpt_image_2_url_model: str | None = Field(default=None, alias=GPT_IMAGE_2_URL_MODEL_ENV)
    gpt_image_2_url_supported_models_raw: str | None = Field(
        default=None,
        alias=GPT_IMAGE_2_URL_SUPPORTED_MODELS_ENV,
    )

    def gpt_image_2_url_config(self) -> ToolRuntimeConfig:
        """执行 gpt_image_2_url_config，用于 运行时环境配置装配 场景下的当前步骤处理。
        
        处理流程：
            - 步骤 1：执行当前函数并返回对应处理结果
            - 步骤 2：按当前模块约束完成输入到输出转换
        """

        supported_models, source = _parse_supported_models(
            self.gpt_image_2_url_supported_models_raw,
            GPT_IMAGE_2_URL_SUPPORTED_MODELS_ENV,
        )
        effective_supported_models: list[str] = (
            supported_models if supported_models else list(GPT_IMAGE_2_URL_SUPPORTED_MODELS_DEFAULT)
        )
        return ToolRuntimeConfig(
            tool_name=GPT_IMAGE_2_URL_NAME,
            modes=[ImageToolMode.GENERATE],
            protocol_style="gpt-image-2-url-generations",
            default_base_url=GPT_IMAGE_2_URL_DEFAULT_BASE_URL,
            effective_base_url=self.gpt_image_2_url_base_url or GPT_IMAGE_2_URL_DEFAULT_BASE_URL,
            base_url_source="env" if self.gpt_image_2_url_base_url else "default",
            default_model=GPT_IMAGE_2_URL_DEFAULT_MODEL,
            effective_model=self.gpt_image_2_url_model or GPT_IMAGE_2_URL_DEFAULT_MODEL,
            model_source="env" if self.gpt_image_2_url_model else "default",
            supported_models_default=list(GPT_IMAGE_2_URL_SUPPORTED_MODELS_DEFAULT),
            supported_models_effective=effective_supported_models,
            supported_models_source=source,
            api_key=self.gpt_image_2_url_api_key,
            api_key_configured=bool(self.gpt_image_2_url_api_key),
            env_names=ToolEnvironmentNames(
                api_key=GPT_IMAGE_2_URL_API_KEY_ENV,
                preset=GPT_IMAGE_2_OFFICIAL_PRESET_ENV,
                base_url=GPT_IMAGE_2_URL_BASE_URL_ENV,
                model=GPT_IMAGE_2_URL_MODEL_ENV,
                supported_models=GPT_IMAGE_2_URL_SUPPORTED_MODELS_ENV,
            ),
            active_preset_id="gpt_image_2_url_compatibility",
            active_preset_class="GptImage2UrlCompatibilityWrapper",
            provider="right_codes",
            protocol="openai_images",
            stability="stable",
            notes=["Compatibility wrapper retained for the legacy gpt-image-2-url tool."],
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
