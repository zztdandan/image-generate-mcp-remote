#!/usr/bin/env python3
"""copperai_gpt_image_2 — wrapper for img-gen preset copperai_gpt_image_2.

Model : gpt-image-2
Route : copperai (openai_images)
Billing: varies  |  tier: standard
Note  : experimental

Usage:
  python3 copperai_gpt_image_2.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 copperai_gpt_image_2.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "copperai_gpt_image_2", *argv[1:]
    ])
