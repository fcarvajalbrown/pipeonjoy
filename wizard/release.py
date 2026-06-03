"""Handles release-type selection and output folder creation."""
import os
from pathlib import Path

OUTPUTS = Path(__file__).resolve().parents[1] / "outputs"

RELEASE_TYPES = {
    "single": "singles",
    "ep": "eps",
    "album": "albums",
}

TRACK_COUNTS = {
    "single": 1,
    "ep": (3, 6),
    "album": (8, 16),
}


def create_output_folder(release_type: str, release_name: str, song_name: str) -> Path:
    folder_key = RELEASE_TYPES[release_type]
    if release_type == "single":
        path = OUTPUTS / folder_key / _slugify(song_name)
    else:
        path = OUTPUTS / folder_key / _slugify(release_name) / _slugify(song_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def suggest_track_count(release_type: str) -> str:
    if release_type == "single":
        return ""
    lo, hi = TRACK_COUNTS[release_type]
    return f"A typical {release_type} has {lo}–{hi} tracks. Consider running the wizard again for each remaining song."


def _slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("/", "-")
