"""OpenAI Images protocol — generate & edit via REST.

Protocol: POST {base_url}/images/generations  (generate)
          POST {base_url}/images/edits        (edit, multipart)
Auth:     Authorization: Bearer {api_key}
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
    """Send HTTP request with retry on transient errors."""
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
    prompt: str,
    size: str = "1024x1024",
    n: int = 1,
    response_format: str = "b64_json",
) -> dict:
    """Call POST /images/generations, return parsed JSON response."""
    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"prompt": prompt, "size": size, "n": n, "response_format": response_format}
    return _api_request(url, headers, json.dumps(body).encode("utf-8"))


def edit(
    base_url: str,
    api_key: str,
    image_path: str,
    prompt: str,
    mask_path: str | None = None,
    size: str = "1024x1024",
    n: int = 1,
    response_format: str = "b64_json",
) -> dict:
    """Call POST /images/edits (multipart), return parsed JSON response."""
    import mimetypes

    url = f"{base_url.rstrip('/')}/images/edits"
    boundary = f"----img_gen_{int(time.time() * 1000)}"

    parts: list[bytes] = []
    for field_name, file_path in [("image", image_path)] + (
        [("mask", mask_path)] if mask_path else []
    ):
        path = Path(file_path)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
            + path.read_bytes()
            + b"\r\n"
        )

    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="prompt"\r\n\r\n'
        f"{prompt}\r\n".encode("utf-8")
    )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="size"\r\n\r\n'
        f"{size}\r\n".encode("utf-8")
    )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="n"\r\n\r\n'
        f"{n}\r\n".encode("utf-8")
    )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="response_format"\r\n\r\n'
        f"{response_format}\r\n".encode("utf-8")
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    body = b"\r\n".join(parts) if False else b"".join(parts)  # noqa
    # Re-assemble cleanly
    body = b"".join(parts)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return _api_request(url, headers, body)


def save_image(response: dict, save_path: str) -> list[str]:
    """Extract base64 images from response and save to disk.

    Returns list of saved file paths.
    """
    data_list = response.get("data", [])
    saved = []
    for idx, item in enumerate(data_list):
        b64_str = item.get("b64_json", "")
        if not b64_str:
            continue
        raw = base64.b64decode(b64_str)
        out = Path(save_path)
        if len(data_list) > 1:
            stem, suf = out.stem, out.suffix
            out = out.with_name(f"{stem}_{idx}{suf}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        saved.append(str(out))
    return saved
