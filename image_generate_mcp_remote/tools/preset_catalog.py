"""preset_catalog 模块用于 preset 列表查询，作用范围为 `image_generate_mcp_remote` 服务运行时。"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import SERVICE_NAME, SERVICE_VERSION
from ..errors import ValidationError
from ..models.common import PresetCatalogEntry, PresetCatalogResponse, ToolVersion
from ..presets.registry import PRESET_REGISTRY

PRESET_CATALOG_TOOL_NAME = "list_image_presets"


class PresetCatalogRequest(BaseModel):
    """PresetCatalogRequest 是 preset 列表查询 的结构模型，作用范围为本模块数据边界与调用契约。"""

    version: ToolVersion


def _preset_entry(preset_id: str) -> PresetCatalogEntry:
    preset_class = PRESET_REGISTRY[preset_id]
    resolved = preset_class().resolve()
    return PresetCatalogEntry(
        preset_id=resolved.config.preset_id,
        preset_class=resolved.preset_class,
        tool_name=resolved.config.tool_name,
        provider=resolved.config.provider,
        protocol=resolved.config.protocol,
        default_model=resolved.config.model,
        supported_models=[resolved.config.model],
        base_url=resolved.config.base_url,
        modes=list(resolved.config.modes),
        stability=resolved.config.stability,
    )


def list_image_presets(version: ToolVersion) -> PresetCatalogResponse:
    """执行 list_image_presets，用于 preset 列表查询 场景下的当前步骤处理。

    处理流程：
        - 步骤 1：校验版本参数
        - 步骤 2：汇总所有已注册 preset 的公开信息
    """

    request = PresetCatalogRequest(version=version)
    if request.version is not ToolVersion.V1:
        raise ValidationError(PRESET_CATALOG_TOOL_NAME, "catalog", "only version v1 is supported")
    return PresetCatalogResponse(
        service_name=SERVICE_NAME,
        service_version=SERVICE_VERSION,
        presets=[_preset_entry(preset_id) for preset_id in sorted(PRESET_REGISTRY)],
    )
