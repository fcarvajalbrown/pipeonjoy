"""
v2.0 — Sample import, slow-down, section selection, and key detection.

PLANNED FEATURES (not yet active):
  1. Download a CC0 / Public Domain track by URL or search term
     → yt-dlp with Creative Commons filter, or Free Music Archive API
  2. Load WAV/MP3 into memory (librosa)
  3. Display a waveform in a canvas widget — user clicks to set section start/end
  4. Slow down the selected section (librosa time_stretch, no pitch shift)
     → vaporwave "slowed + reverb" effect
  5. Detect the key of that section
     → librosa.feature.chroma_cqt → Krumhansl-Schmuckler key-finding algorithm
  6. Return detected key + mode as a suggested answer for the wizard

None of this runs until the user explicitly opens the sample tool (v2.0 menu).
"""

# ── stub constants ────────────────────────────────────────────────────────────
V2_NOT_READY = (
    "Sample analysis is a v2.0 feature.\n\n"
    "When ready it will:\n"
    "  • Search CC0/Public Domain audio\n"
    "  • Let you select and slow down a section\n"
    "  • Auto-detect the key and suggest it in the wizard"
)


def launch_sample_tool():
    """Placeholder — shows the v2.0 message for now."""
    import tkinter.messagebox as mb
    mb.showinfo("pipeonjoy — v2.0 feature", V2_NOT_READY)


# ── future imports (uncomment when implementing) ──────────────────────────────
# import librosa
# import yt_dlp
# import numpy as np
# from pathlib import Path
#
# FREE_MUSIC_ARCHIVE_API = "https://freemusicarchive.org/api/get/tracks.json"
# CC_MIXTER_API          = "https://ccmixter.org/api/query"
#
# def download_cc_track(query: str, out_dir: Path) -> Path: ...
# def slow_section(audio, sr, start_s, end_s, stretch=0.75) -> np.ndarray: ...
# def detect_key(audio, sr) -> tuple[str, str]: ...  # ("A", "Aeolian")
