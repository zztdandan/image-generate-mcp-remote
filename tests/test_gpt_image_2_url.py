from pathlib import Path

import httpx
import pytest

from image_generate_mcp_remote.config import get_settings
from image_generate_mcp_remote.models.common import ToolVersion
from image_generate_mcp_remote.tools.gpt_image_2_url import GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL, gpt_image_2_url_generate


class DummyPostResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = "dummy"
        self.headers: dict[str, str] = {"Content-Type": "application/json"}

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    def json(self) -> dict[str, object]:
        return self._payload


class DummyDownloadResponse:
    def __init__(self, content: bytes, status_code: int = 200, mime_type: str = "image/png"):
        self.content = content
        self.status_code = status_code
        self.text = "download"
        self.headers: dict[str, str] = {"Content-Type": mime_type}

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_gpt_image_2_url_generates_then_downloads(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_URL_API_KEY", "secret-key")
    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return DummyPostResponse(
            {
                "created": 789,
                "data": [{"url": "https://cdn.example.com/generated.png"}],
                "usage": {"input_tokens": 12, "output_tokens": 34, "total_tokens": 46},
            }
        )

    def fake_get(url: str, timeout: float, follow_redirects: bool):
        captured["download_url"] = url
        captured["download_timeout"] = timeout
        captured["follow_redirects"] = follow_redirects
        return DummyDownloadResponse(b"png-bytes")

    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.post", fake_post)
    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.get", fake_get)

    result = gpt_image_2_url_generate(
        version=ToolVersion.V1,
        prompt="draw dogs",
        save_path=str(tmp_path / "dogs.png"),
        model="gpt-image-2-vip",
        image=["https://example.com/ref.png"],
        size="3840x2160",
    )

    assert captured["url"] == "https://www.right.codes/draw/v1/images/generations"
    assert captured["headers"] == {"Authorization": "Bearer secret-key", "Content-Type": "application/json"}
    assert captured["json"] == {
        "model": "gpt-image-2-vip",
        "prompt": "draw dogs",
        "image": ["https://example.com/ref.png"],
        "size": "3840x2160",
        "response_format": "url",
    }
    assert captured["download_url"] == "https://cdn.example.com/generated.png"
    assert Path(result.file_path).exists()
    assert result.file_path.endswith("dogs.png")
    assert result.image_uri.startswith("file://")
    assert result.mime_type == "image/png"
    assert result.usage is not None
    assert result.usage.total_tokens == 46
    assert result.provider_response_excerpt == {
        "created": "789",
        "source_url": "https://cdn.example.com/generated.png",
    }


def test_gpt_image_2_url_rejects_unknown_size(monkeypatch):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_URL_API_KEY", "secret-key")

    with pytest.raises(ValueError):
        gpt_image_2_url_generate(
            version=ToolVersion.V1,
            prompt="bad size",
            save_path="/tmp/bad-size.png",
            size="1024x1024",
        )


def test_gpt_image_2_url_accepts_verified_size(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_URL_API_KEY", "secret-key")

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        return DummyPostResponse(
            {
                "created": 123,
                "data": [{"url": "https://cdn.example.com/verified.png"}],
                "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            }
        )

    def fake_get(url: str, timeout: float, follow_redirects: bool):
        return DummyDownloadResponse(b"png-bytes")

    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.post", fake_post)
    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.get", fake_get)

    verified_size = "2048x1152"
    assert verified_size in GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL

    result = gpt_image_2_url_generate(
        version=ToolVersion.V1,
        prompt="verified size",
        save_path=str(tmp_path / "verified-size.png"),
        size=verified_size,
    )

    assert result.file_path.endswith("verified-size.png")


def test_gpt_image_2_url_rejects_unverified_shared_size(monkeypatch):
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_URL_API_KEY", "secret-key")

    rejected_size = "2048x1360"
    assert rejected_size not in GPT_IMAGE_2_URL_ALLOWED_SIZE_POOL

    with pytest.raises(ValueError, match="verified gpt-image-2-url size pool"):
        gpt_image_2_url_generate(
            version=ToolVersion.V1,
            prompt="unverified size",
            save_path="/tmp/unverified-size.png",
            size=rejected_size,
        )


def test_gpt_image_2_url_retries_then_succeeds(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("IMAGE_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("IMG_GEN_GPT_IMAGE_2_URL_API_KEY", "secret-key")
    calls = {"post": 0}

    def flaky_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: float):
        calls["post"] += 1
        if calls["post"] < 3:
            raise httpx.RequestError("flaky network")
        return DummyPostResponse(
            {
                "created": 999,
                "data": [{"url": "https://cdn.example.com/retry-success.png"}],
                "usage": {"total_tokens": 7},
            }
        )

    def fake_get(url: str, timeout: float, follow_redirects: bool):
        return DummyDownloadResponse(b"png-bytes")

    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.post", flaky_post)
    monkeypatch.setattr("image_generate_mcp_remote.tools.gpt_image_2_url.httpx.get", fake_get)

    result = gpt_image_2_url_generate(
        version=ToolVersion.V1,
        prompt="retry",
        save_path=str(tmp_path / "retry.png"),
        size="2048x1152",
    )

    assert calls["post"] == 3
    assert Path(result.file_path).exists()
