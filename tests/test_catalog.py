from pathlib import Path

from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.models.common import ToolVersion
from image_generate_mcp_remote.tools.catalog import list_image_tools_catalog


def test_catalog_reports_defaults_and_env_overrides(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path / "images"))
    monkeypatch.setenv("IMAGE_BASE_URL", "https://cdn.example.com/assets")
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-a")
    get_settings.cache_clear()

    result = list_image_tools_catalog(ToolVersion.V1)

    assert result.service_name == "image-generate-mcp-remote"
    assert len(result.tools) == 4
    gpt_entry = next(tool for tool in result.tools if tool.tool_name == "gpt_image_2_official")
    assert gpt_entry.active_preset_id == "openai_gpt_image_2"
    assert gpt_entry.model == "gpt-image-2"
    assert gpt_entry.parameter_guidance["model"].accepted_by_mcp is False
    assert gpt_entry.env_values_non_secret.output_dir == str(tmp_path / "images")
    assert gpt_entry.env_values_non_secret.image_base_url == "https://cdn.example.com/assets"
    assert gpt_entry.env_values_non_secret.image_http_timeout_seconds == 180
    assert "1K + 1:1 (gpt=1280x1280)" in gpt_entry.supported_size_presets
    assert gpt_entry.api_key_configured is True

    nano_entry = next(tool for tool in result.tools if tool.tool_name == "nano_banana_2_official")
    assert nano_entry.active_preset_id == "google_nano_banana"
    assert nano_entry.model == "gemini-3.1-flash-image-preview"
    assert "2K + 16:9 (gpt=2048x1152, nano=2752x1536)" in nano_entry.supported_size_presets

    gpt_temporary_entry = next(tool for tool in result.tools if tool.tool_name == "gpt_image_2_temporary")
    assert gpt_temporary_entry.tool_kind == "temporary"
    assert gpt_temporary_entry.active_preset_id is None
    assert gpt_temporary_entry.parameter_guidance["base_url"].accepted_by_mcp is True
    assert gpt_temporary_entry.parameter_guidance["quality"].upstream_behavior == "drop"

    nano_temporary_entry = next(tool for tool in result.tools if tool.tool_name == "nano_banana_2_temporary")
    assert nano_temporary_entry.tool_kind == "temporary"
    assert nano_temporary_entry.protocol == "gemini_generate_content"
    assert "2K + 16:9 (gpt=2048x1152, nano=2752x1536)" in nano_temporary_entry.supported_size_presets

    get_settings.cache_clear()
