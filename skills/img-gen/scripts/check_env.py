#!/usr/bin/env python3
"""Standalone env check — detects GPT and Banana image generation configuration
from OS environment variables.

Usage:
  python3 scripts/check_env.py

Exits 0 if at least one API key is configured, 1 otherwise.
Prints configuration status (without secret values).
"""

from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here / "lib"))

import presets


def _ok(val) -> str:
    return "✓" if val else "✗"


def main() -> int:
    gpt = presets.detect_gpt_config()
    banana = presets.detect_banana_config()

    gpt_ok = bool(gpt and gpt["api_key"])
    banana_ok = bool(banana and banana["api_key"])

    print("img-gen env check (OS environment variables)")
    print()

    # ── GPT Image 2 ──
    print("GPT Image 2:")
    print(f"  available    : {_ok(gpt_ok)}")
    print(f"  api_key      : {_ok(gpt_ok)} ({'set' if gpt_ok else 'not set'})")
    print(f"  preset       : {gpt.get('preset_id') or '—' if gpt else '—'}")
    print(f"  base_url     : {gpt.get('base_url') or '—' if gpt else '—'}")
    print(f"  model        : {gpt.get('model') or '—' if gpt else '—'}")
    print()

    # ── Nano Banana 2 ──
    print("Nano Banana 2:")
    print(f"  available    : {_ok(banana_ok)}")
    print(f"  api_key      : {_ok(banana_ok)} ({'set' if banana_ok else 'not set'})")
    print(f"  preset       : {banana.get('preset_id') or '—' if banana else '—'}")
    print(f"  base_url     : {banana.get('base_url') or '—' if banana else '—'}")
    print(f"  model        : {banana.get('model') or '—' if banana else '—'}")
    print()

    print(f"Output dir: {presets.get_output_dir()}")
    print()

    available_channels: list[str] = []
    if gpt_ok:
        available_channels.append("gpt")
    if banana_ok:
        available_channels.append("banana")
    print(f"Available channels: {', '.join(available_channels) if available_channels else 'none'}")

    if not gpt_ok and not banana_ok:
        print()
        print("ERROR: No API key found in environment variables.")
        print("Required environment variables:")
        print("  IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY")
        print("  IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY")
        print("Optional (set at least one):")
        print("  IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET")
        print("  IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET")
        print("  IMAGE_OUTPUT_DIR")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
