#!/usr/bin/env python3
"""apiyi_gpt_image_2_5_flare_vip — wrapper for img-gen preset apiyi_gpt_image_2_5_flare_vip.

Model : gpt-image-2.5-flare-vip
Route : apiyi (openai_images)
Billing: $0.03/image flat  |  tier: preferred
Note  : 速度优先的 $0.03 路线；画面偏软，适合草稿/批量试稿

Usage:
  python3 apiyi_gpt_image_2_5_flare_vip.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 apiyi_gpt_image_2_5_flare_vip.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "apiyi_gpt_image_2_5_flare_vip", *argv[1:]
    ])
