"""catalog 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ..config import (
    DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
    IMAGE_OUTPUT_DIR_ENV,
    LOG_LEVEL_ENV,
    SERVICE_NAME,
    SERVICE_VERSION,
    ToolRuntimeConfig,
    get_settings,
)
from ..contracts.image_size import SUPPORTED_IMAGE_SIZES, SupportedImageSize
from ..contracts.presets import ParameterGuidance, PresetFieldDispatchMode, PresetProtocol, PresetProvider, PresetStability, PresetToolName, ToolKind
from ..errors import ValidationError
from ..models.common import ToolCatalogEntry, ToolCatalogResponse, ToolEnvValuesNonSecret, ToolVersion
from ..presets.loader import resolve_preset_for_tool

CATALOG_TOOL_NAME = "list_image_tools_catalog"
GPT_IMAGE_2_TEMPORARY_NAME = "gpt_image_2_temporary"
NANO_BANANA_2_TEMPORARY_NAME = "nano_banana_2_temporary"


class CatalogRequest(BaseModel):
    """CatalogRequest 是 preset 基类执行框架 的结构模型，作用范围为本模块数据边界与调用契约。"""

    version: ToolVersion


def _non_secret_values(runtime_config: ToolRuntimeConfig) -> ToolEnvValuesNonSecret:
    settings = get_settings()
    return ToolEnvValuesNonSecret(
        base_url=runtime_config.effective_base_url,
        base_url_source="preset",
        model=runtime_config.effective_model,
        model_source="preset",
        supported_models=[runtime_config.effective_model],
        supported_models_source="preset",
        output_dir=str(Path(settings.image_output_dir)),
        request_timeout_seconds=runtime_config.effective_timeout_seconds,
        request_timeout_source="preset",
        retry_count=runtime_config.effective_retry_count,
        retry_count_source="preset",
    )


def _temporary_non_secret_values() -> ToolEnvValuesNonSecret:
    settings = get_settings()
    return ToolEnvValuesNonSecret(
        base_url="",
        base_url_source="per_call",
        model="",
        model_source="per_call",
        supported_models=[],
        supported_models_source="per_call",
        output_dir=str(Path(settings.image_output_dir)),
        request_timeout_seconds=DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS,
        request_timeout_source="per_call_default",
        retry_count=0,
        retry_count_source="fixed",
    )


def _supported_size_presets(runtime_config: ToolRuntimeConfig) -> list[str]:
    size_presets = SUPPORTED_IMAGE_SIZES.all()
    if runtime_config.tool_name == "nano_banana_2_official":
        return [
            f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value}, nano={preset.nano_banana_value})"
            for preset in size_presets
        ]
    return [f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value})" for preset in size_presets]


def _unsupported_size_presets(runtime_config: ToolRuntimeConfig) -> list[str]:
    preset_tool_name = PresetToolName(runtime_config.tool_name)
    preset_env = (
        get_settings().gpt_image_2_official_preset
        if preset_tool_name is PresetToolName.GPT_IMAGE_2_OFFICIAL
        else get_settings().nano_banana_2_official_preset
    )
    preset = resolve_preset_for_tool(preset_tool_name, preset_env)
    return [
        f"{item.image_size.value} + {item.aspect_ratio.value}"
        for item in preset.resolve().config.unsupported_sizes
    ]


def _guidance_for_formal_tool(runtime_config: ToolRuntimeConfig) -> dict[str, ParameterGuidance]:
    preset_tool_name = PresetToolName(runtime_config.tool_name)
    preset_env = (
        get_settings().gpt_image_2_official_preset
        if preset_tool_name is PresetToolName.GPT_IMAGE_2_OFFICIAL
        else get_settings().nano_banana_2_official_preset
    )
    preset = resolve_preset_for_tool(preset_tool_name, preset_env)
    resolved = preset.resolve()
    return {
        "model": ParameterGuidance(
            accepted_by_mcp=False,
            allowed_by_preset=False,
            locked_value=resolved.config.model,
            guidance="model is preset-owned; do not pass model per call",
        ),
        "preset": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            guidance="preset is optional per call; if you pass preset, you must also pass api_key in the same request; otherwise the configured preset is used",
        ),
        "api_key": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            guidance="api_key is optional per call; if preset is provided in the same request, api_key becomes required; otherwise the configured API key is used",
            must_pair_with="preset",
        ),
        "mode": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            allowed_values=[mode.value for mode in resolved.config.modes],
            guidance="mode must be one of the active preset modes",
        ),
        "quality": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=resolved.config.dispatch.quality,
            guidance="quality remains in the MCP schema; the active preset decides whether it is sent, dropped, or moved into the prompt",
        ),
        "image_size": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            allowed_values=sorted({preset_item.tier.value for preset_item in resolved.supported_sizes}),
            must_pair_with="aspect_ratio",
            upstream_behavior=resolved.config.dispatch.size,
            guidance="image_size must be paired with aspect_ratio and must appear in supported_size_presets",
        ),
        "aspect_ratio": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            allowed_values=sorted({preset_item.aspect_ratio.value for preset_item in resolved.supported_sizes}),
            must_pair_with="image_size",
            upstream_behavior=resolved.config.dispatch.size,
            guidance="aspect_ratio must be paired with image_size and must appear in supported_size_presets",
        ),
    }


def _temporary_guidance(protocol: PresetProtocol) -> dict[str, ParameterGuidance]:
    size_behavior = PresetFieldDispatchMode.SEND
    guidance: dict[str, ParameterGuidance] = {
        "api_key": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            guidance="temporary tools accept api_key per call for unknown-provider exploration",
        ),
        "base_url": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            guidance="temporary tools accept base_url per call and do not participate in the preset registry",
        ),
        "model": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            guidance="temporary tools accept model per call so successful probes can later become reviewed presets",
        ),
        "image_size": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            allowed_values=sorted({preset_item.tier.value for preset_item in SUPPORTED_IMAGE_SIZES.all()}),
            must_pair_with="aspect_ratio",
            upstream_behavior=size_behavior,
            guidance="temporary tools send the standard size mapping as the conservative compatibility probe",
        ),
        "aspect_ratio": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            allowed_values=sorted({preset_item.aspect_ratio.value for preset_item in SUPPORTED_IMAGE_SIZES.all()}),
            must_pair_with="image_size",
            upstream_behavior=size_behavior,
            guidance="temporary tools send the standard aspect ratio mapping with image_size",
        ),
    }
    if protocol is PresetProtocol.OPENAI_IMAGES:
        guidance["quality"] = ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=PresetFieldDispatchMode.DROP,
            guidance="quality is accepted but dropped unless send_quality=true is explicitly provided",
        )
        guidance["output_format"] = ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=PresetFieldDispatchMode.DROP,
            guidance="output_format is accepted but dropped unless send_output_format=true is explicitly provided",
        )
        guidance["background"] = ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=PresetFieldDispatchMode.DROP,
            guidance="background is accepted but dropped unless send_background=true is explicitly provided",
        )
        guidance["moderation"] = ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=PresetFieldDispatchMode.DROP,
            guidance="moderation is accepted but dropped unless send_moderation=true is explicitly provided",
        )
    return guidance


def _entry_for(runtime_config: ToolRuntimeConfig) -> ToolCatalogEntry:
    parameter_guidance = _guidance_for_formal_tool(runtime_config)
    return ToolCatalogEntry(
        tool_name=runtime_config.tool_name,
        tool_version=runtime_config.tool_version,
        title=runtime_config.tool_name.replace("_", " ").title(),
        tool_kind=ToolKind.PRESET,
        modes=list(runtime_config.modes),
        active_preset_id=runtime_config.active_preset_id,
        active_preset_class=runtime_config.active_preset_class,
        stability=PresetStability(runtime_config.stability),
        provider=runtime_config.provider,
        protocol=runtime_config.protocol,
        base_url=runtime_config.effective_base_url,
        model=runtime_config.effective_model,
        model_parameter=parameter_guidance["model"],
        api_key_configured=runtime_config.api_key_configured,
        supported_size_presets=_supported_size_presets(runtime_config),
        unsupported_size_presets=_unsupported_size_presets(runtime_config),
        parameter_guidance=parameter_guidance,
        invalid_call_examples=[
            "Do not pass model, base_url, timeout_seconds, retry_count, send_size, or send_quality to formal preset tools."
        ],
        env_vars=[
            runtime_config.env_names.api_key,
            runtime_config.env_names.preset,
            IMAGE_OUTPUT_DIR_ENV,
            LOG_LEVEL_ENV,
        ],
        env_values_non_secret=_non_secret_values(runtime_config),
        notes=[
            "Catalog omits API key values and any masked derivatives.",
            "Formal tool timeout and retry behavior are owned by the active preset, not by global timeout env vars.",
            *runtime_config.notes,
        ],
    )


def _temporary_entry(tool_name: str, protocol: PresetProtocol) -> ToolCatalogEntry:
    parameter_guidance = _temporary_guidance(protocol)
    is_nano = protocol is PresetProtocol.GEMINI_GENERATE_CONTENT
    return ToolCatalogEntry(
        tool_name=tool_name,
        tool_version=ToolVersion.V1,
        title=tool_name.replace("_", " ").title(),
        tool_kind=ToolKind.TEMPORARY,
        modes=["generate"],
        active_preset_id=None,
        active_preset_class=None,
        stability=PresetStability.EXPERIMENTAL,
        provider=PresetProvider.CUSTOM.value,
        protocol=protocol.value,
        base_url="",
        model="",
        model_parameter=parameter_guidance["model"],
        api_key_configured=False,
        supported_size_presets=[
            f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value}, nano={preset.nano_banana_value})"
            if is_nano
            else f"{preset.tier.value} + {preset.aspect_ratio.value} (gpt={preset.gpt_value})"
            for preset in SUPPORTED_IMAGE_SIZES.all()
        ],
        unsupported_size_presets=[],
        parameter_guidance=parameter_guidance,
        invalid_call_examples=[
            "Do not use temporary tools for production defaults; promote successful provider probes into reviewed preset classes."
        ],
        env_vars=[IMAGE_OUTPUT_DIR_ENV, LOG_LEVEL_ENV],
        env_values_non_secret=_temporary_non_secret_values(),
        notes=[
            "Temporary exploration tool; api_key, base_url, and model are supplied per call.",
            f"Default request timeout is {DEFAULT_IMAGE_HTTP_TIMEOUT_SECONDS} seconds unless timeout_seconds is supplied per call.",
        ],
    )


def list_image_tools_catalog(version: ToolVersion) -> ToolCatalogResponse:
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
            _temporary_entry(GPT_IMAGE_2_TEMPORARY_NAME, PresetProtocol.OPENAI_IMAGES),
            _temporary_entry(NANO_BANANA_2_TEMPORARY_NAME, PresetProtocol.GEMINI_GENERATE_CONTENT),
        ],
    )
