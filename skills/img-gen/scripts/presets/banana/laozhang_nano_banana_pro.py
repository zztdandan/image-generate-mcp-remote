#!/usr/bin/env python3
"""laozhang_nano_banana_pro — wrapper for img-gen preset laozhang_nano_banana_pro.

Model : gemini-3-pro-image-preview
Route : laozhang (gemini_generate_content)
Billing: varies  |  tier: standard
Note  : stable

Usage:
  python3 laozhang_nano_banana_pro.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 laozhang_nano_banana_pro.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "laozhang_nano_banana_pro", *argv[1:]
    ])
