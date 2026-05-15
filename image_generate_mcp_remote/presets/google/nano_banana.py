"""Default Google Gemini-compatible Nano Banana preset."""

from __future__ import annotations

from ..base import BaseNanoBananaPreset


class GoogleNanoBananaPreset(BaseNanoBananaPreset):
    """Default Google Gemini-compatible Nano Banana preset."""

    preset_id = "google_nano_banana"
    notes = ("Default Gemini generateContent compatible preset for nano_banana_2_official.",)
