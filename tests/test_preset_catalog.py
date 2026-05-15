from image_generate_mcp_remote.models.common import ToolVersion
from image_generate_mcp_remote.tools.preset_catalog import list_image_presets


def test_preset_catalog_lists_registered_presets():
    result = list_image_presets(ToolVersion.V1)

    assert result.service_name == "image-generate-mcp-remote"
    assert len(result.presets) >= 2

    openai_preset = next(item for item in result.presets if item.preset_id == "openai_gpt_image_2")
    assert openai_preset.tool_name == "gpt_image_2_official"
    assert openai_preset.base_url == "https://api.openai.com/v1"
    assert openai_preset.default_model == "gpt-image-2"
    assert openai_preset.supported_models == ["gpt-image-2"]

    nano_preset = next(item for item in result.presets if item.preset_id == "google_nano_banana")
    assert nano_preset.tool_name == "nano_banana_2_official"
    assert nano_preset.default_model == "gemini-3.1-flash-image-preview"
    assert nano_preset.supported_models == ["gemini-3.1-flash-image-preview"]
