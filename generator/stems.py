"""
Render each MIDI channel to a separate WAV stem.
Returns a dict {name: numpy float32 array} for the mixer.
"""
import os
import shutil
import subprocess
import wave
from pathlib import Path

import mido
import numpy as np

os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

# channel → human label
CH_NAMES = {0: "chords", 1: "bass", 2: "guitar", 9: "drums"}

SF2_PATHS = [
    Path(__file__).parents[1] / "assets" / "sfz" / "GeneralUser_GS.sf2",
    Path(__file__).parents[1] / "assets" / "sfz" / "VintageDreams.sf2",
]


def _sf2() -> Path | None:
    for p in SF2_PATHS:
        if p.exists() and p.stat().st_size > 50_000:
            return p
    return None


def _filter_channel(src: Path, channel: int, dst: Path) -> bool:
    """Write a copy of src containing only events on channel (and all meta)."""
    try:
        original = mido.MidiFile(str(src))
        filtered = mido.MidiFile(ticks_per_beat=original.ticks_per_beat)
        for track in original.tracks:
            new_track = mido.MidiTrack()
            acc = 0
            for msg in track:
                acc += msg.time
                keep = msg.is_meta or (
                    hasattr(msg, "channel") and msg.channel == channel
                )
                if keep:
                    new_track.append(msg.copy(time=acc))
                    acc = 0
            filtered.tracks.append(new_track)
        filtered.save(str(dst))
        return True
    except Exception:
        return False


def _fluidsynth_render(mid: Path, wav: Path) -> bool:
    sf2 = _sf2()
    if not sf2 or not shutil.which("fluidsynth"):
        return False
    result = subprocess.run(
        ["fluidsynth", "-ni", "-F", str(wav), "-r", "44100", str(sf2), str(mid)],
        capture_output=True, timeout=60,
    )
    return result.returncode == 0 and wav.exists()


def _wav_to_array(wav_path: Path) -> np.ndarray:
    with wave.open(str(wav_path), "r") as wf:
        raw = wf.readframes(wf.getnframes())
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            data = (data[0::2] + data[1::2]) * 0.5
    return data


def render_stems(mid_path: Path, stems_dir: Path) -> dict[str, np.ndarray]:
    """
    Split mid_path by channel and render each through FluidSynth.
    Returns {label: float32_array}.  Falls back to empty dict on failure.
    """
    stems_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, np.ndarray] = {}

    # find which channels actually have note events
    try:
        mid = mido.MidiFile(str(mid_path))
    except Exception:
        return result

    active_channels: set[int] = set()
    for track in mid.tracks:
        for msg in track:
            if hasattr(msg, "channel") and msg.type in ("note_on", "note_off"):
                active_channels.add(msg.channel)

    for ch in sorted(active_channels):
        label = CH_NAMES.get(ch, f"ch{ch}")
        stem_mid = stems_dir / f"{label}.mid"
        stem_wav = stems_dir / f"{label}.wav"

        if not _filter_channel(mid_path, ch, stem_mid):
            continue
        if not _fluidsynth_render(stem_mid, stem_wav):
            continue

        arr = _wav_to_array(stem_wav)
        result[label] = arr
        stem_mid.unlink(missing_ok=True)   # tidy up temp MIDI

    return result


def mix_to_wav(
    stems: dict[str, np.ndarray],
    levels: dict[str, float],
    muted: dict[str, bool],
    master: float,
    out_path: Path,
    sr: int = 44100,
) -> None:
    """Mix stems with given levels and write a new WAV."""
    if not stems:
        return
    length = max(len(a) for a in stems.values())
    mixed = np.zeros(length, dtype=np.float32)
    for name, arr in stems.items():
        if muted.get(name, False):
            continue
        lvl = levels.get(name, 1.0) * master
        mixed[: len(arr)] += arr * lvl
    np.clip(mixed, -1.0, 1.0, out=mixed)

    data = (mixed * 32767).astype(np.int16)
    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())
