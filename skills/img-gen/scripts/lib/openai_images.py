"""OpenAI Images protocol — generate & edit via REST.

Protocol: POST {base_url}/images/generations  (generate)
          POST {base_url}/images/edits        (edit, multipart)
Auth:     Authorization: Bearer {api_key}

Notes baked in from the apiyi docs (2026-10):
  * the image endpoints are synchronous — there is no task id. A client-side
    disconnect still gets billed, so the default timeout is 360 s.
  * `response_format` is always sent explicitly (`b64_json` default) because
    the historical default flipped between url and b64_json per group/load.
  * `data[]` entries carry either `url` or `b64_json`; both are handled.
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from urllib import request, error as urllib_error

DEFAULT_TIMEOUT = 360.0


def _api_request(
    url: str,
    headers: dict,
    data: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = 1,
) -> dict:
    """Send an HTTP request with retry on transient errors.

    5xx and saturation-style 429s are retried with exponential backoff.
    Quota 403s and parameter 400s are raised immediately: retrying them only
    burns time (and, on image endpoints, money).
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = request.Request(url, data=data, headers=headers)
            with request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib_error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            retryable = e.code >= 500
            if e.code == 429 and "饱和" in body:
                retryable = True
            if retryable and attempt < retries:
                time.sleep(2 ** attempt)
                last_exc = RuntimeError(f"HTTP {e.code}: {body}")
                continue
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                last_exc = e
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
    model: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Call POST /images/generations, return parsed JSON response.

    `model` MUST be sent: relay gateways default to dall-e-2 when it is
    omitted and then reject the request with "no available channels for
    model dall-e-2".

    `n` is deliberately kept at 1: the -vip models bill `n=3` as three
    images but still return one, so the CLI never sends more than 1.

    `quality` is optional and ONLY sent when non-empty. GPT-image-2.5 accepts
    low/medium/high/xhigh/max/auto; gpt-image-2 accepts low/medium/high/auto.
    Do NOT send an empty quality string — upstream 400s on unsupported values.

    `background` ("transparent" | "opaque" | "auto") and `output_format`
    ("png" | "webp" | "jpeg") are optional and only sent when set. GPT-image-2.5
    honours background="transparent" with output_format="png" and returns a real
    alpha channel; gpt-image-2 may ignore it.
    """
    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"prompt": prompt, "size": size, "n": n, "response_format": response_format}
    if model:
        body["model"] = model
    if quality:
        body["quality"] = quality
    if background:
        body["background"] = background
    if output_format:
        body["output_format"] = output_format
    return _api_request(url, headers, json.dumps(body).encode("utf-8"), timeout=timeout)


def edit(
    base_url: str,
    api_key: str,
    image_path: str,
    prompt: str,
    mask_path: str | None = None,
    size: str | None = None,
    n: int = 1,
    response_format: str = "b64_json",
    model: str | None = None,
    quality: str | None = None,
    background: str | None = None,
    output_format: str | None = None,
    input_fidelity: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Call POST /images/edits (multipart), return parsed JSON response.

    `model` MUST be sent: relay gateways fall back to dall-e-2 when it is
    omitted and reject the request with "no available channels for model
    dall-e-2".

    `size` is optional: omit (None) to let the gateway keep the input image size.
    Some gates reject sizes they don't support, so only send when explicitly
    provided. On the -vip table30 presets, always pass an explicit slot when a
    2K result is required: apiyi otherwise falls back to a ~1120 px long edge.

    `quality` is optional and ONLY sent when non-empty (same rule as generate:
    gpt-image-2.5 accepts low/medium/high/xhigh/max/auto). Do NOT send an empty
    quality string — upstream 400s on unsupported values.

    `background` / `output_format` mirror generate(); `input_fidelity` exists
    for API compatibility but the apiyi docs say not to send it, so it is
    omitted unless explicitly provided.
    """
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

    def add_text(name: str, value: str) -> None:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )

    add_text("prompt", prompt)
    if model:
        add_text("model", model)
    if size:
        add_text("size", size)
    if quality:
        add_text("quality", quality)
    if background:
        add_text("background", background)
    if output_format:
        add_text("output_format", output_format)
    if input_fidelity:
        add_text("input_fidelity", input_fidelity)
    add_text("n", str(n))
    add_text("response_format", response_format)
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(parts)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return _api_request(url, headers, body, timeout=timeout)


def _download(url: str, out: Path, timeout: float = 120.0) -> None:
    """Fetch a url-form image immediately (those links expire in ~24 h)."""
    req = request.Request(url, headers={"User-Agent": "img-gen/2.3"})
    with request.urlopen(req, timeout=timeout) as resp:
        out.write_bytes(resp.read())


def save_image(response: dict, save_path: str) -> list[str]:
    """Extract images from the response and save them to disk.

    Handles both `b64_json` (optionally with a `data:` prefix — historical
    relay versions differed) and `url` (downloaded right away, since CDN
    links expire ~24 h). Returns the list of saved file paths, and also
    attaches `_saved` to the response for callers that want the paths.
    """
    data_list = response.get("data", []) or []
    saved: list[str] = []
    for idx, item in enumerate(data_list):
        out = Path(save_path)
        if len(data_list) > 1:
            stem, suf = out.stem, out.suffix
            out = out.with_name(f"{stem}_{idx}{suf}")
        out.parent.mkdir(parents=True, exist_ok=True)

        b64_str = item.get("b64_json") or ""
        if b64_str:
            if b64_str.startswith("data:"):
                b64_str = b64_str.split(",", 1)[1]
            out.write_bytes(base64.b64decode(b64_str))
            saved.append(str(out))
            continue

        url = item.get("url") or ""
        if url:
            _download(url, out)
            saved.append(str(out))

    response["_saved"] = saved
    return saved
