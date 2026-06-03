"""Build a MIDI file from the wizard answers."""
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from pathlib import Path
from audio.engine import (
    _root_midi, _mode_ivs, _prog_sem, _find_bpm, DR, GM, MODES
)

CH_DRUMS  = 9
CH_BASS   = 1
CH_CHORDS = 0
CH_PAD    = 2
TICKS     = 480  # ticks per beat


def _velocity(label: str, default: int = 90) -> int:
    if "sparse" in label.lower() or "minimal" in label.lower():
        return 70
    if "lush" in label.lower() or "heavy" in label.lower():
        return 105
    return default


def build_midi(answers: dict, out_path: Path) -> Path:
    """Generate a 32-bar MIDI sketch and save to out_path/sketch.mid."""
    out_path.mkdir(parents=True, exist_ok=True)
    mid_file = out_path / "sketch.mid"

    root_name  = answers.get("root_key", "A")
    root       = _root_midi(root_name)
    mode_lbl   = answers.get("mode", "Aeolian — natural minor (melancholic base)")
    scale_ivs  = _mode_ivs(mode_lbl)
    prog_lbl   = answers.get("chord_prog", "i – VII – VI – VII (post-punk standard)")
    chord_prog = _prog_sem(prog_lbl)
    bpm        = _find_bpm(answers.get("tempo_range", "Drive (100–130 BPM) — post-punk energy"))
    tempo      = bpm2tempo(bpm)
    mix_dense  = answers.get("mix_density", "mid-dense")
    vel        = _velocity(mix_dense)

    mid = MidiFile(ticks_per_beat=TICKS)

    # ── track 0: tempo + time sig ──────────────────────────────────────────
    t0 = MidiTrack()
    mid.tracks.append(t0)
    t0.append(MetaMessage("set_tempo", tempo=tempo, time=0))
    t0.append(MetaMessage("track_name", name="pipeonjoy sketch", time=0))

    # ── drums ──────────────────────────────────────────────────────────────
    t_drums = MidiTrack()
    mid.tracks.append(t_drums)
    t_drums.append(MetaMessage("track_name", name="drums", time=0))

    kick_lbl  = answers.get("kick_pattern", "")
    snare_lbl = answers.get("snare_place", "2 & 4 backbeat")
    hihat_lbl = answers.get("hihat_density", "Eighth notes (standard)")

    hihat_div = 4 if "Sixteenth" in hihat_lbl else (2 if "Eighth" in hihat_lbl else 1)
    beats_per_bar  = 4
    total_bars     = 32
    total_beats    = beats_per_bar * total_bars
    beat_ticks     = TICKS

    drum_msgs: list[tuple[int, int, int, int]] = []  # (abs_tick, note, vel, on)
    for b in range(total_beats):
        bar  = b % beats_per_bar
        tick = b * beat_ticks
        # kick
        if "Polyrhythm" in kick_lbl:
            for frac in [0, TICKS*2//3, TICKS*4//3]:
                drum_msgs += [(tick+frac, DR["kick"], vel, 1),
                              (tick+frac+30, DR["kick"], 0, 0)]
        elif "Double" in kick_lbl and bar == 0:
            drum_msgs += [(tick, DR["kick"], vel, 1), (tick+25, DR["kick"], 0, 0),
                          (tick+TICKS//8, DR["kick"], vel-15, 1), (tick+TICKS//8+25, DR["kick"], 0, 0)]
        elif bar in (0, 2):
            drum_msgs += [(tick, DR["kick"], vel, 1), (tick+30, DR["kick"], 0, 0)]
        # snare
        if "1 & 3" in snare_lbl:
            if bar in (0, 2):
                drum_msgs += [(tick, DR["snare"], vel, 1), (tick+40, DR["snare"], 0, 0)]
        elif "Syncopated" in snare_lbl:
            if bar == 1:
                drum_msgs += [(tick+TICKS//2, DR["snare"], vel, 1),
                              (tick+TICKS//2+40, DR["snare"], 0, 0)]
        else:  # 2 & 4
            if bar in (1, 3):
                drum_msgs += [(tick, DR["snare"], vel, 1), (tick+40, DR["snare"], 0, 0)]
        # ghost notes
        if "Subtle" in answers.get("ghost_notes", ""):
            if bar in (0, 2):
                drum_msgs += [(tick+TICKS//3, DR["snare"], 35, 1),
                              (tick+TICKS//3+20, DR["snare"], 0, 0)]
        # hihat
        for d in range(hihat_div):
            ht = tick + beat_ticks * d // hihat_div
            drum_msgs += [(ht, DR["hihat_c"], 60, 1), (ht+15, DR["hihat_c"], 0, 0)]

    _write_abs_msgs(t_drums, drum_msgs, CH_DRUMS)

    # ── bass ───────────────────────────────────────────────────────────────
    t_bass = MidiTrack()
    mid.tracks.append(t_bass)
    t_bass.append(MetaMessage("track_name", name="bass", time=0))
    bass_prog = GM["bass"]
    t_bass.append(Message("program_change", channel=CH_BASS, program=bass_prog, time=0))

    role_lbl = answers.get("bass_role", "")
    reg_lbl  = answers.get("bass_register", "")
    bass_root = root - 12 if "Deep" in reg_lbl else (root if "Mid" in reg_lbl else root + 12)
    bass_msgs: list[tuple[int, int, int, int]] = []

    for bar_i in range(total_bars):
        chord_ivs = chord_prog[bar_i % len(chord_prog)]
        bar_tick  = bar_i * beats_per_bar * beat_ticks
        bass_note = bass_root + chord_ivs[0]
        if "Melodic" in role_lbl or "Hook" in role_lbl:
            run = [0, scale_ivs[1], scale_ivs[2], scale_ivs[4],
                   scale_ivs[4], scale_ivs[2], scale_ivs[1], 0]
            for i, s in enumerate(run):
                t  = bar_tick + i * beat_ticks // 2
                nn = bass_note + s
                bass_msgs += [(t, nn, vel, 1), (t + beat_ticks//2 - 10, nn, 0, 0)]
        elif "Walking" in role_lbl:
            for beat_n in range(4):
                t  = bar_tick + beat_n * beat_ticks
                nn = bass_root + chord_prog[(bar_i + beat_n//2) % len(chord_prog)][0]
                bass_msgs += [(t, nn, vel, 1), (t + beat_ticks - 10, nn, 0, 0)]
        else:
            bass_msgs += [(bar_tick, bass_note, vel, 1),
                          (bar_tick + beat_ticks*2, bass_note, 0, 0)]
            if "Root" not in role_lbl:
                fifth = bass_note + 7
                bass_msgs += [(bar_tick + beat_ticks*2, fifth, vel-5, 1),
                              (bar_tick + beat_ticks*4 - 10, fifth, 0, 0)]

    _write_abs_msgs(t_bass, bass_msgs, CH_BASS)

    # ── chords / pad ───────────────────────────────────────────────────────
    t_chords = MidiTrack()
    mid.tracks.append(t_chords)
    t_chords.append(MetaMessage("track_name", name="chords", time=0))
    synth_ch = answers.get("synth_char", "")
    if "FM" in synth_ch or "electric" in synth_ch.lower():
        chord_prog_gm = GM["epiano"]
    elif "cold" in synth_ch.lower():
        chord_prog_gm = GM["pad_choir"]
    else:
        chord_prog_gm = GM["pad_warm"]
    t_chords.append(Message("program_change", channel=CH_CHORDS, program=chord_prog_gm, time=0))

    chord_root = root + 12
    chord_msgs: list[tuple[int, int, int, int]] = []
    for bar_i in range(total_bars):
        sem    = chord_prog[bar_i % len(chord_prog)]
        bt     = bar_i * beats_per_bar * beat_ticks
        dur    = beats_per_bar * beat_ticks - 20
        for s in sem:
            chord_msgs += [(bt, chord_root+s, vel-10, 1),
                           (bt+dur, chord_root+s, 0, 0)]

    _write_abs_msgs(t_chords, chord_msgs, CH_CHORDS)

    mid.save(str(mid_file))
    return mid_file


def _write_abs_msgs(track: MidiTrack, msgs: list, channel: int):
    msgs.sort(key=lambda x: x[0])
    prev = 0
    for abs_t, note, vel, on in msgs:
        delta = max(0, abs_t - prev)
        kind  = "note_on" if on else "note_off"
        track.append(Message(kind, channel=channel, note=note, velocity=vel, time=delta))
        prev = abs_t
    track.append(MetaMessage("end_of_track", time=0))
