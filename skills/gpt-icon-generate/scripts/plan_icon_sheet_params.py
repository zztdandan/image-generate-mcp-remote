#!/usr/bin/env python3
import argparse
import json


BASE_SIZE = 2048
BASE_MIN_AREA = 50000
BASE_PAD = 28
BASE_BORDER = 16


def clamp(value, minimum):
    return max(minimum, int(round(value)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--fuzz", default="1.5%")
    parser.add_argument("--postprocess", choices=["baseline", "alpha_open_blur"], default="baseline")
    parser.add_argument("--pad", type=int)
    parser.add_argument("--border", type=int)
    parser.add_argument("--min-area", type=int)
    args = parser.parse_args()

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("rows and cols must be positive integers.")

    expected_count = args.rows * args.cols
    cell_width = args.width / args.cols
    cell_height = args.height / args.rows
    icon_canvas_size = int(min(cell_width, cell_height))
    recommended_icon_extent = int(icon_canvas_size * 0.8)
    scale = min(args.width, args.height) / BASE_SIZE
    area_scale = (args.width * args.height) / (BASE_SIZE * BASE_SIZE)

    pad = args.pad if args.pad is not None else clamp(BASE_PAD * scale, 8)
    border = args.border if args.border is not None else clamp(BASE_BORDER * scale, 6)
    min_area = args.min_area if args.min_area is not None else clamp(BASE_MIN_AREA * area_scale, 1000)

    result = {
        "width": args.width,
        "height": args.height,
        "rows": args.rows,
        "cols": args.cols,
        "expected_count": expected_count,
        "cell_width": round(cell_width, 2),
        "cell_height": round(cell_height, 2),
        "icon_canvas_size": icon_canvas_size,
        "recommended_icon_extent": recommended_icon_extent,
        "pad": pad,
        "border": border,
        "fuzz": args.fuzz,
        "postprocess": args.postprocess,
        "min_area": min_area,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
