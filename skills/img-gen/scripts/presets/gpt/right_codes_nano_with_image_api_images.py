#!/usr/bin/env python3
"""right_codes_nano_with_image_api_images — direct GPT image generation/editing.

Usage:
  python3 right_codes_nano_with_image_api_images.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 right_codes_nano_with_image_api_images.py edit --image in.png --prompt "..." --save out.png
"""
import os, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_IMG_GEN = _HERE / "../../img_gen.py"

if __name__ == "__main__":
    os.execvp("python3", ["python3", str(_IMG_GEN), "--preset", "right_codes_nano_with_image_api_images"] + sys.argv[1:])
