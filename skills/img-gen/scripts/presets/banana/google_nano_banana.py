#!/usr/bin/env python3
"""google_nano_banana — wrapper for img-gen preset google_nano_banana.

Model : gemini-3.1-flash-image-preview
Route : google (gemini_generate_content)
Billing: varies  |  tier: standard
Note  : stable

Usage:
  python3 google_nano_banana.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 google_nano_banana.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "google_nano_banana", *argv[1:]
    ])
