import base64
from pathlib import Path

import httpx
import pytest

from image_generate_mcp_remote.contracts.image_size import ImageAspectRatio, ImageSizeTier
from image_generate_mcp_remote.contracts.presets import PresetToolName
from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.errors import ValidationError
from image_generate_mcp_remote.models.common import ImageToolMode, ToolVersion
from image_generate_mcp_remote.presets.loader import resolve_preset_for_tool
from image_generate_mcp_remote.tools.gpt_image_2_official import (
    GptImageBackground,
    GptImageCount,
    GptImageOutputFormat,
    GptImageQuality,
    gpt_image_2_official_edit,
    gpt_image_2_official_generate,
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


def test_gpt_generate_builds_json_request_and_saves_file(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-key")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 123, "data": [{"b64_json": image_payload}], "usage": {"total_tokens": 5}})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="draw a cat",
        save_path=str(tmp_path / "generated.png"),
        aspect_ratio=ImageAspectRatio.SQUARE,
        image_size=ImageSizeTier.SIZE_1K,
        quality=GptImageQuality.HIGH,
        output_format=GptImageOutputFormat.PNG,
        background=GptImageBackground.OPAQUE,
        n=GptImageCount.SINGLE,
    )

    assert captured["url"] == "https://api.openai.com/v1/images/generations"
    assert captured["headers"] == {"Authorization": "Bearer secret-key"}
    assert captured["json"] == {
        "prompt": "draw a cat",
        "model": "gpt-image-2",
        "size": "1280x1280",
        "quality": "high",
        "output_format": "png",
        "background": "opaque",
        "moderation": "auto",
        "n": 1,
    }
    assert Path(result.file_path).exists()
    assert result.file_path.endswith("generated.png")
    assert result.image_uri.startswith("file://")
    assert result.mime_type == "image/png"
    assert result.elapsed_seconds >= 0
    assert result.width == 1
    assert result.height == 1
    assert result.actual_size_verification is not None
    assert result.actual_size_verification.requested_image_size == ImageSizeTier.SIZE_1K
    assert result.actual_size_verification.requested_aspect_ratio == ImageAspectRatio.SQUARE
    assert result.actual_size_verification.expected_width == 1280
    assert result.actual_size_verification.expected_height == 1280
    assert result.actual_size_verification.actual_width == 1
    assert result.actual_size_verification.actual_height == 1
    assert result.actual_size_verification.is_consistent is False
    assert captured["timeout"] == 180


def test_gpt_generate_uses_active_laozhang_preset_dispatch(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "env-secret-key")
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET", "laozhang_gpt_image_2_default")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 777, "data": [{"b64_json": image_payload}]})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="draw a mug",
        save_path=str(tmp_path / "override.png"),
        aspect_ratio=ImageAspectRatio.WIDE_16_9,
        image_size=ImageSizeTier.SIZE_2K,
        quality=GptImageQuality.HIGH,
    )

    assert captured["url"] == "https://api.laozhang.ai/v1/images/generations"
    assert captured["headers"] == {"Authorization": "Bearer env-secret-key"}
    assert captured["json"] == {
        "prompt": (
            "draw a mug\n\n"
            "Provider parameter fallback requirements:\n"
            "- Target image size: 2048x1152.\n"
            "- Target image quality: high."
        ),
        "model": "gpt-image-2",
        "output_format": "png",
        "background": "auto",
        "moderation": "auto",
        "n": 1,
    }
    assert result.provider_model == "gpt-image-2"


def test_gpt_generate_supports_per_call_preset_and_api_key_override(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "env-secret-key")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 778, "data": [{"b64_json": image_payload}]})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="draw a lantern",
        save_path=str(tmp_path / "override-per-call.png"),
        aspect_ratio=ImageAspectRatio.WIDE_16_9,
        image_size=ImageSizeTier.SIZE_2K,
        quality=GptImageQuality.HIGH,
        preset="laozhang_gpt_image_2_default",
        api_key="request-secret-key",
    )

    assert captured["url"] == "https://api.laozhang.ai/v1/images/generations"
    assert captured["headers"] == {"Authorization": "Bearer request-secret-key"}
    assert captured["timeout"] == 180
    assert "Target image size: 2048x1152." in captured["json"]["prompt"]
    assert result.file_path.endswith("override-per-call.png")


def test_gpt_generate_rejects_preset_override_without_api_key(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "env-secret-key")

    with pytest.raises(ValidationError, match="preset override requires api_key"):
        gpt_image_2_official_generate(
            version=ToolVersion.V1,
            mode=ImageToolMode.GENERATE,
            prompt="draw a lantern",
            save_path=str(tmp_path / "invalid.png"),
            preset="laozhang_gpt_image_2_default",
        )


def test_gpt_generate_downloads_url_response(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-key")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["post_url"] = url
        return DummyResponse({"created": 321, "data": [{"url": "https://cdn.example.com/generated.png"}]})

    def fake_get(url: str, timeout: float, follow_redirects: bool):
        captured["download_url"] = url
        captured["download_timeout"] = timeout
        captured["follow_redirects"] = follow_redirects
        return DummyResponse({})

    fake_get_response = type(
        "FakeDownloadResponse",
        (),
        {
            "__init__": lambda self: None,
            "content": PNG_1X1_BYTES,
            "status_code": 200,
            "text": "download",
            "headers": {"Content-Type": "image/png"},
            "is_error": False,
        },
    )

    def fake_get_with_image(url: str, timeout: float, follow_redirects: bool):
        captured["download_url"] = url
        captured["download_timeout"] = timeout
        captured["follow_redirects"] = follow_redirects
        return fake_get_response()

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)
    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.get", fake_get_with_image)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="draw from url response",
        save_path=str(tmp_path / "from-url.png"),
    )

    assert captured["post_url"] == "https://api.openai.com/v1/images/generations"
    assert captured["download_url"] == "https://cdn.example.com/generated.png"
    assert captured["download_timeout"] == 180
    assert captured["follow_redirects"] is True
    assert result.file_path.endswith("from-url.png")
    assert result.provider_response_excerpt == {
        "created": "321",
        "source_url": "https://cdn.example.com/generated.png",
    }


def test_gpt_edit_builds_multipart_request_with_mask(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-key")
    source_path = tmp_path / "input.png"
    source_path.write_bytes(b"image-1")
    mask_base64 = base64.b64encode(b"mask-1").decode("utf-8")
    captured: dict[str, object] = {}

    def fake_post(
        url: str,
        headers: dict[str, str],
        data: dict[str, str],
        files: list[tuple[str, tuple[str, bytes, str]]],
        timeout: float,
    ):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        captured["files"] = files
        captured["timeout"] = timeout
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 456, "data": [{"b64_json": image_payload}]})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)

    result = gpt_image_2_official_edit(
        version=ToolVersion.V1,
        mode=ImageToolMode.EDIT,
        prompt="edit this",
        save_path=str(tmp_path / "edited.webp"),
        images=[{"source_type": "path", "path": str(source_path)}],
        mask={"source_type": "base64", "data_base64": mask_base64, "filename": "mask.png", "mime_type": "image/png"},
        output_format=GptImageOutputFormat.WEBP,
    )

    assert captured["url"] == "https://api.openai.com/v1/images/edits"
    assert captured["data"]["prompt"] == "edit this"
    assert captured["data"]["output_format"] == "webp"
    assert captured["files"][0][0] == "image[]"
    assert captured["files"][0][1][0] == "input.png"
    assert captured["files"][1][0] == "mask"
    assert captured["timeout"] == 180
    assert result.mime_type == "image/webp"
    assert result.file_path.endswith("edited.webp")
    assert result.width == 1
    assert result.height == 1


def test_gpt_generate_builds_provider_size_from_enums(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-key")
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))

    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["json"] = json
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 999, "data": [{"b64_json": image_payload}]})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", fake_post)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="wide size",
        save_path=str(tmp_path / "bad-size.png"),
        aspect_ratio=ImageAspectRatio.WIDE_16_9,
        image_size=ImageSizeTier.SIZE_2K,
    )

    assert captured["json"]["size"] == "2048x1152"
    assert result.file_path.endswith("bad-size.png")


def test_gpt_generate_retries_then_succeeds(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY", "secret-key")
    calls = {"post": 0}

    def flaky_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        calls["post"] += 1
        if calls["post"] < 4:
            raise httpx.RequestError("flaky network")
        image_payload = base64.b64encode(PNG_1X1_BYTES).decode("utf-8")
        return DummyResponse({"created": 123, "data": [{"b64_json": image_payload}]})

    monkeypatch.setattr("image_generate_mcp_remote.presets.base.httpx.post", flaky_post)

    result = gpt_image_2_official_generate(
        version=ToolVersion.V1,
        mode=ImageToolMode.GENERATE,
        prompt="retry",
        save_path=str(tmp_path / "retry.png"),
    )

    assert calls["post"] == 4
    assert result.file_path.endswith("retry.png")


def test_laozhang_vip_preset_uses_240s_timeout_and_single_retry():
    resolved = resolve_preset_for_tool(PresetToolName.GPT_IMAGE_2_OFFICIAL, "laozhang_gpt_image_2_vip").resolve()

    assert resolved.config.runtime.timeout_seconds == 240
    assert resolved.config.runtime.retry_count == 1
