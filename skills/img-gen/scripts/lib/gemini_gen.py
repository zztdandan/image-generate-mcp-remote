"""Gemini generateContent protocol — generate & edit via REST.

Protocol: POST {base_url}/v1beta/models/{model}:generateContent
Auth:     Authorization: Bearer {api_key}
Response: candidates[].content.parts[].inlineData (base64)
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from urllib import request, error as urllib_error


def _api_request(
    url: str,
    headers: dict,
    data: bytes | None = None,
    timeout: float = 150.0,
    retries: int = 1,
) -> dict:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            req = request.Request(url, data=data, headers=headers)
            with request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib_error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code and 500 <= e.code < 600 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            last_exc = RuntimeError(f"HTTP {e.code}: {body}")
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            last_exc = e
    raise last_exc or RuntimeError("request failed")


def generate(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    image_size: str = "1K",
    aspect_ratio: str = "1:1",
) -> dict:
    """Call Gemini generateContent for text-to-image.

    The size and ratio are appended to the prompt text as instructions.
    """
    url = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }
    return _api_request(url, headers, json.dumps(body).encode("utf-8"))


def edit(
    base_url: str,
    api_key: str,
    model: str,
    image_path: str,
    prompt: str,
) -> dict:
    """Call Gemini generateContent for image-to-image editing.

    Sends the input image as base64 inline data alongside the text prompt.
    """
    import mimetypes

    path_obj = Path(image_path)
    mime = mimetypes.guess_type(path_obj.name)[0] or "image/png"
    b64 = base64.b64encode(path_obj.read_bytes()).decode("utf-8")

    url = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime, "data": b64}},
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }
    return _api_request(url, headers, json.dumps(body).encode("utf-8"))


def save_image(response: dict, save_path: str) -> list[str]:
    """Extract inlineData images from Gemini response candidates.

    Returns list of saved file paths.
    """
    saved = []
    candidates = response.get("candidates", [])
    for cand_idx, cand in enumerate(candidates):
        parts = cand.get("content", {}).get("parts", [])
        for part_idx, part in enumerate(parts):
            inline = part.get("inlineData", {})
            data_b64 = inline.get("data", "")
            mime_type = inline.get("mimeType", "image/png")
            if not data_b64:
                continue
            raw = base64.b64decode(data_b64)
            out = Path(save_path)
            if len(candidates) > 1 or len(parts) > 1:
                stem, suf = out.stem, out.suffix
                out = out.with_name(f"{stem}_c{cand_idx}_p{part_idx}{suf}")
            # Guess extension from mime
            ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
            if out.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                out = out.with_suffix(ext_map.get(mime_type, ".png"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
            saved.append(str(out))
    return saved
