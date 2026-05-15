from image_generate_mcp_remote.models.common import ToolVersion
from image_generate_mcp_remote.server import list_image_tools_catalog_tool


def test_server_catalog_tool_returns_expected_shape():
    result = list_image_tools_catalog_tool(ToolVersion.V1)

    assert result["service_name"] == "image-generate-mcp-remote"
    assert len(result["tools"]) == 4
