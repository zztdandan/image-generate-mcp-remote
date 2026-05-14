#!/usr/bin/env python3
import argparse
import json
import math
import subprocess


def run(command):
    return subprocess.run(command, text=True, capture_output=True, check=True)


def gcd_ratio(width, height):
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def identify(path):
    out = run(["identify", "-format", "%w %h %[channels]", path]).stdout.strip()
    width, height, channels = out.split(maxsplit=2)
    return int(width), int(height), channels.lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--requested-width", type=int)
    parser.add_argument("--requested-height", type=int)
    parser.add_argument("--strict-size", action="store_true")
    parser.add_argument("--strict-ratio", action="store_true", default=True)
    parser.add_argument("--allow-ratio-mismatch", dest="strict_ratio", action="store_false")
    args = parser.parse_args()

    actual_width, actual_height, channels = identify(args.image)
    requested_width = args.requested_width
    requested_height = args.requested_height

    has_request = requested_width is not None and requested_height is not None
    actual_ratio = gcd_ratio(actual_width, actual_height)
    requested_ratio = gcd_ratio(requested_width, requested_height) if has_request else None
    size_matches = (
        actual_width == requested_width and actual_height == requested_height
        if has_request else None
    )
    ratio_matches = actual_ratio == requested_ratio if has_request else None
    has_alpha = "a" in channels

    result = {
        "path": args.image,
        "actual_width": actual_width,
        "actual_height": actual_height,
        "requested_width": requested_width,
        "requested_height": requested_height,
        "actual_aspect_ratio": actual_ratio,
        "requested_aspect_ratio": requested_ratio,
        "channels": channels,
        "has_alpha": has_alpha,
        "size_matches_request": size_matches,
        "aspect_ratio_matches_request": ratio_matches,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.strict_size and has_request and not size_matches:
        raise SystemExit("Actual image size does not match requested size.")
    if args.strict_ratio and has_request and not ratio_matches:
        raise SystemExit("Actual image aspect ratio does not match requested ratio.")


if __name__ == "__main__":
    main()
