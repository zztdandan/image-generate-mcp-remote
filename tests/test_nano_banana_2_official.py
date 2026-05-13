import base64
from pathlib import Path

import pytest

from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.models.common import ImageToolMode, ToolVersion
from image_generate_mcp_remote.tools.nano_banana_2_official import (
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


PNG_1X1_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q1fQAAAAASUVORK5CYII="
)


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
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
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
        save_path=str(tmp_path / "nano.png"),
        size="1024x1024",
        response_modalities=[ResponseModality.IMAGE],
    )

    assert captured["url"] == "https://www.uocode.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"
    assert captured["headers"] == {"Content-Type": "application/json", "x-goog-api-key": "secret-key"}
    assert captured["json"]["contents"] == [{"parts": [{"text": "make a fox"}]}]
    assert captured["json"]["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert captured["json"]["generationConfig"]["imageConfig"] == {"aspectRatio": "1:1", "imageSize": "1K"}
    assert Path(result.file_path).exists()
    assert result.file_path.endswith("nano.png")
    assert result.elapsed_seconds >= 0
    assert result.width == 1
    assert result.height == 1


def test_nano_edit_builds_text_plus_inline_data(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")
    source_path = tmp_path / "edit.png"
    source_path.write_bytes(b"edit-source")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["json"] = json
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
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
        save_path=str(tmp_path / "nano-edit.jpg"),
        input_images=[{"source_type": "path", "path": str(source_path)}],
        size="3800x1700",
        response_modalities=[ResponseModality.IMAGE, ResponseModality.TEXT],
    )

    parts = captured["json"]["contents"][0]["parts"]
    assert parts[0] == {"text": "add a hat"}
    assert "inlineData" in parts[1]
    assert captured["json"]["generationConfig"]["imageConfig"] == {"aspectRatio": "21:9", "imageSize": "4K"}
    assert result.mime_type == "image/jpeg"
    assert result.text_output == "done"
    assert result.file_path.endswith("nano-edit.jpg")
    assert result.width == 1
    assert result.height == 1


def test_nano_rejects_missing_image_modality(monkeypatch):
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")

    with pytest.raises(ValueError):
        nano_banana_2_official_generate(
            version=ToolVersion.V1,
            mode=ImageToolMode.GENERATE,
            prompt="text only",
            save_path="/tmp/text-only.png",
            response_modalities=[ResponseModality.TEXT],
        )


def test_nano_rejects_malformed_size_with_supported_size_list(monkeypatch):
    monkeypatch.setenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY", "secret-key")

    with pytest.raises(ValueError, match="Supported size presets") as exc_info:
        nano_banana_2_official_generate(
            version=ToolVersion.V1,
            mode=ImageToolMode.GENERATE,
            prompt="bad size",
            save_path="/tmp/bad-size.png",
            size="1024*1024",
            response_modalities=[ResponseModality.IMAGE],
        )
    assert "1280x1280 (1K, 1:1)" in str(exc_info.value)
