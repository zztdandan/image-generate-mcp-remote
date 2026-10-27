#!/usr/bin/env python3
"""openai_gpt_image_2 — wrapper for img-gen preset openai_gpt_image_2.

Model : gpt-image-2
Route : openai (openai_images)
Billing: EXPENSIVE (token-billed relay)  |  tier: last_resort
Note  : 官方直连，最贵；仅在需要官方字段行为时使用

Usage:
  python3 openai_gpt_image_2.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 openai_gpt_image_2.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "openai_gpt_image_2", *argv[1:]
    ])
