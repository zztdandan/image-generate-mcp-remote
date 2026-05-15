from pathlib import Path

from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.models.common import ToolVersion
from image_generate_mcp_remote.tools.catalog import list_image_tools_catalog


def test_catalog_reports_defaults_and_env_overrides(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path / "images"))
    monkeypatch.setenv("IMAGE_BASE_URL", "https://cdn.example.com/assets")
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-a")
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL", "gpt-image-2-alt")
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS", "gpt-image-2,gpt-image-2-alt")
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS", "gemini-3.1-flash-image-preview,gemini-fast")
    get_settings.cache_clear()

    result = list_image_tools_catalog(ToolVersion.V1)

    assert result.service_name == "image-generate-mcp-remote"
    assert len(result.tools) == 3
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

    gpt_image_2_url_entry = next(tool for tool in result.tools if tool.tool_name == "gpt-image-2-url")
    assert gpt_image_2_url_entry.model == "gpt-image-2-vip"
    assert gpt_image_2_url_entry.modes == ["generate"]
    assert "1K + 1:1 (gpt=1280x1280)" in gpt_image_2_url_entry.supported_size_presets
    assert "4K + 16:9 (gpt=3840x2160)" in gpt_image_2_url_entry.supported_size_presets
    assert "2K + 3:2 (gpt=2048x1360)" not in gpt_image_2_url_entry.supported_size_presets

    get_settings.cache_clear()
