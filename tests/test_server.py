from image_generate_mcp_remote.server import health_check


def test_health_check_reports_basic_status():
    result = health_check()

    assert result["status"] == "healthy"
    assert result["service"] == "image-generate-mcp-remote"
