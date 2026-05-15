"""catalog 模块用于preset 基类执行框架，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

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
from ..contracts.presets import ParameterGuidance, PresetFieldDispatchMode, PresetStability, PresetToolName, ToolKind
from ..errors import ValidationError
from ..models.common import ToolCatalogEntry, ToolCatalogResponse, ToolEnvValuesNonSecret, ToolVersion
from ..presets.loader import resolve_preset_for_tool
from .gpt_image_2_url import GPT_IMAGE_2_URL_ALLOWED_SIZES

CATALOG_TOOL_NAME = "list_image_tools_catalog"


class CatalogRequest(BaseModel):
    """CatalogRequest 是 preset 基类执行框架 的结构模型，作用范围为本模块数据边界与调用契约。
    
    职责：
        - 定义该场景下必须字段与可选字段的语义边界
        - 作为模块间传递对象，保证类型与字段命名一致
    """

    version: ToolVersion


def _non_secret_values(runtime_config: ToolRuntimeConfig) -> ToolEnvValuesNonSecret:
    """执行 _non_secret_values，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

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
    """执行 _supported_size_presets，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

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


def _unsupported_size_presets(runtime_config: ToolRuntimeConfig) -> list[str]:
    if runtime_config.tool_name not in {"gpt_image_2_official", "nano_banana_2_official"}:
        return []
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


def _guidance_for_compatibility_tool(runtime_config: ToolRuntimeConfig) -> dict[str, ParameterGuidance]:
    return {
        "model": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            locked_value=runtime_config.effective_model,
            guidance="legacy compatibility wrapper still accepts model and validates it against supported models",
        ),
        "image_size": ParameterGuidance(
            accepted_by_mcp=True,
            allowed_by_preset=True,
            upstream_behavior=PresetFieldDispatchMode.SEND,
            guidance="only benchmark-verified size pairs listed in supported_size_presets are accepted",
        ),
    }


def _entry_for(runtime_config: ToolRuntimeConfig) -> ToolCatalogEntry:
    """执行 _entry_for，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：执行当前函数并返回对应处理结果
        - 步骤 2：按当前模块约束完成输入到输出转换
    """

    is_formal_tool = runtime_config.tool_name in {"gpt_image_2_official", "nano_banana_2_official"}
    parameter_guidance = _guidance_for_formal_tool(runtime_config) if is_formal_tool else _guidance_for_compatibility_tool(runtime_config)
    return ToolCatalogEntry(
        tool_name=runtime_config.tool_name,
        tool_version=runtime_config.tool_version,
        title=runtime_config.tool_name.replace("_", " ").replace("-", " ").title(),
        tool_kind=ToolKind.PRESET if is_formal_tool else ToolKind.COMPATIBILITY,
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
            "Do not pass model, base_url, api_key, timeout_seconds, retry_count, send_size, or send_quality to formal preset tools."
            if is_formal_tool
            else "For gpt-image-2-url, choose only size pairs listed in supported_size_presets."
        ],
        env_vars=[
            runtime_config.env_names.api_key,
            runtime_config.env_names.preset,
            runtime_config.env_names.base_url,
            runtime_config.env_names.model,
            runtime_config.env_names.supported_models,
            IMAGE_OUTPUT_DIR_ENV,
            IMAGE_BASE_URL_ENV,
            IMAGE_HTTP_TIMEOUT_SECONDS_ENV,
            LOG_LEVEL_ENV,
        ],
        env_values_non_secret=_non_secret_values(runtime_config),
        notes=[
            "Catalog omits API key values and any masked derivatives.",
            *runtime_config.notes,
        ],
    )


def list_image_tools_catalog(version: ToolVersion) -> ToolCatalogResponse:
    """执行 list_image_tools_catalog，用于 preset 基类执行框架 场景下的当前步骤处理。
    
    处理流程：
        - 步骤 1：汇总可用工具信息并对外返回
        - 步骤 2：遍历配置后生成统一目录结构
    """

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
