"""Runtime configuration and catalog-facing settings models."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models.common import ToolVersion

load_dotenv()

GPT_IMAGE_2_OFFICIAL_NAME = "gpt_image_2_official"
NANO_BANANA_2_OFFICIAL_NAME = "nano_banana_2_official"
SERVICE_NAME = "image-generate-mcp-remote"
SERVICE_VERSION = "0.1.0"

GPT_IMAGE_2_OFFICIAL_DEFAULT_BASE_URL = "https://www.uocode.com/v1"
GPT_IMAGE_2_OFFICIAL_DEFAULT_MODEL = "gpt-image-2"
GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT = ["gpt-image-2"]

NANO_BANANA_2_OFFICIAL_DEFAULT_BASE_URL = "https://www.uocode.com"
NANO_BANANA_2_OFFICIAL_DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT = ["gemini-3.1-flash-image-preview"]

DEFAULT_OUTPUT_DIR = Path("storage/images")
DEFAULT_LOG_LEVEL = "INFO"

GPT_IMAGE_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY"
GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL"
GPT_IMAGE_2_OFFICIAL_MODEL_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL"
GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV = "IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS"

NANO_BANANA_2_OFFICIAL_API_KEY_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY"
NANO_BANANA_2_OFFICIAL_BASE_URL_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL"
NANO_BANANA_2_OFFICIAL_MODEL_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL"
NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV = "IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS"

IMAGE_OUTPUT_DIR_ENV = "IMAGE_OUTPUT_DIR"
IMAGE_BASE_URL_ENV = "IMAGE_BASE_URL"
LOG_LEVEL_ENV = "LOG_LEVEL"
IMAGE_HTTP_TIMEOUT_SECONDS_ENV = "IMAGE_HTTP_TIMEOUT_SECONDS"


class ToolEnvironmentNames(BaseModel):
    """Names of environment variables that influence one tool."""

    api_key: str
    base_url: str
    model: str
    supported_models: str


class ToolRuntimeConfig(BaseModel):
    """Effective configuration for one tool instance."""

    tool_name: str
    tool_version: ToolVersion = Field(default=ToolVersion.V1)
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


def _parse_supported_models(raw_value: str | None, env_name: str) -> tuple[list[str], str]:
    """Parse a comma-separated model list while preserving order."""

    if raw_value is None:
        return [], "default"

    values: list[str] = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not values:
        message = f"Environment variable {env_name} produced an empty supported_models list"
        raise ValueError(message)
    return values, "env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    image_output_dir: Path = Field(default=DEFAULT_OUTPUT_DIR, alias=IMAGE_OUTPUT_DIR_ENV)
    image_base_url: str = Field(default="", alias=IMAGE_BASE_URL_ENV)
    image_http_timeout_seconds: float = Field(default=600.0, alias=IMAGE_HTTP_TIMEOUT_SECONDS_ENV)
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias=LOG_LEVEL_ENV)

    gpt_image_2_official_api_key: str = Field(default="", alias=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV)
    gpt_image_2_official_base_url: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV)
    gpt_image_2_official_model: str | None = Field(default=None, alias=GPT_IMAGE_2_OFFICIAL_MODEL_ENV)
    gpt_image_2_official_supported_models_raw: str | None = Field(
        default=None,
        alias=GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV,
    )

    nano_banana_2_official_api_key: str = Field(default="", alias=NANO_BANANA_2_OFFICIAL_API_KEY_ENV)
    nano_banana_2_official_base_url: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_BASE_URL_ENV)
    nano_banana_2_official_model: str | None = Field(default=None, alias=NANO_BANANA_2_OFFICIAL_MODEL_ENV)
    nano_banana_2_official_supported_models_raw: str | None = Field(
        default=None,
        alias=NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize log level for predictable logging setup."""

        return value.upper()

    def gpt_image_2_official_config(self) -> ToolRuntimeConfig:
        """Build effective config for the OpenAI Images compatible tool."""

        supported_models, source = _parse_supported_models(
            self.gpt_image_2_official_supported_models_raw,
            GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV,
        )
        effective_supported_models: list[str] = (
            supported_models if supported_models else list(GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT)
        )
        return ToolRuntimeConfig(
            tool_name=GPT_IMAGE_2_OFFICIAL_NAME,
            protocol_style="openai-images",
            default_base_url=GPT_IMAGE_2_OFFICIAL_DEFAULT_BASE_URL,
            effective_base_url=self.gpt_image_2_official_base_url or GPT_IMAGE_2_OFFICIAL_DEFAULT_BASE_URL,
            base_url_source="env" if self.gpt_image_2_official_base_url else "default",
            default_model=GPT_IMAGE_2_OFFICIAL_DEFAULT_MODEL,
            effective_model=self.gpt_image_2_official_model or GPT_IMAGE_2_OFFICIAL_DEFAULT_MODEL,
            model_source="env" if self.gpt_image_2_official_model else "default",
            supported_models_default=list(GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT),
            supported_models_effective=effective_supported_models,
            supported_models_source=source,
            api_key=self.gpt_image_2_official_api_key,
            api_key_configured=bool(self.gpt_image_2_official_api_key),
            env_names=ToolEnvironmentNames(
                api_key=GPT_IMAGE_2_OFFICIAL_API_KEY_ENV,
                base_url=GPT_IMAGE_2_OFFICIAL_BASE_URL_ENV,
                model=GPT_IMAGE_2_OFFICIAL_MODEL_ENV,
                supported_models=GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS_ENV,
            ),
        )

    def nano_banana_2_official_config(self) -> ToolRuntimeConfig:
        """Build effective config for the Gemini compatible tool."""

        supported_models, source = _parse_supported_models(
            self.nano_banana_2_official_supported_models_raw,
            NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV,
        )
        effective_supported_models: list[str] = (
            supported_models if supported_models else list(NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT)
        )
        return ToolRuntimeConfig(
            tool_name=NANO_BANANA_2_OFFICIAL_NAME,
            protocol_style="gemini-generate-content",
            default_base_url=NANO_BANANA_2_OFFICIAL_DEFAULT_BASE_URL,
            effective_base_url=self.nano_banana_2_official_base_url or NANO_BANANA_2_OFFICIAL_DEFAULT_BASE_URL,
            base_url_source="env" if self.nano_banana_2_official_base_url else "default",
            default_model=NANO_BANANA_2_OFFICIAL_DEFAULT_MODEL,
            effective_model=self.nano_banana_2_official_model or NANO_BANANA_2_OFFICIAL_DEFAULT_MODEL,
            model_source="env" if self.nano_banana_2_official_model else "default",
            supported_models_default=list(NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_DEFAULT),
            supported_models_effective=effective_supported_models,
            supported_models_source=source,
            api_key=self.nano_banana_2_official_api_key,
            api_key_configured=bool(self.nano_banana_2_official_api_key),
            env_names=ToolEnvironmentNames(
                api_key=NANO_BANANA_2_OFFICIAL_API_KEY_ENV,
                base_url=NANO_BANANA_2_OFFICIAL_BASE_URL_ENV,
                model=NANO_BANANA_2_OFFICIAL_MODEL_ENV,
                supported_models=NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS_ENV,
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings to keep runtime reads stable."""

    return Settings()
