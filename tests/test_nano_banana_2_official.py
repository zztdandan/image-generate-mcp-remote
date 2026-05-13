import base64
from pathlib import Path

import pytest

from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.models.common import ImageToolMode, ToolVersion
from image_generate_mcp_remote.tools.nano_banana_2_official import (
    NanoBananaAspectRatio,
    NanoBananaImageSize,
    ResponseModality,
    nano_banana_2_official_edit,
    nano_banana_2_official_generate,
)


class DummyResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = "dummy"

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def json(self) -> dict[str, object]:
        return self._payload


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_nano_generate_builds_text_only_payload(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        image_payload = base64.b64encode(b"nano-image").decode("utf-8")
        return DummyResponse(
            {
                "responseId": "resp-1",
                "candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": image_payload}}]}}],
            }
        )

    monkeypatch.setattr("image_generate_mcp_remote.tools.nano_banana_2_official.httpx.post", fake_post)

    result = nano_banana_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="make a fox",
        response_modalities=[ResponseModality.IMAGE],
        aspect_ratio=NanoBananaAspectRatio.SQUARE,
        image_size=NanoBananaImageSize.SIZE_1K,
    )

    assert captured["url"] == "https://api.apiyi.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"
    assert captured["headers"] == {"Content-Type": "application/json", "x-goog-api-key": "secret-key"}
    assert captured["json"]["contents"] == [{"parts": [{"text": "make a fox"}]}]
    assert captured["json"]["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert Path(result.file_path).exists()


def test_nano_edit_builds_text_plus_inline_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")
    source_path = tmp_path / "edit.png"
    source_path.write_bytes(b"edit-source")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["json"] = json
        image_payload = base64.b64encode(b"nano-edit").decode("utf-8")
        return DummyResponse(
            {
                "responseId": "resp-2",
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "done"},
                                {"inlineData": {"mimeType": "image/jpeg", "data": image_payload}},
                            ]
                        }
                    }
                ],
            }
        )

    monkeypatch.setattr("image_generate_mcp_remote.tools.nano_banana_2_official.httpx.post", fake_post)

    result = nano_banana_2_official_edit(
        version=ToolVersion.V1,
        mode=ImageToolMode.EDIT,
        prompt="add a hat",
        input_images=[{"source_type": "path", "path": str(source_path)}],
        response_modalities=[ResponseModality.IMAGE, ResponseModality.TEXT],
    )

    parts = captured["json"]["contents"][0]["parts"]
    assert parts[0] == {"text": "add a hat"}
    assert "inlineData" in parts[1]
    assert result.mime_type == "image/jpeg"
    assert result.text_output == "done"


def test_nano_rejects_missing_image_modality(monkeypatch):
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")

    with pytest.raises(ValueError):
        nano_banana_2_official_generate(
            version=ToolVersion.V1,
            mode=ImageToolMode.GENERATE,
            prompt="text only",
            response_modalities=[ResponseModality.TEXT],
        )
