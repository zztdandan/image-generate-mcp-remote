import base64
from pathlib import Path

from image_generate_mcp_remote.models.common import ImageRawResultType, ImageToolBase64AsyncResult, ToolVersion
from image_generate_mcp_remote.tools.gpt_image_2_temporary import gpt_image_2_temporary_generate


PNG_1X1_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q1fQAAAAASUVORK5CYII="
)


class DummyResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return {"data": [{"b64_json": image_payload}]}


def test_temporary_tool_returns_async_base64_ack_and_persists(monkeypatch, tmp_path: Path):
    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float) -> DummyResponse:
        return DummyResponse()

    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_temporary.httpx.post", fake_post)
    save_path = tmp_path / "temporary.png"

    result = gpt_image_2_temporary_generate(
        version=ToolVersion.V1,
        api_key="temporary-key",
        base_url="https://provider.example.com/v1",
        model="image-model",
        prompt="temporary",
        save_path=str(save_path),
    )

    assert isinstance(result, ImageToolBase64AsyncResult)
    assert result.raw_result_type is ImageRawResultType.BASE64
    assert result.estimated_file_size_bytes == len(PNG_1X1_BYTES)
    assert result.save_path == str(save_path)
    assert "source_url" not in result.model_dump(mode="json", exclude_none=True)
    assert save_path.exists()