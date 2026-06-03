"""Render MIDI → WAV via FluidSynth, then apply a basic master mix with pydub."""
import os
import shutil
import subprocess
from pathlib import Path

os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

SF2_PATHS = [
    Path(__file__).parents[1] / "assets" / "sfz" / "VintageDreams.sf2",
    Path("/opt/homebrew/Cellar/fluid-synth/2.5.4/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2"),
]

def _sf2() -> Path | None:
    for p in SF2_PATHS:
        if p.exists() and p.stat().st_size > 50_000:
            return p
    return None


def render_wav(mid_path: Path, out_path: Path) -> Path | None:
    """
    Render mid_path → WAV via FluidSynth CLI, then master via pydub.
    Returns path to the mastered WAV, or None on failure.
    """
    sf2 = _sf2()
    if not sf2:
        return None
    if not shutil.which("fluidsynth"):
        return None

    raw_wav = out_path / "sketch_raw.wav"
    final   = out_path / "sketch.wav"

    # 1. FluidSynth render
    cmd = [
        "fluidsynth", "-ni",
        "-F", str(raw_wav),
        "-r", "44100",
        str(sf2), str(mid_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0 or not raw_wav.exists():
        return None

    # 2. pydub master: normalize → subtle compression → fade in/out
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize

        audio = AudioSegment.from_wav(str(raw_wav))
        audio = normalize(audio, headroom=1.0)    # peak to -1 dBFS

        # gentle gain reduction on the louder half (simple compression stand-in)
        chunks = []
        step_ms = 50
        threshold_db = -12
        ratio = 3.0
        for i in range(0, len(audio), step_ms):
            chunk = audio[i:i+step_ms]
            if chunk.dBFS > threshold_db:
                reduction = (chunk.dBFS - threshold_db) * (1 - 1/ratio)
                chunk = chunk - reduction
            chunks.append(chunk)
        audio = sum(chunks, AudioSegment.empty())

        # fade in 80ms, fade out 500ms
        audio = audio.fade_in(80).fade_out(500)
        audio = normalize(audio, headroom=0.5)

        audio.export(str(final), format="wav")
        raw_wav.unlink(missing_ok=True)
        return final

    except ImportError:
        # pydub not available — rename raw
        raw_wav.rename(final)
        return final
    except Exception:
        return None
