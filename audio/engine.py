"""Additive synthesis engine — no external instruments needed for previews."""
import threading
import numpy as np

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False

SR = 44100

# ── note tables ───────────────────────────────────────────────────────────────

ROOT_HZ = {
    "C": 130.81, "C#": 138.59, "D": 146.83, "Eb": 155.56,
    "E": 164.81, "F": 174.61, "F#": 185.00, "G": 196.00,
    "Ab": 207.65, "A": 220.00, "Bb": 233.08, "B": 246.94,
}

MODES = {
    "Aeolian":           [0, 2, 3, 5, 7, 8, 10, 12],
    "Dorian":            [0, 2, 3, 5, 7, 9, 10, 12],
    "Phrygian":          [0, 1, 3, 5, 7, 8, 10, 12],
    "Phrygian Dominant": [0, 1, 4, 5, 7, 8, 10, 12],
    "Double Harmonic":   [0, 1, 4, 5, 7, 8, 11, 12],
    "Locrian":           [0, 1, 3, 5, 6, 8, 10, 12],
    "Mixolydian":        [0, 2, 4, 5, 7, 9, 10, 12],
}

CHORD_PROGS = {
    "i – VII – VI – VII": [[0,3,7], [-2,2,5], [-4,0,3], [-2,2,5]],
    "i – VI – III – VII":  [[0,3,7], [-4,0,3], [-9,-5,-2], [-2,2,5]],
    "i – iv – VII – III":  [[0,3,7], [5,8,12], [-2,2,5], [-9,-5,-2]],
    "i – ♭II – VII – i":  [[0,3,7], [1,5,8], [-2,2,5], [0,3,7]],
    "i – III – ♭VII – IV": [[0,3,7], [-9,-5,-2], [-2,2,5], [5,9,12]],
    "I – V – vi – IV":     [[0,4,7], [7,11,14], [-3,0,4], [5,9,12]],
}

BPM_MAP = {"Drift": 70, "Walk": 90, "Drive": 115, "Aggro": 155}

# ── primitives ────────────────────────────────────────────────────────────────

def _env(n: int, sr: int = SR, attack: float = 0.015, release: float = 0.1) -> np.ndarray:
    e = np.ones(n, dtype=np.float32)
    a = min(int(sr * attack), n)
    r = min(int(sr * release), n)
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] *= np.linspace(1, 0, r)
    return e


def _sine(freq: float, dur: float, amp: float = 0.22) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    w = np.sin(2 * np.pi * freq * t).astype(np.float32)
    return w * _env(n) * amp


def _triangle(freq: float, dur: float, amp: float = 0.20) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    w = (2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1).astype(np.float32)
    return w * _env(n, release=0.15) * amp


def _kick(dur: float = 0.3) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = 90 * np.exp(-t * 28)
    phase = np.cumsum(freq) / SR
    w = np.sin(2 * np.pi * phase).astype(np.float32)
    return w * np.exp(-t * 14).astype(np.float32) * 0.7


def _snare(dur: float = 0.18) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.default_rng(42).standard_normal(n).astype(np.float32)
    tone  = np.sin(2 * np.pi * 210 * t).astype(np.float32)
    env   = np.exp(-t * 22).astype(np.float32)
    return (noise * 0.45 + tone * 0.15) * env * 0.55


def _hihat(dur: float = 0.04) -> np.ndarray:
    n = int(SR * dur)
    noise = np.random.default_rng(7).standard_normal(n).astype(np.float32)
    env   = np.exp(-np.linspace(0, 30, n)).astype(np.float32)
    return noise * env * 0.25


def _silence(dur: float) -> np.ndarray:
    return np.zeros(int(SR * dur), dtype=np.float32)


def _chord(root_hz: float, semitones: list, dur: float, amp: float = 0.18) -> np.ndarray:
    parts = [_sine(root_hz * 2 ** (s / 12), dur, amp) for s in semitones]
    w = sum(parts)
    return np.clip(w, -1.0, 1.0).astype(np.float32)


def _mix(*waves: np.ndarray) -> np.ndarray:
    L = max(len(w) for w in waves)
    out = np.zeros(L, dtype=np.float32)
    for w in waves:
        out[:len(w)] += w
    return np.clip(out, -1.0, 1.0)

# ── preview generators ────────────────────────────────────────────────────────

def preview_scale(mode_label: str, root: str = "A") -> np.ndarray:
    intervals = _mode_intervals(mode_label)
    hz = ROOT_HZ.get(root, 220.0)
    up   = [_sine(hz * 2 ** (s / 12), 0.22) for s in intervals]
    down = [_sine(hz * 2 ** (s / 12), 0.18) for s in reversed(intervals[:-1])]
    gap  = _silence(0.03)
    parts = []
    for n in up + down:
        parts.append(n)
        parts.append(gap)
    return np.concatenate(parts)


def preview_chord_prog(prog_label: str, root: str = "A") -> np.ndarray:
    prog = _find_prog(prog_label)
    hz   = ROOT_HZ.get(root, 220.0)
    dur  = 60 / 100 * 2  # 2 beats at 100 BPM
    bars = []
    for _ in range(2):
        for sem in prog:
            bars.append(_chord(hz, sem, dur))
    return np.concatenate(bars)


def preview_tempo(tempo_label: str) -> np.ndarray:
    bpm  = _find_bpm(tempo_label)
    beat = 60 / bpm
    parts = []
    for i in range(8):
        parts.append(_kick() if i % 4 == 0 else _snare())
        gap = beat - (0.3 if i % 4 == 0 else 0.18)
        parts.append(_silence(max(gap, 0.02)))
    return np.concatenate(parts)


def preview_timesig(sig: str) -> np.ndarray:
    patterns = {
        "4/4":  [1,0,0,0,1,0,0,0],
        "3/4":  [1,0,0,1,0,0],
        "6/8":  [1,0,0,0,0,0,1,0,0,0,0,0],
        "5/4":  [1,0,0,1,0,1,0,0,1,0],
        "7/8":  [1,0,1,0,1,0,0,1,0,1,0,1,0,0],
        "11/8": [1,0,0,1,0,0,1,0,1,0,0],
    }
    key  = sig.split()[0]
    pat  = patterns.get(key, patterns["4/4"])
    step = 0.14
    parts = []
    for _ in range(2):
        for loud in pat:
            if loud:
                parts.append(_kick() if loud == 2 else _snare())
            else:
                parts.append(_silence(step))
    return np.concatenate(parts)


def preview_groove(label: str) -> np.ndarray:
    beat = 0.5
    parts = []
    for i in range(4):
        parts.append(_kick())
        if "Swung" in label:
            parts.append(_silence(beat * 0.62))
            parts.append(_snare())
            parts.append(_silence(beat * 0.38))
        elif "Shuffled" in label:
            parts.append(_silence(beat * 0.55))
            parts.append(_snare())
            parts.append(_silence(beat * 0.45))
        else:
            parts.append(_silence(beat * 0.5))
            parts.append(_snare())
            parts.append(_silence(beat * 0.5))
    return np.concatenate(parts)


def preview_bass(label: str, root: str = "A") -> np.ndarray:
    hz   = ROOT_HZ.get(root, 220.0)
    beat = 0.38
    if "Melodic" in label or "Hook" in label:
        run = [0, 2, 3, 7, 12, 10, 7, 5, 3, 2, 0, -2]
    elif "Walking" in label:
        run = [0, 2, 4, 5, 7, 5, 4, 2, 0, 2, 4, 5]
    elif "Counter" in label:
        run = [0, 3, 5, 7, 5, 3, 7, 5, 3, 0, 3, 0]
    else:
        run = [0, 0, 7, 0, 0, 0, 7, 0, 0, 0, 12, 0]
    return np.concatenate([_triangle(hz * 2 ** (s / 12), beat) for s in run])


def preview_synth(label: str, root: str = "A") -> np.ndarray:
    hz  = ROOT_HZ.get(root, 220.0)
    sem = [0, 3, 7, 10]
    dur = 2.8
    if "FM" in label or "electric" in label.lower() or "warm" in label.lower():
        # FM-ish: sine + frequency modulation
        parts = []
        for s in sem:
            f = hz * 2 ** (s / 12)
            n = int(SR * dur)
            t = np.linspace(0, dur, n, endpoint=False)
            mod = 0.5 * np.sin(2 * np.pi * f * 2.01 * t)
            w   = np.sin(2 * np.pi * f * t + mod).astype(np.float32)
            parts.append(w * _env(n, release=0.3) * 0.15)
        return _mix(*parts)
    elif "cold" in label.lower() or "digital" in label.lower():
        parts = [_triangle(hz * 2 ** (s / 12), dur, 0.13) for s in sem]
        return _mix(*parts)
    elif "Detuned" in label:
        # two slightly detuned oscillators
        parts = []
        for s in sem:
            f = hz * 2 ** (s / 12)
            parts.append(_sine(f, dur, 0.10))
            parts.append(_sine(f * 1.008, dur, 0.08))  # 8 cents detune
        return _mix(*parts)
    else:
        parts = [_sine(hz * 2 ** (s / 12), dur, 0.13) for s in sem]
        return _mix(*parts)


def preview_generic(root: str = "A") -> np.ndarray:
    hz = ROOT_HZ.get(root, 220.0)
    return _chord(hz, [0, 3, 7], dur=2.0)


# ── dispatcher ────────────────────────────────────────────────────────────────

def preview_for_step(key: str, value: str, answers: dict) -> np.ndarray:
    root = answers.get("root_key", "A")
    if root not in ROOT_HZ:
        root = "A"
    dispatch = {
        "mode":        lambda: preview_scale(value, root),
        "root_key":    lambda: preview_generic(value if value in ROOT_HZ else "A"),
        "tempo_range": lambda: preview_tempo(value),
        "time_sig":    lambda: preview_timesig(value),
        "chord_prog":  lambda: preview_chord_prog(value, root),
        "groove":      lambda: preview_groove(value),
        "bass_role":   lambda: preview_bass(value, root),
        "synth_char":  lambda: preview_synth(value, root),
    }
    fn = dispatch.get(key)
    return fn() if fn else preview_generic(root)


# ── playback ──────────────────────────────────────────────────────────────────

_thread: threading.Thread | None = None


def play(audio: np.ndarray) -> None:
    global _thread
    stop()
    if not HAS_SD:
        return
    def _run():
        try:
            sd.play(audio, samplerate=SR)
            sd.wait()
        except Exception:
            pass
    _thread = threading.Thread(target=_run, daemon=True)
    _thread.start()


def stop() -> None:
    if HAS_SD:
        try:
            sd.stop()
        except Exception:
            pass


# ── helpers ───────────────────────────────────────────────────────────────────

def _mode_intervals(label: str) -> list:
    for name, intervals in MODES.items():
        if name.lower() in label.lower():
            return intervals
    return MODES["Aeolian"]


def _find_prog(label: str) -> list:
    for k, v in CHORD_PROGS.items():
        if label.strip().startswith(k.split()[0]):
            return v
    return CHORD_PROGS["i – VII – VI – VII"]


def _find_bpm(label: str) -> int:
    for k, v in BPM_MAP.items():
        if k.lower() in label.lower():
            return v
    return 100
