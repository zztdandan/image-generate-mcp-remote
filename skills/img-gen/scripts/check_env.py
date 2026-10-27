#!/usr/bin/env python3
"""Standalone env check — reports which GPT / Banana image generation channels are
configured in the current process environment.

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

    gpt_ok = gpt and gpt["api_key"]
    banana_ok = banana and banana["api_key"]

    print("img-gen env check")
    print(f"  GPT Image 2    : API_KEY={_ok(gpt_ok)}  "
          f"PRESET={gpt.get('preset_id') or '—' if gpt else '—'}  "
          f"BASE={gpt.get('base_url') or '—' if gpt else '—'}")
    print(f"  Nano Banana 2  : API_KEY={_ok(banana_ok)}  "
          f"PRESET={banana.get('preset_id') or '—' if banana else '—'}  "
          f"BASE={banana.get('base_url') or '—' if banana else '—'}")
    print(f"  OUTPUT_DIR     : {presets.get_output_dir()}")

    print("\n  Environment variables:")
    for name in presets.REQUIRED_ANY_OF:
        print(f"    {_ok(presets.env(name))} {name}  (required: at least one)")
    for name in presets.OPTIONAL_KEYS:
        value = presets.env(name)
        shown = f"  = {value}" if name in (
            "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET",
            "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET",
            "IMAGE_OUTPUT_DIR",
        ) and value else ""
        print(f"    {_ok(value)} {name}{shown}")

    available = presets.list_available_presets()
    if available:
        print(f"\n  Available presets ({len(available)}):")
        for pid in available:
            p = presets.PRESETS[pid]
            print(f"    {pid}  →  {p.base_url}  [{p.default_model}]")
    else:
        print("\n  No presets fully configured.")

    if not gpt_ok and not banana_ok:
        print("\n  ERROR: no image generation API key in the environment.")
        print(f"  {presets.ENV_SETUP_HINT}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
