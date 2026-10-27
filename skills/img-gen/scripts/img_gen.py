#!/usr/bin/env python3
"""img-gen — Unified CLI for GPT-Image and Nano Banana image generation.

Loads API keys from the process environment (no .env file is read).

Usage:
  python3 scripts/img_gen.py check
  python3 scripts/img_gen.py generate --preset auto --prompt "..." --save out.png
  python3 scripts/img_gen.py generate --preset laozhang_gpt_image_2_5_flare_vip \
      --prompt "..." --save out.png --size 2K --ratio 16:9 --quality low
  python3 scripts/img_gen.py edit --image in.png --prompt "..." --save out.png

`--preset auto` (the default) walks the $0.03/image flat chain and only falls
through on transport/quota/saturation errors. The expensive token-billed
official relay presets are reachable with `--allow-expensive` or by naming one
explicitly.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here / "lib"))

import presets
import openai_images as gpt_api
import gemini_gen as banana_api


# ── Error classification ────────────────────────────────────────────

def _http_code(exc: Exception) -> int | None:
    m = re.search(r"HTTP (\d{3})", str(exc))
    return int(m.group(1)) if m else None


def _should_fall_through(exc: Exception) -> bool:
    """True when trying the next preset in the auto chain is worthwhile.

    Quota (403), auth (401), saturation (429), 5xx and network/timeout errors
    are per-route problems → try the next route. A 400 means our parameters are
    wrong and every route would fail the same way → stop immediately.
    """
    code = _http_code(exc)
    if code is None:
        return True  # timeout / connection reset / json error
    if code == 400:
        return False
    return code in (401, 403, 404, 408, 409, 425, 429) or code >= 500


# ── CLI ─────────────────────────────────────────────────────────────

def _add_common(p, *, is_edit: bool) -> None:
    p.add_argument("--preset", default="auto",
                   help="Preset ID, or 'auto' (default) to walk the $0.03/image chain.")
    p.add_argument("--prompt", required=True, help="Text prompt")
    p.add_argument("--save", required=True, help="Output file path")
    p.add_argument("--quality", default=None,
                   choices=["auto", "low", "medium", "high", "xhigh", "max"],
                   help="Validated per preset: gpt-image-2(-vip) stops at 'high'; "
                        "2.5 models accept xhigh/max. Not sent when omitted.")
    p.add_argument("--timeout", type=float, default=gpt_api.DEFAULT_TIMEOUT,
                   help="HTTP timeout seconds (default 360). Image APIs are synchronous: "
                        "a disconnect still bills, so do not lower this casually.")
    p.add_argument("--response-format", default="b64_json", choices=["b64_json", "url"],
                   help="Always sent explicitly. 'url' links expire in ~24h; the CLI downloads "
                        "them immediately, so the saved file is still durable.")
    p.add_argument("--background", default=None, choices=["transparent", "opaque", "auto"],
                   help="'transparent' + --output-format png gives a real alpha PNG on 2.5 models.")
    p.add_argument("--output-format", default=None, choices=["png", "webp", "jpeg"],
                   help="Requested container format. Use png together with --background transparent.")
    p.add_argument("--allow-expensive", action="store_true",
                   help="Only with --preset auto: append the token-billed official-relay presets "
                        "after every cheap route has failed. Off by default on purpose.")

    if not is_edit:
        p.add_argument("--size", default="2K", choices=presets.VALID_SIZES)
        p.add_argument("--ratio", default="16:9", choices=presets.VALID_RATIOS)
        p.add_argument("--size-px", default=None, metavar="WxH",
                       help="Exact pixel size (must be one of the 30 documented slots). "
                            "Overrides --size/--ratio.")
    else:
        p.add_argument("--image", required=True)
        p.add_argument("--mask", default=None)
        p.add_argument("--size", default=None, metavar="WxH",
                       help="Explicit pixel size (e.g. 2048x1152). Omit to keep the input size — "
                            "but on apiyi table30 presets omitting it downgrades the result to "
                            "~1120 px long edge, so pass a slot when a 2K result is wanted.")


def _parse_args():
    ap = argparse.ArgumentParser(
        description="Direct image generation via GPT / Banana APIs (environment-variable based)")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("check", help="Check environment configuration and preset pricing")

    gen = sub.add_parser("generate", help="Generate an image from a text prompt")
    _add_common(gen, is_edit=False)

    ed = sub.add_parser("edit", help="Edit an existing image")
    _add_common(ed, is_edit=True)

    return ap.parse_args()


# ── Preset resolution / chain execution ────────────────────────────

def _require_preset(preset_id: str) -> presets.Preset:
    p = presets.PRESETS.get(preset_id)
    if not p:
        ids = "\n  ".join(presets.PRESETS)
        raise SystemExit(f"Unknown preset: {preset_id}\nAvailable:\n  {ids}")
    if not presets.resolve_preset_api_key(preset_id):
        raise SystemExit(
            f"Preset {preset_id} has no API key in the environment "
            f"(expected IMG_GEN_PRESET_{preset_id.upper()}_API_KEY or a provider/family key)."
        )
    if not presets.resolve_preset_base_url(preset_id):
        raise SystemExit(f"Preset {preset_id} has no base_url.")
    return p


def _describe_route(pid: str) -> str:
    p = presets.PRESETS[pid]
    price = p.cost_hint or presets.TIER_LABELS.get(p.tier, "varies")
    quality = "" if p.protocol != "openai_images" else f" quality≤{p.qualities[-1]}"
    return (f"{pid}  [{p.default_model}]  {price}"
            f"  tier={p.tier}{quality}  {p.base_url}")


def _warn_if_expensive(pid: str) -> None:
    p = presets.PRESETS[pid]
    if p.tier == "last_resort":
        print("  [!] LAST-RESORT ROUTE: this preset is token-billed (expensive). "
              "Use it only after every $0.03/image route failed.")


def _run_chain(args, protocol: str, run_once):
    """Run `run_once(preset)` over auto chain or a single preset."""
    if args.preset != "auto":
        p = _require_preset(args.preset)
        _warn_if_expensive(p.preset_id)
        return run_once(p), p.preset_id

    chain = presets.build_auto_chain(allow_expensive=args.allow_expensive, protocol=protocol)
    if not chain:
        raise SystemExit("No configured preset available for --preset auto.")

    print(f"[auto] cheap chain ({len(chain)}): {', '.join(chain)}")
    failures: list[str] = []
    for pid in chain:
        try:
            _warn_if_expensive(pid)
            return run_once(presets.PRESETS[pid]), pid
        except SystemExit:
            raise
        except Exception as e:
            if not _should_fall_through(e):
                raise
            msg = str(e).splitlines()[0][:200]
            print(f"  [warn] {pid} failed: {msg}")
            failures.append(f"{pid}: {msg}")

    hint = "" if args.allow_expensive else (
        "\nAll cheap $0.03/image routes failed. Re-run with --allow-expensive to try the "
        "token-billed official relay (materially more expensive).")
    raise SystemExit("Every auto-chain preset failed:\n  " + "\n  ".join(failures) + hint)


def _validate_for_preset(p: presets.Preset, size_px: str | None, quality: str | None) -> None:
    if p.protocol != "openai_images":
        return
    err = presets.validate_quality(p.preset_id, quality)
    if err:
        raise SystemExit(err)
    if size_px and p.size_policy == "table30":
        err = presets.check_size_table30(size_px)
        if err:
            raise SystemExit(err)


def _warn_input_size(image_path: str) -> None:
    try:
        size = Path(image_path).stat().st_size
    except OSError:
        return
    if size > 1.5 * 1024 * 1024:
        print(f"  [!] input is {size / 1048576:.1f} MB (>1.5 MB recommended): "
              "downscaling the reference can avoid shell_api_error / timeouts.")


# ── Commands ────────────────────────────────────────────────────────

def cmd_check():
    def _o(v): return "✓" if v else "✗"

    print("=" * 72)
    print("img-gen env check")
    print("=" * 72)
    print("  source: process environment (no .env file is read)")
    for name in presets.REQUIRED_ANY_OF:
        print(f"  {name}: {_o(presets.env(name))}")

    gpt = presets.detect_gpt_config()
    banana = presets.detect_banana_config()

    print(f"\n  GPT   : KEY={_o(gpt and gpt['api_key'])}  "
          f"PRESET={gpt.get('preset_id') or '—' if gpt else '—'}  "
          f"BASE={gpt.get('base_url') or '—' if gpt else '—'}")
    print(f"  Banana: KEY={_o(banana and banana['api_key'])}  "
          f"PRESET={banana.get('preset_id') or '—' if banana else '—'}  "
          f"BASE={banana.get('base_url') or '—' if banana else '—'}")

    available = presets.list_available_presets()
    cheap = presets.build_auto_chain()
    last = [pid for pid in presets.build_auto_chain(allow_expensive=True) if pid not in cheap]
    print(f"\n  Auto cheap chain: {', '.join(cheap) or '—'}")
    print(f"  Auto last resort: {', '.join(last) or '—'}")

    print(f"\n  Configured presets ({len(available)}):")
    for pid in available:
        p = presets.PRESETS[pid]
        price = p.cost_hint or presets.TIER_LABELS.get(p.tier, "varies")
        print(f"    {pid:42s} {p.tier:11s} {price:34s} {p.base_url}")

    if not available:
        print("  ERROR: no preset has an API key in the environment.")
        print(f"  {presets.ENV_SETUP_HINT}")
        return 1
    return 0


def cmd_generate(args):
    protocol = "openai_images"
    print(f"[generate] preset={args.preset}  size={args.size}  ratio={args.ratio}"
          + (f"  size_px={args.size_px}" if args.size_px else ""))

    def run_once(p):
        if p.protocol == "gemini_generate_content":
            if args.size_px:
                raise SystemExit("--size-px is only supported on OpenAI Images presets; "
                                 "use --size/--ratio for Banana.")
            w, h = presets.resolve_size(args.size, args.ratio, p.protocol)
            print(f"  -> {p.preset_id}  model={p.default_model}  resolution={w}x{h}")
            resp = banana_api.generate(
                presets.resolve_preset_base_url(p.preset_id),
                presets.resolve_preset_api_key(p.preset_id),
                p.default_model, args.prompt)
            saved = banana_api.save_image(resp, args.save)
            _report_saved(saved, resp)
            return resp

        w, h = presets.resolve_size(args.size, args.ratio, "openai_images")
        size_str = args.size_px or f"{w}x{h}"
        _validate_for_preset(p, size_str, args.quality)
        print(f"  -> {p.preset_id}  model={p.default_model}  size={size_str}"
              + (f"  quality={args.quality}" if args.quality else "")
              + (f"  background={args.background}" if args.background else "")
              + (f"  output_format={args.output_format}" if args.output_format else "")
              + f"  response_format={args.response_format}")
        resp = gpt_api.generate(
            presets.resolve_preset_base_url(p.preset_id),
            presets.resolve_preset_api_key(p.preset_id),
            args.prompt, size=size_str, model=p.default_model, quality=args.quality,
            background=args.background, output_format=args.output_format,
            response_format=args.response_format, timeout=args.timeout)
        saved = gpt_api.save_image(resp, args.save)
        _report_saved(saved, resp)
        return resp

    _, pid = _run_chain(args, protocol, run_once)
    print(f"  served by: {pid}")


def cmd_edit(args):
    protocol = "openai_images"
    print(f"[edit] preset={args.preset}  image={args.image}")
    _warn_input_size(args.image)

    def run_once(p):
        if p.protocol == "gemini_generate_content":
            print(f"  -> {p.preset_id}  model={p.default_model}")
            resp = banana_api.edit(
                presets.resolve_preset_base_url(p.preset_id),
                presets.resolve_preset_api_key(p.preset_id),
                p.default_model, args.image, args.prompt)
            saved = banana_api.save_image(resp, args.save)
            _report_saved(saved, resp)
            return resp

        _validate_for_preset(p, args.size, args.quality)
        print(f"  -> {p.preset_id}  model={p.default_model}"
              + (f"  size={args.size}" if args.size else "  size=<input>")
              + (f"  quality={args.quality}" if args.quality else "")
              + f"  response_format={args.response_format}")
        resp = gpt_api.edit(
            presets.resolve_preset_base_url(p.preset_id),
            presets.resolve_preset_api_key(p.preset_id),
            args.image, args.prompt, mask_path=args.mask, size=args.size,
            model=p.default_model, quality=args.quality,
            background=args.background, output_format=args.output_format,
            response_format=args.response_format, timeout=args.timeout)
        saved = gpt_api.save_image(resp, args.save)
        _report_saved(saved, resp)
        return resp

    _, pid = _run_chain(args, protocol, run_once)
    print(f"  served by: {pid}")


def _report_saved(saved: list[str], resp: dict) -> None:
    if not saved:
        keys = list(resp.keys())
        print(f"  [!] response carried no image (keys={keys}, "
              f"error={str(resp.get('error'))[:300]})")
        return
    print(f"  saved: {saved}")


def main():
    args = _parse_args()
    if args.command == "check":
        return cmd_check()
    try:
        if args.command == "generate":
            cmd_generate(args)
        elif args.command == "edit":
            cmd_edit(args)
        else:
            sys.exit("unknown command")
    except SystemExit:
        raise
    except Exception as e:  # network/SSL/JSON errors too — keep the CLI output clean
        print(f"[error] {e}", file=sys.stderr)
        if args.preset != "auto":
            print("[hint] this preset failed; re-run with --preset auto to fall back "
                  "to the other $0.03/image routes.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
