"""
Audio engine.
Primary:  FluidSynth (pyfluidsynth) + GeneralUser GS SF2 (31 MB, real multi-sampled GM bank).
Fallback: VintageDreams.sf2, then additive synthesis when FluidSynth is unavailable.
"""
import os
import sys
import threading
import numpy as np
from pathlib import Path

# ── env: help macOS find the Homebrew dylib ───────────────────────────────────
os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False

try:
    import fluidsynth as _fluidsynth
    HAS_FS = True
except ImportError:
    HAS_FS = False

SR = 44100

# ── GM program numbers (0-indexed) ───────────────────────────────────────────
# Tuned for GeneralUser GS which has real multi-sampled guitar and voice patches
GM = {
    "piano":      0,  "epiano":   4,  "organ":    16,
    "guitar_ny": 24,  "guitar":  25,  "guitar_cl":26,
    "guitar_muted":28,"distort": 29,  "guitar_harm":30,
    "bass":      32,  "bass_pick":33, "fret":     35,
    "strings":   48,
    "voice_oohs":53,  "synth_voice":54,           # vocal reference patches
    "lead_voice":85,                               # solo lead voice
    "pad_age":   87,  "pad_warm": 88,
    "pad_choir": 91,
}
CH_GTR  = 2   # dedicated guitar channel
CH_VOCAL = 3  # vocal reference channel
# GM drum note numbers
DR = {
    "kick": 36, "snare": 38, "hihat_c": 42,
    "hihat_o": 46, "crash": 49, "ride": 51, "clap": 39,
}

# ── music tables ──────────────────────────────────────────────────────────────
ROOT_HZ = {
    "C":130.81,"C#":138.59,"D":146.83,"Eb":155.56,"E":164.81,
    "F":174.61,"F#":185.00,"G":196.00,"Ab":207.65,"A":220.00,
    "Bb":233.08,"B":246.94,
}
MODES = {
    "Aeolian":           [0,2,3,5,7,8,10,12],
    "Dorian":            [0,2,3,5,7,9,10,12],
    "Phrygian":          [0,1,3,5,7,8,10,12],
    "Phrygian Dominant": [0,1,4,5,7,8,10,12],
    "Double Harmonic":   [0,1,4,5,7,8,11,12],
    "Locrian":           [0,1,3,5,6,8,10,12],
    "Mixolydian":        [0,2,4,5,7,9,10,12],
}
PROGS = {
    "i – VII – VI – VII": [[0,3,7],[-2,2,5],[-4,0,3],[-2,2,5]],
    "i – VI – III – VII":  [[0,3,7],[-4,0,3],[-9,-5,-2],[-2,2,5]],
    "i – iv – VII – III":  [[0,3,7],[5,8,12],[-2,2,5],[-9,-5,-2]],
    "i – ♭II – VII – i":  [[0,3,7],[1,5,8],[-2,2,5],[0,3,7]],
    "i – III – ♭VII – IV": [[0,3,7],[-9,-5,-2],[-2,2,5],[5,9,12]],
    "I – V – vi – IV":     [[0,4,7],[7,11,14],[-3,0,4],[5,9,12]],
}
BPM_MAP = {"Drift":70,"Walk":90,"Drive":115,"Aggro":155}

def _root_midi(root: str) -> int:
    """Return MIDI note number for root in octave 2 (bass register)."""
    notes = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]
    idx   = notes.index(root) if root in notes else 9  # default A
    return 36 + idx  # C2=36, A2=45

# ── soundfont locator ─────────────────────────────────────────────────────────
def _find_sf2() -> Path | None:
    # frozen bundle: assets are relative to _MEIPASS
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parents[1]

    # Prefer GeneralUser GS (31 MB, real multi-sampled GM bank) over VintageDreams
    for name in ("GeneralUser_GS.sf2", "VintageDreams.sf2"):
        p = base / "assets" / "sfz" / name
        if p.exists() and p.stat().st_size > 50_000:
            return p
    # dev mode: also search Homebrew Cellar
    hw = Path("/opt/homebrew/Cellar/fluid-synth")
    if hw.exists():
        hits = sorted(hw.rglob("VintageDreamsWaves-v2.sf2"))
        if hits:
            return hits[0]
    return None

_SF2 = _find_sf2()

# ── FluidSynth render ─────────────────────────────────────────────────────────
def _render_fs(events: list, total_dur: float) -> np.ndarray | None:
    """
    Render event list through FluidSynth to float32 mono numpy array.
    events: [(time_s, channel, bank, program, note, velocity, duration_s)]
    channel 9 = drums (GM standard).
    """
    if not HAS_FS or not _SF2:
        return None
    try:
        fs = _fluidsynth.Synth(samplerate=float(SR), gain=0.8)
        sfid = fs.sfload(str(_SF2))

        # configure channels used in this render
        channels_seen = {(e[1], e[2], e[3]) for e in events}
        for ch, bank, prog in channels_seen:
            fs.program_select(ch, sfid, bank, prog)

        # build sorted timeline of note-on / note-off
        tl = []
        for t, ch, bank, prog, note, vel, dur in events:
            tl.append((t, "on",  ch, note, vel))
            tl.append((t + dur, "off", ch, note))
        tl.sort(key=lambda x: x[0])

        chunks = []
        pos    = 0.0
        for item in tl:
            t = item[0]
            n = int(SR * (t - pos))
            if n > 0:
                chunks.append(np.array(fs.get_samples(n), dtype=np.int16))
            if item[1] == "on":
                fs.noteon(item[2], item[4], item[5])
            else:
                fs.noteoff(item[2], item[4])
            pos = t

        remaining = int(SR * total_dur) - int(SR * pos)
        if remaining > 0:
            chunks.append(np.array(fs.get_samples(remaining), dtype=np.int16))

        fs.delete()

        if not chunks:
            return None
        raw  = np.concatenate(chunks).astype(np.float32) / 32768.0
        left, right = raw[0::2], raw[1::2]
        n    = min(len(left), len(right), int(SR * total_dur))
        mono = np.clip((left[:n] + right[:n]) / 2, -1.0, 1.0)
        # fade out last 100ms
        fade = min(int(SR * 0.1), n)
        mono[-fade:] *= np.linspace(1, 0, fade)
        return mono
    except Exception:
        return None

# ── fallback additive synthesis ───────────────────────────────────────────────
def _sine(f, dur, amp=0.22) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    w = (np.sin(2*np.pi*f*t) + 0.4*np.sin(4*np.pi*f*t)).astype(np.float32)
    e = np.ones(n, np.float32)
    a, r = min(int(SR*.015),n), min(int(SR*.08),n)
    e[:a] = np.linspace(0,1,a); e[n-r:] = np.linspace(1,0,r)
    return w * e * amp

def _kick_syn() -> np.ndarray:
    dur, n = 0.45, int(SR*.45)
    t = np.linspace(0, dur, n, endpoint=False)
    f = 160*np.exp(-t*22)+40
    w = np.sin(2*np.pi*np.cumsum(f/SR)).astype(np.float32)
    click_n = int(SR*.004)
    click = np.random.default_rng(1).standard_normal(click_n).astype(np.float32)
    click *= np.linspace(1,0,click_n)
    w[:click_n] += click * 0.4
    env = np.exp(-t*9).astype(np.float32)
    return np.clip(w*env*0.85, -1, 1)

def _snare_syn() -> np.ndarray:
    dur, n = 0.22, int(SR*.22)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.default_rng(7).standard_normal(n).astype(np.float32)
    tone  = (np.sin(2*np.pi*230*t) + np.sin(2*np.pi*180*t)).astype(np.float32)
    env   = np.exp(-t*18).astype(np.float32)
    return np.clip((noise*.55 + tone*.2)*env*0.72, -1, 1)

def _hihat_syn(open_=False) -> np.ndarray:
    dur = 0.12 if open_ else 0.035
    n   = int(SR*dur)
    t   = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.default_rng(3).standard_normal(n).astype(np.float32)
    env   = np.exp(-t*(8 if open_ else 60)).astype(np.float32)
    return noise * env * 0.28

def _silence(dur) -> np.ndarray:
    return np.zeros(int(SR*dur), np.float32)

def _chord_syn(root_hz, semitones, dur) -> np.ndarray:
    parts = [_sine(root_hz*2**(s/12), dur, 0.16) for s in semitones]
    return np.clip(sum(parts), -1, 1).astype(np.float32)

# ── event sequence builders ───────────────────────────────────────────────────
#  event tuple: (time_s, channel, bank, program, note, velocity, duration_s)

def _drum_bar(bpm=100, pattern="4/4", loops=2) -> list:
    beat = 60/bpm
    if pattern.startswith("3"):
        positions = [0, beat, beat*2] * loops
        hits = ["kick","hihat_c","snare"] * loops
    elif pattern.startswith("7"):
        positions = [0, beat, beat*2, beat*3, beat*3.5, beat*4, beat*4.5] * loops
        hits = ["kick","hihat_c","snare","hihat_c","kick","snare","hihat_c"] * loops
    else:  # 4/4 default
        positions = []
        hits      = []
        for i in range(4*loops):
            positions += [beat*i, beat*i+beat*.5]
            hits      += ["kick" if i%2==0 else "snare", "hihat_c"]
    return [(t, 9, 128, 0, DR[h], 100, 0.08) for t, h in zip(positions, hits)]

def _bass_run(root_midi, intervals, bpm=100) -> list:
    beat = 60/bpm
    events = []
    for i, s in enumerate(intervals):
        events.append((beat*i, 1, 0, GM["bass"], root_midi+s, 90, beat*.9))
    return events

def _chord_events(root_midi, semitones, time, dur, ch=0, prog=None) -> list:
    prog = prog or GM["pad_age"]
    return [(time, ch, 0, prog, root_midi+s, 80, dur) for s in semitones]

# ── per-step preview builders ─────────────────────────────────────────────────

def _seq_scale(mode_lbl, root):
    intervals = _mode_ivs(mode_lbl)
    rm = _root_midi(root) + 12  # one octave up for clearer timbre
    bpm, beat = 120, 60/120
    events = []
    for i, s in enumerate(intervals):
        events.append((beat*i, 1, 0, GM["guitar"], rm+s, 85, beat*.85))
    for i, s in enumerate(reversed(intervals[:-1])):
        events.append((beat*(len(intervals)+i), 1, 0, GM["guitar"], rm+s, 75, beat*.85))
    dur = beat * (len(intervals)*2 - 1) + 0.5
    return events, dur

def _seq_chords(prog_lbl, root):
    prog_sem = _prog_sem(prog_lbl)
    rm = _root_midi(root) + 12
    bpm, beat = 100, 60/100
    chord_dur = beat * 2
    events = []
    drums  = _drum_bar(bpm, "4/4", 2)
    for loop in range(2):
        for i, sem in enumerate(prog_sem):
            t = loop * 4 * beat + i * chord_dur
            events += _chord_events(rm, sem, t, chord_dur, ch=0, prog=GM["pad_age"])
            events.append((t, 1, 0, GM["bass"], rm+sem[0]-12, 90, chord_dur*.9))
            # angular guitar stab on beat 1 of each chord
            events.append((t, CH_GTR, 0, GM["guitar"], rm+12+sem[0], 82, beat*.35))
            events.append((t+beat, CH_GTR, 0, GM["guitar"], rm+12+sem[-1], 75, beat*.3))
    events += drums
    dur = chord_dur * 4 * 2 + 0.3
    return events, dur


def _seq_guitar(texture_lbl, root):
    rm   = _root_midi(root) + 24
    bpm, beat = 120, 60/120

    if "Angular" in texture_lbl or "post-punk" in texture_lbl.lower():
        # Overdriven Guitar (GM 30, 0-indexed 29) — warm overdrive, not metal
        prog    = GM["distort"]   # 29 = Overdriven Guitar in GM spec
        pitches = [0, 3, 5, 0, 7, 5, 3, 5, 0, 3, 0, -2]
        events  = [(beat*i*.5, CH_GTR, 0, prog, rm+p, 90, beat*.3)
                   for i, p in enumerate(pitches)]
    elif "Power" in texture_lbl:
        prog   = GM["distort"]
        events = []
        for i in range(8):
            t = beat * i
            for interval in [0, 7, 12]:
                events.append((t, CH_GTR, 0, prog, rm+interval, 95, beat*.8))
    elif "Arpeggi" in texture_lbl:
        # keep clean for arpeggios — contrast is part of the sound
        prog    = GM["guitar_cl"]
        pitches = [0, 3, 7, 12, 10, 7, 3, 0, 3, 7, 12, 14]
        events  = [(beat*i*.4, CH_GTR, 0, prog, rm+p, 78, beat*.38)
                   for i, p in enumerate(pitches)]
    elif "Heavy" in texture_lbl or "distort" in texture_lbl.lower():
        # Distortion Guitar (GM 31, 0-indexed 30) — heaviest preset
        prog    = GM["guitar_harm"]   # 30 = Distortion Guitar in GM spec
        pitches = [0, 0, 0, 7, 0, 5, 0, 3]
        events  = []
        for i, p in enumerate(pitches):
            t = beat * i * .5
            events.append((t, CH_GTR, 0, prog, rm+p,   100, beat*.42))
            events.append((t, CH_GTR, 0, prog, rm+p+7,  95, beat*.42))
    elif "Harmonic" in texture_lbl or "tremolo" in texture_lbl.lower():
        prog    = GM["distort"]
        pitches = [0, 3, 0, 7, 0, 5, 0, 3]
        events  = [(beat*i*.5, CH_GTR, 0, prog, rm+p,
                    78 + (i % 3)*8, beat*.55)
                   for i, p in enumerate(pitches)]
    else:
        prog    = GM["distort"]
        pitches = [0, 3, 7, 10, 7, 3]
        events  = [(beat*i*.5, CH_GTR, 0, prog, rm+p, 85, beat*.45)
                   for i, p in enumerate(pitches)]

    drums     = _drum_bar(bpm, "4/4", 1)
    bass_root = rm - 24
    bass      = [(0, 1, 0, GM["bass"], bass_root, 85, beat*3.8)]
    dur       = beat * 7 + 0.5

    events_out = events + drums + bass
    return events_out, dur

def _seq_tempo(tempo_lbl):
    bpm = _find_bpm(tempo_lbl)
    drums = _drum_bar(bpm, "4/4", 2)
    dur = 60/bpm * 8 + 0.3
    return drums, dur

def _seq_timesig(sig):
    drums = _drum_bar(100, sig, 2)
    dur = 0.14 * len(drums) + 0.3
    return drums, dur

def _seq_groove(lbl):
    bpm = 110
    beat = 60/bpm
    events = []
    for loop in range(2):
        for i in range(4):
            base = (loop*4 + i) * beat
            events.append((base, 9, 128, 0, DR["kick" if i%2==0 else "snare"], 100, 0.08))
            if "Swung" in lbl:
                events.append((base + beat*0.62, 9, 128, 0, DR["hihat_c"], 70, 0.04))
            elif "Shuffled" in lbl:
                events.append((base + beat*0.55, 9, 128, 0, DR["hihat_c"], 65, 0.04))
            else:
                events.append((base + beat*0.5, 9, 128, 0, DR["hihat_c"], 60, 0.04))
    dur = beat * 8 + 0.3
    return events, dur

def _seq_bass(role_lbl, root):
    rm = _root_midi(root)
    bpm, beat = 100, 60/100
    if "Melodic" in role_lbl or "Hook" in role_lbl:
        run = [0,2,3,7,12,10,7,5,3,2,0,2]
    elif "Walking" in role_lbl:
        run = [0,2,4,5,7,5,4,2,0,2,4,7]
    elif "Counter" in role_lbl:
        run = [0,3,5,7,5,3,0,3,5,7,3,0]
    elif "Root" in role_lbl:
        run = [0,0,7,0,0,0,7,0,0,0,0,7]
    else:
        run = [0,0,0,7,0,0,12,0,0,0,7,0]
    events = [(beat*i, 1, 0, GM["bass"], rm+s, 90, beat*.9) for i, s in enumerate(run)]
    drums  = _drum_bar(bpm, "4/4", 1)
    dur    = beat*len(run) + 0.3
    return events + drums, dur

def _seq_drums_only(kick_lbl="", snare_lbl="", hihat_lbl="", loops=2):
    bpm, beat = 110, 60/110
    events = []
    for loop in range(loops):
        for bar in range(4):
            base = (loop*4 + bar) * beat
            # kick
            if "Polyrhythm" in kick_lbl:
                for k in [0, beat*0.67, beat*1.33]:
                    events.append((base+k, 9, 128, 0, DR["kick"], 100, 0.05))
            elif "Double" in kick_lbl:
                events += [(base, 9,128,0,DR["kick"],100,.05),
                           (base+beat*.12, 9,128,0,DR["kick"],85,.05)]
            elif "2-and-4" in kick_lbl or "1 & 3" in snare_lbl:
                if bar % 2 == 0:
                    events.append((base, 9,128,0,DR["kick"],100,.05))
            else:
                if bar % 2 == 0:
                    events.append((base, 9,128,0,DR["kick"],100,.05))
            # snare
            if "1 & 3" in snare_lbl:
                if bar % 2 == 0:
                    events.append((base, 9,128,0,DR["snare"],95,.05))
            elif "Ghost" in snare_lbl:
                events += [(base+beat*.25, 9,128,0,DR["snare"],40,.04),
                           (base+beat*.75, 9,128,0,DR["snare"],45,.04)]
            else:
                if bar % 2 == 1:
                    events.append((base, 9,128,0,DR["snare"],100,.05))
            # hihat
            density = 4 if "Sixteenth" in hihat_lbl else (2 if "Eighth" in hihat_lbl else 1)
            for d in range(density):
                ht = base + beat * d / density
                events.append((ht, 9,128,0,DR["hihat_c"],65,.04))
    dur = beat * 4 * loops + 0.3
    return events, dur

def _seq_synth(char_lbl, root):
    rm = _root_midi(root) + 12
    sem = [0,3,7,10]
    if "FM" in char_lbl or "electric" in char_lbl.lower():
        prog = GM["epiano"]
    elif "cold" in char_lbl.lower() or "digital" in char_lbl.lower():
        prog = GM["pad_choir"]
    elif "Detuned" in char_lbl:
        prog = GM["strings"]
    else:
        prog = GM["pad_warm"]
    events = [(0, 0, 0, prog, rm+s, 80, 2.5) for s in sem]
    return events, 3.0

def _seq_vocal(delivery_lbl, contour_lbl, root):
    """Vocal reference preview — uses voice GM patches so it sounds like a sung line."""
    rm   = _root_midi(root) + 24    # vocal sits in the mid-upper register
    bpm, beat = 90, 60/90

    # pick patch based on delivery style
    if "Slurred" in delivery_lbl or "pitch-shifted" in delivery_lbl.lower():
        prog = GM["synth_voice"]
    elif "Chant" in delivery_lbl or "monotone" in delivery_lbl.lower():
        prog = GM["voice_oohs"]
    else:
        prog = GM["lead_voice"]

    # build melody shape from contour label
    if "Arch" in contour_lbl:
        pitches = [0, 2, 3, 5, 7, 7, 5, 7, 5, 3, 2, 0]
    elif "Ascending" in contour_lbl:
        pitches = [0, 2, 3, 5, 5, 7, 8, 10, 10, 8, 7, 5]
    elif "Descending" in contour_lbl:
        pitches = [10, 8, 7, 5, 5, 3, 2, 0, 0, 2, 0, -2]
    else:  # Plateau — sustained tension
        pitches = [5, 5, 7, 5, 5, 7, 5, 3, 5, 5, 7, 5]

    note_dur = beat * 0.85
    events = [(beat * i, CH_VOCAL, 0, prog, rm + p, 82, note_dur)
              for i, p in enumerate(pitches)]

    # add a simple drum + bass backdrop
    drums = _drum_bar(bpm, "4/4", 1)
    bass  = [(0, 1, 0, GM["bass"], rm - 24, 78, beat * 3.8)]
    dur   = beat * len(pitches) + 0.5
    return events + drums + bass, dur


def _seq_varied(key, value, root):
    """Fallback: generate a subtly varied preview so every option sounds different."""
    rm   = _root_midi(root)
    bpm  = 100
    beat = 60/bpm
    # use a hash of the value text to pick a voicing variant
    h    = sum(ord(c) for c in value) % 7
    chord_voicings = [
        [0,3,7],[0,4,7],[0,3,6],[0,4,8],[0,5,7],[0,3,7,10],[0,4,7,11]
    ]
    prog_choices = [GM["pad_age"], GM["pad_warm"], GM["pad_choir"],
                    GM["strings"], GM["epiano"], GM["guitar"], GM["organ"]]
    sem   = chord_voicings[h]
    prog  = prog_choices[h]
    drums = _drum_bar(bpm, "4/4", 1)
    chords = [(beat*i, 0, 0, prog, rm+12+s, 75, beat*1.8)
              for i, s in enumerate(sem) for _ in range(1)]
    bass  = [(0, 1, 0, GM["bass"], rm+sem[0], 85, beat*3.5)]
    dur   = beat * 4 + 0.3
    return drums + chords + bass, dur

# ── public preview dispatcher ─────────────────────────────────────────────────

def preview_for_step(key: str, value: str, answers: dict) -> np.ndarray:
    root = answers.get("root_key", "A")
    if root not in ROOT_HZ:
        root = "A"
    bpm = _find_bpm(answers.get("tempo_range", "Drive"))

    dispatch = {
        "mode":              lambda: _seq_scale(value, root),
        "root_key":          lambda: _seq_scale(answers.get("mode","Aeolian"), value if value in ROOT_HZ else "A"),
        "tempo_range":       lambda: _seq_tempo(value),
        "time_sig":          lambda: _seq_timesig(value),
        "chord_prog":        lambda: _seq_chords(value, root),
        "groove":            lambda: _seq_groove(value),
        "kick_pattern":      lambda: _seq_drums_only(kick_lbl=value),
        "snare_place":       lambda: _seq_drums_only(snare_lbl=value),
        "hihat_density":     lambda: _seq_drums_only(hihat_lbl=value),
        "ghost_notes":       lambda: _seq_drums_only(snare_lbl=value),
        "bass_role":         lambda: _seq_bass(value, root),
        "bass_pattern":      lambda: _seq_bass(value, root),
        "synth_char":        lambda: _seq_synth(value, root),
        "synth_presence":    lambda: _seq_synth(value, root),
        # ── guitar steps ──
        "guitar_texture":    lambda: _seq_guitar(value, root),
        "guitar_density":    lambda: _seq_guitar(value, root),
        "delay_type":        lambda: _seq_guitar(answers.get("guitar_texture","Angular"), root),
        "reverb_amount":     lambda: _seq_guitar(answers.get("guitar_texture","Angular"), root),
        "tremolo":           lambda: _seq_guitar(answers.get("guitar_texture","Angular"), root),
        # ── vocal reference steps ──
        "vocal_delivery":    lambda: _seq_vocal(value,
                                 answers.get("vocal_contour","Arch — rises then falls"), root),
        "vocal_contour":     lambda: _seq_vocal(
                                 answers.get("vocal_delivery","Melodic minor scale"), value, root),
        "vocal_tessitura":   lambda: _seq_vocal(
                                 answers.get("vocal_delivery","Melodic minor scale"),
                                 answers.get("vocal_contour","Arch — rises then falls"), root),
        "hook_placement":    lambda: _seq_vocal(
                                 answers.get("vocal_delivery","Melodic minor scale"),
                                 answers.get("vocal_contour","Arch — rises then falls"), root),
        "phrasing_density":  lambda: _seq_vocal(
                                 answers.get("vocal_delivery","Melodic minor scale"), value, root),
        "call_response":     lambda: _seq_vocal(
                                 answers.get("vocal_delivery","Melodic minor scale"),
                                 answers.get("vocal_contour","Arch — rises then falls"), root),
    }

    fn = dispatch.get(key)
    events, dur = fn() if fn else _seq_varied(key, value, root)

    audio = _render_fs(events, dur)
    if audio is not None:
        return audio
    # ── additive fallback ──
    return _synth_fallback(events, dur, root)

def _synth_fallback(events: list, dur: float, root: str) -> np.ndarray:
    """Crude additive synthesis fallback when FluidSynth is unavailable."""
    hz     = ROOT_HZ.get(root, 220.0)
    n_out  = int(SR * dur)
    out    = np.zeros(n_out, np.float32)
    for (t, ch, bank, prog, note, vel, note_dur) in events:
        start = int(SR * t)
        if ch == 9:  # drums
            d = _kick_syn() if note == DR["kick"] else (_hihat_syn() if note == DR["hihat_c"] else _snare_syn())
        else:
            freq = 440 * 2**((note - 69)/12)
            d    = _sine(freq, note_dur, amp=vel/127*0.25)
        end = min(start + len(d), n_out)
        out[start:end] += d[:end-start]
    return np.clip(out, -1, 1)

# ── playback ──────────────────────────────────────────────────────────────────
_play_thread: threading.Thread | None = None

def play(audio: np.ndarray) -> None:
    global _play_thread
    stop()
    if not HAS_SD:
        return
    def _run():
        try:
            sd.play(audio, samplerate=SR)
            sd.wait()
        except Exception:
            pass
    _play_thread = threading.Thread(target=_run, daemon=True)
    _play_thread.start()

def stop() -> None:
    if HAS_SD:
        try:
            sd.stop()
        except Exception:
            pass

# ── helpers ───────────────────────────────────────────────────────────────────
def _mode_ivs(label: str) -> list:
    for k, v in MODES.items():
        if k.lower() in label.lower():
            return v
    return MODES["Aeolian"]

def _prog_sem(label: str) -> list:
    for k, v in PROGS.items():
        clean = k.replace("♭","b")
        if label.strip().startswith(k.split()[0]) or clean.split()[0] in label:
            return v
    return PROGS["i – VII – VI – VII"]

def _find_bpm(label: str) -> int:
    for k, v in BPM_MAP.items():
        if k.lower() in label.lower():
            return v
    return 100
