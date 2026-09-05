"""Preset catalog — every registered preset from image-generate-mcp-remote.

Reads configuration from OS environment variables:
  GPT family:
    IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY
    IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET
  Banana family:
    IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY
    IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET
  General:
    IMAGE_OUTPUT_DIR
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def dotenv(key: str, default: str = "") -> str:
    """Read a value from OS environment variables."""
    return os.environ.get(key, default)


# ── Data model ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class Preset:
    preset_id: str
    provider: str
    protocol: str  # "openai_images" | "gemini_generate_content"
    base_url: str
    default_model: str
    modes: tuple[str, ...] = ("generate", "edit")
    stability: str = "stable"
    env_key_family: str = "gpt"  # "gpt" | "banana"


# ── All registered presets ──────────────────────────────────────────

PRESETS: dict[str, Preset] = {
    # ── GPT Image 2 presets (OpenAI Images protocol) ──
    "laozhang_gpt_image_2_vip": Preset(
        "laozhang_gpt_image_2_vip", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2-vip",
        stability="stable", env_key_family="gpt",
    ),
    "laozhang_gpt_image_2_default": Preset(
        "laozhang_gpt_image_2_default", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "laozhang_gpt_image_2_enterprise": Preset(
        "laozhang_gpt_image_2_enterprise", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "laozhang_gpt_image_2_sora_official": Preset(
        "laozhang_gpt_image_2_sora_official", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "openai_gpt_image_2": Preset(
        "openai_gpt_image_2", "openai", "openai_images",
        "https://api.openai.com/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "apiyi_gpt_image_2": Preset(
        "apiyi_gpt_image_2", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "right_codes_gpt_image_2": Preset(
        "right_codes_gpt_image_2", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "gpt-image-2",
        stability="stable", env_key_family="gpt",
    ),
    "right_codes_gpt_image_2_vip": Preset(
        "right_codes_gpt_image_2_vip", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "gpt-image-2-vip",
        stability="experimental", env_key_family="gpt",
    ),
    "right_codes_nano_with_image_api_images": Preset(
        "right_codes_nano_with_image_api_images", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "nano-banana-2",
        stability="stable", env_key_family="gpt",
    ),
    "copperai_gpt_image_2": Preset(
        "copperai_gpt_image_2", "copperai", "openai_images",
        "https://api.copperai.dev/v1", "gpt-image-2",
        stability="experimental", env_key_family="gpt",
    ),
    # ── Nano Banana 2 presets (Gemini generateContent protocol) ──
    "laozhang_nano_banana_pro": Preset(
        "laozhang_nano_banana_pro", "laozhang", "gemini_generate_content",
        "https://api.laozhang.ai", "gemini-3-pro-image-preview",
        stability="stable", env_key_family="banana",
    ),
    "apiyi_nano_banana_2": Preset(
        "apiyi_nano_banana_2", "apiyi", "gemini_generate_content",
        "https://api.apiyi.com", "gemini-3.1-flash-image-preview",
        stability="stable", env_key_family="banana",
    ),
    "google_nano_banana": Preset(
        "google_nano_banana", "google", "gemini_generate_content",
        "https://generativelanguage.googleapis.com", "gemini-3.1-flash-image-preview",
        stability="stable", env_key_family="banana",
    ),
}


# ── Size / aspect-ratio mapping ─────────────────────────────────────

SIZE_MAP: dict[str, dict[str, dict[str, int]]] = {
    "1K": {
        "1:1":  {"gpt": (1280, 1280), "nano": (1024, 1024)},
        "2:3":  {"gpt": (848, 1280),  "nano": (848, 1264)},
        "3:2":  {"gpt": (1280, 848),  "nano": (1264, 848)},
        "3:4":  {"gpt": (960, 1280),  "nano": (896, 1200)},
        "4:3":  {"gpt": (1280, 960),  "nano": (1200, 896)},
        "4:5":  {"gpt": (1024, 1280), "nano": (928, 1152)},
        "5:4":  {"gpt": (1280, 1024), "nano": (1152, 928)},
        "9:16": {"gpt": (720, 1280),  "nano": (768, 1376)},
        "16:9": {"gpt": (1280, 720),  "nano": (1376, 768)},
        "21:9": {"gpt": (1280, 544),  "nano": (1584, 672)},
    },
    "2K": {
        "1:1":  {"gpt": (2048, 2048), "nano": (2048, 2048)},
        "2:3":  {"gpt": (1360, 2048), "nano": (1696, 2528)},
        "3:2":  {"gpt": (2048, 1360), "nano": (2528, 1696)},
        "3:4":  {"gpt": (1536, 2048), "nano": (1792, 2400)},
        "4:3":  {"gpt": (2048, 1536), "nano": (2400, 1792)},
        "4:5":  {"gpt": (1632, 2048), "nano": (1856, 2304)},
        "5:4":  {"gpt": (2048, 1632), "nano": (2304, 1856)},
        "9:16": {"gpt": (1152, 2048), "nano": (1536, 2752)},
        "16:9": {"gpt": (2048, 1152), "nano": (2752, 1536)},
        "21:9": {"gpt": (2048, 864),  "nano": (3168, 1344)},
    },
    "4K": {
        "1:1":  {"gpt": (2880, 2880), "nano": (4096, 4096)},
        "2:3":  {"gpt": (2336, 3520), "nano": (3392, 5056)},
        "3:2":  {"gpt": (3520, 2336), "nano": (5056, 3392)},
        "3:4":  {"gpt": (2480, 3312), "nano": (3584, 4800)},
        "4:3":  {"gpt": (3312, 2480), "nano": (4800, 3584)},
        "4:5":  {"gpt": (2560, 3216), "nano": (3712, 4608)},
        "5:4":  {"gpt": (3216, 2560), "nano": (4608, 3712)},
        "9:16": {"gpt": (2160, 3840), "nano": (3072, 5504)},
        "16:9": {"gpt": (3840, 2160), "nano": (5504, 3072)},
        "21:9": {"gpt": (3840, 1632), "nano": (6336, 2688)},
    },
}

VALID_SIZES = list(SIZE_MAP.keys())
VALID_RATIOS = sorted(SIZE_MAP["1K"].keys())


def resolve_size(tier: str, ratio: str, protocol: str) -> tuple[int, int]:
    """Return (width, height) for the given tier + ratio + protocol."""
    key = "gpt" if protocol == "openai_images" else "nano"
    return SIZE_MAP[tier][ratio][key]


# ── Configuration detection (from OS env) ──────────────────────────

def detect_gpt_config() -> dict | None:
    """Detect GPT (OpenAI Images) configuration from OS environment variables."""
    api_key = dotenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY")
    preset_id = dotenv("IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET")
    if not api_key:
        return None
    preset = PRESETS.get(preset_id)
    base_url = dotenv("IMG_GEN_GPT_BASE_URL") or (preset.base_url if preset else "")
    return {
        "api_key": api_key,
        "preset_id": preset_id,
        "base_url": base_url,
        "model": preset.default_model if preset else None,
        "preset": preset,
        "ok": bool(base_url),
    }


def detect_banana_config() -> dict | None:
    """Detect Nano Banana (Gemini) configuration from OS environment variables."""
    api_key = dotenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY")
    preset_id = dotenv("IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET")
    if not api_key:
        return None
    preset = PRESETS.get(preset_id)
    base_url = dotenv("IMG_GEN_BANANA_BASE_URL") or (preset.base_url if preset else "")
    return {
        "api_key": api_key,
        "preset_id": preset_id,
        "base_url": base_url,
        "model": preset.default_model if preset else None,
        "preset": preset,
        "ok": bool(base_url),
    }


def get_output_dir() -> str:
    """Return the default image output directory."""
    return dotenv("IMAGE_OUTPUT_DIR") or os.path.expanduser("~/images")


def list_available_presets() -> list[str]:
    """Return which preset IDs have valid environment configuration."""
    available: list[str] = []
    for pid, p in PRESETS.items():
        if p.protocol == "openai_images":
            cfg = detect_gpt_config()
        else:
            cfg = detect_banana_config()
        if cfg and cfg["ok"]:
            available.append(pid)
    return available
