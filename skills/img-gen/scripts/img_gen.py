#!/usr/bin/env python3
"""img-gen — Unified CLI for GPT Image 2 and Nano Banana 2 generation.

Reads API keys from OS environment variables.

Usage:
  python3 scripts/img_gen.py check
  python3 scripts/img_gen.py generate --preset <id> --prompt "..." --save out.png
  python3 scripts/img_gen.py edit --preset <id> --image in.png --prompt "..." --save out.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here / "lib"))

import presets
import openai_images as gpt_api
import gemini_gen as banana_api


# ── CLI ─────────────────────────────────────────────────────────────

def _parse_args():
    ap = argparse.ArgumentParser(description="Direct image generation via GPT / Banana APIs (.env-based)")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("check", help="Check .env configuration")

    gen = sub.add_parser("generate", help="Generate an image from text prompt")
    gen.add_argument("--preset", required=True, help="Preset ID")
    gen.add_argument("--prompt", required=True, help="Text prompt")
    gen.add_argument("--save", required=True, help="Output file path")
    gen.add_argument("--size", default="2K", choices=presets.VALID_SIZES)
    gen.add_argument("--ratio", default="16:9", choices=presets.VALID_RATIOS)

    ed = sub.add_parser("edit", help="Edit an existing image")
    ed.add_argument("--preset", required=True)
    ed.add_argument("--image", required=True)
    ed.add_argument("--prompt", required=True)
    ed.add_argument("--save", required=True)
    ed.add_argument("--mask", default=None)
    ed.add_argument("--size", default="2K", choices=presets.VALID_SIZES)
    ed.add_argument("--ratio", default="16:9", choices=presets.VALID_RATIOS)

    return ap.parse_args()


def _resolve_config(preset_id: str) -> dict:
    p = presets.PRESETS.get(preset_id)
    if not p:
        ids = "\n  ".join(presets.PRESETS)
        raise SystemExit(f"Unknown preset: {preset_id}\nAvailable:\n  {ids}")

    if p.protocol == "openai_images":
        cfg = presets.detect_gpt_config()
    else:
        cfg = presets.detect_banana_config()

    if not cfg or not cfg["api_key"]:
        family = p.env_key_family.upper()
        env_var = (
            "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY"
            if p.env_key_family == "gpt"
            else "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY"
        )
        raise SystemExit(
            f"No {family} API key in environment.\n"
            f"Set environment variable: {env_var}"
        )

    return {
        "preset": p,
        "base_url": cfg["base_url"] or p.base_url,
        "model": p.default_model,
        "api_key": cfg["api_key"],
    }


def cmd_check():
    print("=" * 60)
    print("img-gen env check (OS environment variables)")
    print("=" * 60)

    gpt = presets.detect_gpt_config()
    banana = presets.detect_banana_config()

    def _o(v): return "✓" if v else "✗"
    print(f"\n  GPT   : KEY={_o(gpt and gpt['api_key'])}  "
          f"PRESET={gpt.get('preset_id') or '—' if gpt else '—'}  "
          f"BASE={gpt.get('base_url') or '—' if gpt else '—'}")
    print(f"  Banana: KEY={_o(banana and banana['api_key'])}  "
          f"PRESET={banana.get('preset_id') or '—' if banana else '—'}  "
          f"BASE={banana.get('base_url') or '—' if banana else '—'}")

    available = presets.list_available_presets()
    print(f"\n  Available ({len(available)}):")
    for pid in available:
        p = presets.PRESETS[pid]
        print(f"    {pid:45s} {p.base_url} [{p.default_model}]")

    print(f"\n  All ({len(presets.PRESETS)}):")
    for pid, p in presets.PRESETS.items():
        mark = "✓" if pid in available else "—"
        print(f"    {mark} {pid:45s} {p.provider:12s} {p.base_url}")


def cmd_generate(args):
    cfg = _resolve_config(args.preset)
    p = cfg["preset"]
    print(f"[generate] preset={args.preset}  size={args.size}  ratio={args.ratio}")

    if p.protocol == "openai_images":
        w, h = presets.resolve_size(args.size, args.ratio, "openai_images")
        size_str = f"{w}x{h}"
        print(f"  -> {cfg['base_url']}  model={cfg['model']}  size={size_str}")
        resp = gpt_api.generate(cfg["base_url"], cfg["api_key"], args.prompt, size=size_str)
        saved = gpt_api.save_image(resp, args.save)
    else:
        w, h = presets.resolve_size(args.size, args.ratio, "gemini_generate_content")
        print(f"  -> {cfg['base_url']}  model={cfg['model']}  resolution={w}x{h}")
        resp = banana_api.generate(cfg["base_url"], cfg["api_key"], cfg["model"], args.prompt)
        saved = banana_api.save_image(resp, args.save)

    print(f"  saved: {saved}")


def cmd_edit(args):
    cfg = _resolve_config(args.preset)
    p = cfg["preset"]
    print(f"[edit] preset={args.preset}  image={args.image}")

    if p.protocol == "openai_images":
        w, h = presets.resolve_size(args.size, args.ratio, "openai_images")
        size_str = f"{w}x{h}"
        resp = gpt_api.edit(cfg["base_url"], cfg["api_key"], args.image, args.prompt,
                            mask_path=args.mask, size=size_str)
        saved = gpt_api.save_image(resp, args.save)
    else:
        resp = banana_api.edit(cfg["base_url"], cfg["api_key"], cfg["model"],
                               args.image, args.prompt)
        saved = banana_api.save_image(resp, args.save)

    print(f"  saved: {saved}")


def main():
    args = _parse_args()
    if args.command == "check":
        cmd_check()
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "edit":
        cmd_edit(args)
    else:
        # argparse already enforces, but handle edge case
        sys.exit("unknown command")


if __name__ == "__main__":
    main()
