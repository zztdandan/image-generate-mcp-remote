#!/usr/bin/env python3
"""laozhang_gpt_image_2_default — wrapper for img-gen preset laozhang_gpt_image_2_default.

Model : gpt-image-2
Route : laozhang (openai_images)
Billing: EXPENSIVE (token-billed relay)  |  tier: last_resort
Note  : 官转 gpt-image-2，按 token 计费（贵）

Usage:
  python3 laozhang_gpt_image_2_default.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 laozhang_gpt_image_2_default.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "laozhang_gpt_image_2_default", *argv[1:]
    ])
