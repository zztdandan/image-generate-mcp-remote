#!/usr/bin/env python3
"""right_codes_nano_with_image_api_images — wrapper for img-gen preset right_codes_nano_with_image_api_images.

Model : nano-banana-2
Route : right_codes (openai_images)
Billing: varies  |  tier: standard
Note  : stable

Usage:
  python3 right_codes_nano_with_image_api_images.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 right_codes_nano_with_image_api_images.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_IMG_GEN = _HERE / "../../img_gen.py"

if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        sys.exit(__doc__)
    os.execvp(sys.executable, [
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "right_codes_nano_with_image_api_images", *argv[1:]
    ])
