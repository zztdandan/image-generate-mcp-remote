#!/usr/bin/env python3
"""laozhang_gpt_image_2_vip — direct GPT image generation/editing.

Usage:
  python3 laozhang_gpt_image_2_vip.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 laozhang_gpt_image_2_vip.py edit --image in.png --prompt "..." --save out.png
"""
import os, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_IMG_GEN = _HERE / "../../img_gen.py"

if __name__ == "__main__":
    os.execvp("python3", ["python3", str(_IMG_GEN), "--preset", "laozhang_gpt_image_2_vip"] + sys.argv[1:])
