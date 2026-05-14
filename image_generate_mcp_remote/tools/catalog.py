"""Catalog tool describing exposed image-generation tools."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ..config import (
    IMAGE_BASE_URL_ENV,
    IMAGE_HTTP_TIMEOUT_SECONDS_ENV,
    IMAGE_OUTPUT_DIR_ENV,
    LOG_LEVEL_ENV,
    SERVICE_NAME,
    SERVICE_VERSION,
    ToolRuntimeConfig,
    get_settings,
)
from ..contracts.image_size import SUPPORTED_IMAGE_SIZES, SupportedImageSize
from ..errors import ValidationError
from ..models.common import ToolCatalogEntry, ToolCatalogResponse, ToolEnvValuesNonSecret, ToolVersion
from .gpt_image_2_url import GPT_IMAGE_2_URL_ALLOWED_SIZES

CATALOG_TOOL_NAME = "list_image_tools_catalog"


class CatalogRequest(BaseModel):
    """Catalog tool request contract."""

    version: ToolVersion


def _non_secret_values(runtime_config: ToolRuntimeConfig) -> ToolEnvValuesNonSecret:
    """Collect catalog-safe effective values for one tool."""

    settings = get_settings()
    return ToolEnvValuesNonSecret(
        base_url=runtime_config.effective_base_url,
        base_url_source=runtime_config.base_url_source,
        model=runtime_config.effective_model,
        model_source=runtime_config.model_source,
        supported_models=list(runtime_config.supported_models_effective),
        supported_models_source=runtime_config.supported_models_source,
        output_dir=str(Path(settings.image_output_dir)),
        image_base_url=settings.image_base_url,
        image_base_url_source="env" if settings.image_base_url else "default",
        image_http_timeout_seconds=settings.image_http_timeout_seconds,
    )


def _supported_size_presets(runtime_config: ToolRuntimeConfig) -> list[str]:
    """Expose per-tool size presets in the catalog for MCP clients and agents."""

    size_presets: tuple[SupportedImageSize, ...]
    if runtime_config.tool_name == "gpt-image-2-url":
        size_presets = GPT_IMAGE_2_URL_ALLOWED_SIZES
    else:
        size_presets = SUPPORTED_IMAGE_SIZES.all()
    if runtime_config.tool_name == "nano_banana_2_official":
        return [
            f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value}, nano={preset.nano_banana_value})"
            for preset in size_presets
        ]
    return [f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value})" for preset in size_presets]


def _entry_for(runtime_config: ToolRuntimeConfig) -> ToolCatalogEntry:
    """Build one catalog entry from runtime config."""

    return ToolCatalogEntry(
        tool_name=runtime_config.tool_name,
        tool_version=runtime_config.tool_version,
        modes=list(runtime_config.modes),
        protocol_style=runtime_config.protocol_style,
        default_base_url=runtime_config.default_base_url,
        effective_base_url=runtime_config.effective_base_url,
        default_model=runtime_config.default_model,
        effective_model=runtime_config.effective_model,
        supported_models_default=list(runtime_config.supported_models_default),
        supported_models_effective=list(runtime_config.supported_models_effective),
        supported_size_presets=_supported_size_presets(runtime_config),
        env_vars=[
            runtime_config.env_names.api_key,
            runtime_config.env_names.base_url,
            runtime_config.env_names.model,
            runtime_config.env_names.supported_models,
            IMAGE_OUTPUT_DIR_ENV,
            IMAGE_BASE_URL_ENV,
            IMAGE_HTTP_TIMEOUT_SECONDS_ENV,
            LOG_LEVEL_ENV,
        ],
        env_values_non_secret=_non_secret_values(runtime_config),
        api_key_configured=runtime_config.api_key_configured,
        notes=[
            "Catalog omits API key values and any masked derivatives.",
            "Supported models come from code defaults plus optional env override.",
        ],
    )


def list_image_tools_catalog(version: ToolVersion) -> ToolCatalogResponse:
    """Return the exposed image tool catalog for the current runtime."""

    request = CatalogRequest(version=version)
    if request.version is not ToolVersion.V1:
        raise ValidationError(CATALOG_TOOL_NAME, "catalog", "only version v1 is supported")

    settings = get_settings()
    return ToolCatalogResponse(
        service_name=SERVICE_NAME,
        service_version=SERVICE_VERSION,
        tools=[
            _entry_for(settings.gpt_image_2_official_config()),
            _entry_for(settings.nano_banana_2_official_config()),
            _entry_for(settings.gpt_image_2_url_config()),
        ],
    )
