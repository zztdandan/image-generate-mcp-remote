#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import tempfile


COMPONENT_RE = re.compile(
    r"^\s*(\d+):\s+(\d+)x(\d+)\+(\d+)\+(\d+)\s+([0-9.]+),([0-9.]+)\s+(\d+)\s+gray\((\d+)\)"
)


def run(command):
    return subprocess.run(command, text=True, capture_output=True, check=True)


def identify_size(path):
    out = run(["identify", "-format", "%w %h", path]).stdout.strip()
    return tuple(map(int, out.split()))


def postprocess_operations(name):
    if name == "baseline":
        return []
    if name == "alpha_open_blur":
        return [
            "(", "+clone", "-alpha", "extract",
            "-morphology", "Open", "Diamond:1",
            "-blur", "0x0.4", ")",
            "-compose", "CopyOpacity", "-composite",
        ]
    raise SystemExit(f"Unsupported postprocess mode: {name}")


def detect_components(sheet, threshold, close_disk):
    result = run([
        "convert", sheet,
        "-colorspace", "gray",
        "-negate",
        "-threshold", threshold,
        "-morphology", "Close", f"Disk:{close_disk}",
        "-define", "connected-components:verbose=true",
        "-connected-components", "8",
        "NULL:",
    ])
    text = result.stdout + "\n" + result.stderr
    components = []
    for line in text.splitlines():
        match = COMPONENT_RE.match(line)
        if not match:
            continue
        comp_id, w, h, x, y, cx, cy, area, gray = match.groups()
        components.append({
            "id": int(comp_id),
            "w": int(w),
            "h": int(h),
            "x": int(x),
            "y": int(y),
            "cx": float(cx),
            "cy": float(cy),
            "area": int(area),
            "gray": int(gray),
        })
    return components


def choose_icon_components(components, rows, cols, min_area):
    expected_count = rows * cols
    foreground = [
        comp for comp in components
        if comp["id"] != 0 and comp["gray"] == 255
    ]
    icons = [comp for comp in foreground if comp["area"] >= min_area]
    icons = sorted(icons, key=lambda comp: comp["area"], reverse=True)[:expected_count]
    if len(icons) != expected_count:
        icons = sorted(foreground, key=lambda comp: comp["area"], reverse=True)[:expected_count]
    if len(icons) != expected_count:
        raise SystemExit(
            f"Expected {expected_count} main components for {rows}x{cols}, "
            f"found {len(icons)} after fallback."
        )

    icons = sorted(icons, key=lambda comp: comp["cy"])
    ordered = []
    for row_index in range(rows):
        start = row_index * cols
        row = sorted(icons[start:start + cols], key=lambda comp: comp["cx"])
        ordered.extend(row)
    return ordered


def crop_original(sheet, comp, pad, out_path):
    sheet_w, sheet_h = identify_size(sheet)
    x = max(0, comp["x"] - pad)
    y = max(0, comp["y"] - pad)
    right = min(sheet_w, comp["x"] + comp["w"] + pad)
    bottom = min(sheet_h, comp["y"] + comp["h"] + pad)
    w = right - x
    h = bottom - y
    subprocess.run([
        "convert", sheet,
        "-crop", f"{w}x{h}+{x}+{y}", "+repage",
        out_path,
    ], check=True)


def apply_border_connected_transparency(crop_path, out_path, fuzz, border, postprocess):
    width, height = identify_size(crop_path)
    top_right = f"color {width - 1},0 floodfill"
    bottom_left = f"color 0,{height - 1} floodfill"
    bottom_right = f"color {width - 1},{height - 1} floodfill"
    command = [
        "convert", crop_path,
        "-alpha", "set",
        "-channel", "rgba",
        "-fuzz", fuzz,
        "-fill", "none", "-draw", "color 0,0 floodfill",
        "-fill", "none", "-draw", top_right,
        "-fill", "none", "-draw", bottom_left,
        "-fill", "none", "-draw", bottom_right,
        "+channel",
        "-trim", "+repage",
        "-bordercolor", "none", "-border", str(border),
    ]
    command.extend(postprocess_operations(postprocess))
    command.append(f"PNG32:{out_path}")
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet")
    parser.add_argument("output_dir")
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--threshold", default="4%")
    parser.add_argument("--close-disk", type=int, default=5)
    parser.add_argument("--min-area", type=int, default=50000)
    parser.add_argument("--pad", type=int, default=28)
    parser.add_argument("--fuzz", default="1.5%")
    parser.add_argument("--border", type=int, default=16)
    parser.add_argument("--postprocess", choices=["baseline", "alpha_open_blur"], default="baseline")
    args = parser.parse_args()

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("rows and cols must be positive integers.")

    os.makedirs(args.output_dir, exist_ok=True)
    components = detect_components(args.sheet, args.threshold, args.close_disk)
    icons = choose_icon_components(components, args.rows, args.cols, args.min_area)

    with tempfile.TemporaryDirectory() as tmpdir:
        for index, comp in enumerate(icons):
            crop_path = os.path.join(tmpdir, f"crop-{index:02d}.png")
            out_path = os.path.join(args.output_dir, f"icon-{index:02d}.png")
            crop_original(args.sheet, comp, args.pad, crop_path)
            apply_border_connected_transparency(crop_path, out_path, args.fuzz, args.border, args.postprocess)

    print(f"Wrote {len(icons)} icons to {args.output_dir} using {args.rows}x{args.cols}")


if __name__ == "__main__":
    main()
