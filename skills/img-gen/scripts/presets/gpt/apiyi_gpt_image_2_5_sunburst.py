#!/usr/bin/env python3
"""apiyi_gpt_image_2_5_sunburst — wrapper for img-gen preset apiyi_gpt_image_2_5_sunburst.

Model : gpt-image-2.5-sunburst
Route : apiyi (openai_images)
Billing: EXPENSIVE (token-billed relay)  |  tier: last_resort
Note  : 官转按 token 计费（贵）；画质兜底，仅最后手段

Usage:
  python3 apiyi_gpt_image_2_5_sunburst.py generate --prompt "..." --save out.png --size 2K --ratio 16:9
  python3 apiyi_gpt_image_2_5_sunburst.py edit --image in.png --prompt "..." --save out.png --size 2048x1152
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
        sys.executable, str(_IMG_GEN), argv[0], "--preset", "apiyi_gpt_image_2_5_sunburst", *argv[1:]
    ])
