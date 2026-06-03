"""pipeonjoy — vaporwave composition wizard."""
import tkinter as tk
from tkinter import ttk, messagebox
from wizard.release import create_output_folder, suggest_track_count
from wizard.sample_analysis import launch_sample_tool

# ── vaporwave Win98 palette ───────────────────────────────────────────────────
C = {
    "desktop":   "#1a0a2e",   # deep space purple — desktop bg
    "window":    "#2d1b4e",   # slightly lighter panel
    "chrome":    "#4a2080",   # Win98 title bar shifted purple
    "title_txt": "#fffb96",   # yellow title text
    "label":     "#00ffcc",   # cyan labels
    "label_dim": "#7755aa",   # muted purple for secondary text
    "value":     "#ff77cc",   # pink for selected/important values
    "btn_bg":    "#3d1a6e",   # dark purple buttons
    "btn_fg":    "#ff77cc",   # pink button text
    "btn_active":"#5c2a9e",
    "entry_bg":  "#0d0520",
    "entry_fg":  "#00ffcc",
    "radio_sel": "#0d0520",
    "border":    "#7744aa",
    "warn":      "#ffaa44",
    "path":      "#44aaff",
}

FONT_TITLE  = ("Courier New", 16, "bold")
FONT_STEP   = ("Courier New", 13, "bold")
FONT_BODY   = ("Courier New", 10)
FONT_SMALL  = ("Courier New", 9)
FONT_MONO   = ("Courier New", 11)

STEPS = [
    ("release_type", "What are you making?", [
        "Single", "EP", "Album",
    ]),
    ("mood", "Emotional core", [
        "nostalgic / melancholic",
        "dreamy / dissociated",
        "cold / electronic",
        "euphoric / hollow",
        "lo-fi / hazed",
        "dark / heavy",
        "spiritual / slow",
    ]),
    ("mode", "Scale / mode", [
        "Aeolian — natural minor (melancholic base)",
        "Dorian — minor raised 6th (jazzy, hopeful shadow)",
        "Phrygian — dark, tense, minor ♭2",
        "Phrygian Dominant / Hijaz — Armenian, alien, flamenco",
        "Double Harmonic / Byzantine — two augmented 2nds",
        "Locrian — tritone root, maximum instability",
        "Mixolydian — major flat 7 (blues / vaporwave warmth)",
    ]),
    ("root_key", "Root key", [
        "E", "A", "D", "G", "B", "F#", "C#",
        "C", "F", "Bb", "Eb", "Ab",
    ]),
    ("tempo_range", "Tempo feel", [
        "Drift (60–80 BPM) — slowed vaporwave core",
        "Walk (80–100 BPM) — lo-fi groove",
        "Drive (100–130 BPM) — post-punk energy",
        "Aggro (140–180 BPM) — industrial / metal",
    ]),
    ("time_sig", "Time signature", [
        "4/4", "3/4", "6/8", "5/4", "7/8", "11/8", "Mixed per section",
    ]),
    ("chord_prog", "Chord progression", [
        "i – VII – VI – VII (post-punk / vaporwave standard)",
        "i – VI – III – VII (cinematic minor)",
        "i – iv – VII – III (descending bass line)",
        "i – ♭II – VII – i (Phrygian tension)",
        "i – III – ♭VII – IV (Dorian lift)",
        "I – V – vi – IV (pop loop slowed down)",
    ]),
    ("borrowed_chord", "Borrowed chords / modal mixture", [
        "None",
        "♭VI (borrow from parallel minor)",
        "♭VII (flat seven lift)",
        "iv in major (minor four — emotional punch)",
        "♭II (Neapolitan — very dark)",
    ]),
    ("modulation", "Modulation / key change", [
        "None",
        "Chromatic mediant ±3 semitones",
        "Jazz ii–V–I pivot",
        "Direct / brutal — no pivot (Gojira style)",
        "Deceptive cadence (V → ♭VI)",
    ]),
    ("pedal_tone", "Pedal tone (sustained bass note)", [
        "None",
        "Tonic pedal (root stays fixed)",
        "Dominant pedal (5th held — tension)",
    ]),
    ("groove", "Groove feel", [
        "Straight / machine-tight",
        "Swung",
        "Shuffled",
        "Quantized stiff (no humanize)",
    ]),
    ("syncopation", "Syncopation density", [
        "None — on the grid",
        "Light — occasional off-beat",
        "Moderate",
        "Heavy",
    ]),
    ("rhythmic_displacement", "Rhythmic displacement", [
        "None",
        "Shifted 1 sixteenth note",
        "Shifted 1 eighth note",
        "Custom offset",
    ]),
    ("polyrhythm", "Polyrhythm layer", [
        "None",
        "3-over-4 (Gojira triplet wash)",
        "4-over-3",
        "2-over-3 hemiola",
    ]),
    ("metric_mod", "Metric modulation mid-song", [
        "No",
        "Yes — reinterpret 8ths as triplets",
        "Yes — other feel shift",
    ]),
    ("structure", "Song sections", [
        "Intro → Verse → Chorus → Outro",
        "Intro → Verse → Chorus → Bridge → Chorus → Outro",
        "Intro → Verse → Pre-Chorus → Chorus → Bridge → Outro",
        "Minimal: Intro → Part A → Part B → Outro",
        "Instrumental (no vocal sections)",
    ]),
    ("intro_char", "Intro character", [
        "Cold open — single instrument alone",
        "Full band from bar 1",
        "Slow build from silence",
        "Drums only",
        "Sampled / field recording (v2.0)",
    ]),
    ("outro_char", "Outro treatment", [
        "Hard cut",
        "Fade",
        "Deconstruct — drop instruments one by one",
        "Loop and stutter",
    ]),
    ("kick_pattern", "Kick drum pattern", [
        "Straight 4-on-floor",
        "2-and-4 backbeat emphasis",
        "Syncopated",
        "Double-kick bursts",
        "Polyrhythmic",
    ]),
    ("snare_place", "Snare placement", [
        "2 & 4 backbeat",
        "1 & 3 push",
        "Syncopated",
        "Rimshot only",
        "Ghost notes only",
    ]),
    ("hihat_density", "Hi-hat density", [
        "Quarter notes (sparse)",
        "Eighth notes (standard)",
        "Sixteenth notes (driving)",
        "Open + close pattern",
    ]),
    ("ghost_notes", "Snare ghost notes", [
        "None",
        "Subtle — a few between main beats",
        "Heavy — funk style",
    ]),
    ("fill_freq", "Drum fill frequency", [
        "Every 4 bars",
        "Every 8 bars",
        "Minimal — Joy Division / vaporwave restraint",
    ]),
    ("bass_role", "Bass role", [
        "Melodic lead — high register (Peter Hook style)",
        "Root-locker — harmonic anchor",
        "Rhythmic pulse",
        "Walking — jazz style",
        "Counter-melody",
    ]),
    ("bass_pattern", "Bass pattern type", [
        "Scalar runs",
        "Arpeggiated chord tones",
        "Root–fifth",
        "Chromatic approach notes",
        "Pedal with fills",
    ]),
    ("bass_register", "Bass octave register", [
        "Deep low",
        "Mid (Hook style — rides above guitar)",
        "High riding",
    ]),
    ("bass_kick_rel", "Bass vs kick relationship", [
        "Locked tight",
        "Slightly ahead of kick (aggressive)",
        "Independent (rhythmic tension)",
    ]),
    ("bass_length", "Bass note length", [
        "Staccato — punchy",
        "Sustained",
        "Mixed",
    ]),
    ("guitar_texture", "Guitar texture", [
        "Angular single-note (post-punk)",
        "Sparse power chord stabs",
        "Arpeggiated clean",
        "Heavy distorted",
        "Harmonics / tremolo",
        "None — synth replaces guitar",
    ]),
    ("guitar_density", "Guitar layering", [
        "Single dry line",
        "Double-tracked",
        "Harmonized — 3rd",
        "Harmonized — tritone (dark)",
    ]),
    ("delay_type", "Guitar delay", [
        "None",
        "Slapback 100–200 ms (tight)",
        "Long 400–600 ms (atmospheric)",
        "Tape echo (lo-fi, vaporwave)",
    ]),
    ("reverb_amount", "Reverb amount", [
        "Dry",
        "Room — subtle space",
        "Hall — spacious",
        "Wash — ambient high wet (shoegaze / vapor)",
    ]),
    ("tremolo", "Tremolo / vibrato", [
        "None",
        "Subtle",
        "Heavy — surf / goth",
    ]),
    ("synth_presence", "Synth presence", [
        "None",
        "Subtle background pad",
        "Prominent texture",
        "Lead voice",
    ]),
    ("synth_role", "Synth role", [
        "Harmonic pad",
        "Bass doubling",
        "Counter-melody",
        "Rhythmic stab",
        "Ambient noise / texture",
    ]),
    ("synth_char", "Synth character", [
        "Warm analog",
        "Cold digital",
        "Detuned / detached (vaporwave classic)",
        "Granular noise",
        "FM bell / electric piano (vaporwave warmth)",
    ]),
    ("atmo_fx", "Atmospheric FX layer", [
        "None",
        "White noise swell",
        "Reversed pads",
        "Industrial clang",
        "Vinyl crackle (lo-fi / vaporwave)",
    ]),
    ("vocal_delivery", "Vocal delivery (MIDI reference only)", [
        "Monotone / spoken (Ian Curtis)",
        "Melodic minor scale",
        "Call and response",
        "Chant-like",
        "Slurred / pitch-shifted (vaporwave style)",
    ]),
    ("vocal_tessitura", "Vocal tessitura target", [
        "Low baritone",
        "Mid range",
        "Upper mid",
        "High tenor",
    ]),
    ("vocal_contour", "Vocal contour shape", [
        "Arch — rises then falls",
        "Ascending build",
        "Plateau — sustained tension",
        "Descending release",
    ]),
    ("hook_placement", "Hook placement", [
        "Chorus top",
        "Pre-chorus",
        "Outro",
        "All sections",
    ]),
    ("phrasing_density", "Vocal phrasing density", [
        "Syllabic — one note per syllable",
        "Melismatic — runs",
        "Sparse — lots of space between phrases",
    ]),
    ("call_response", "Instrument answers the vocal?", [
        "None",
        "Bass answer",
        "Guitar echo",
        "Synth pad response",
    ]),
    ("compression", "Compression character", [
        "Punchy — transient-heavy",
        "Smooth — sustain-heavy",
        "Sidechain pump (EDM / vapor)",
    ]),
    ("stereo", "Stereo picture", [
        "Mono — raw",
        "Standard wide",
        "Asymmetric (bass left, guitar right)",
        "Immersive",
    ]),
    ("mix_density", "Mix density", [
        "Sparse and dry (post-punk minimal)",
        "Mid-dense",
        "Lush and layered",
    ]),
]


class Win98Frame(tk.Frame):
    """A frame styled with raised Win98-like chrome border."""
    def __init__(self, parent, **kw):
        super().__init__(
            parent, bg=C["window"], relief="raised", bd=3,
            highlightbackground=C["border"], highlightthickness=1,
            **kw,
        )


class TitleBar(tk.Frame):
    """Fake Win98 title bar."""
    def __init__(self, parent, title: str):
        super().__init__(parent, bg=C["chrome"], relief="raised", bd=1, height=24)
        self.pack_propagate(False)
        tk.Label(
            self, text=f"  {title}", bg=C["chrome"], fg=C["title_txt"],
            font=("Courier New", 10, "bold"), anchor="w",
        ).pack(side="left", fill="y")


class PipeOnJoy(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("pipeonjoy")
        self.configure(bg=C["desktop"])
        self.resizable(False, False)

        self.answers: dict = {}
        self.step_index = 0
        self._release_name_var = tk.StringVar()
        self._song_name_var = tk.StringVar()

        self._build_name_screen()

    # ── name screen ──────────────────────────────────────────────────────────

    def _build_name_screen(self):
        self._clear()

        outer = Win98Frame(self, padx=0, pady=0)
        outer.pack(padx=12, pady=12)

        TitleBar(outer, "pipeonjoy v0.1.0 — new session").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=24, pady=18)
        inner.pack()

        tk.Label(
            inner, text="PIPEONJOY", bg=C["window"], fg=C["value"],
            font=("Courier New", 22, "bold"),
        ).pack(pady=(0, 4))
        tk.Label(
            inner, text="vaporwave composition wizard",
            bg=C["window"], fg=C["label_dim"], font=FONT_SMALL,
        ).pack(pady=(0, 18))

        _field(inner, "Release / project name:", self._release_name_var)
        _field(inner, "Song title:", self._song_name_var)

        _btn(inner, "START  ▶", self._names_confirmed).pack(anchor="e", pady=(12, 0))

    def _names_confirmed(self):
        if not self._release_name_var.get().strip() or not self._song_name_var.get().strip():
            messagebox.showwarning("pipeonjoy", "Both fields are required.")
            return
        self._build_lyrics_screen()

    # ── lyrics screen ─────────────────────────────────────────────────────────

    def _build_lyrics_screen(self):
        self._clear()
        outer = Win98Frame(self, padx=0, pady=0)
        outer.pack(padx=12, pady=12)
        TitleBar(outer, "pipeonjoy — lyrics (optional)").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=24, pady=18)
        inner.pack()

        tk.Label(inner, text="Paste your lyrics here (optional):",
                 bg=C["window"], fg=C["label"], font=FONT_BODY).pack(anchor="w")
        tk.Label(
            inner,
            text="The wizard will analyze emotion, syllable density and phrasing\n"
                 "to pre-fill suggestions — no LLM, pure lexicon + rules.\n"
                 "Leave blank for a random seeded spec.",
            bg=C["window"], fg=C["label_dim"], font=FONT_SMALL, justify="left",
        ).pack(anchor="w", pady=(2, 8))

        self._lyrics_text = tk.Text(
            inner, width=52, height=10,
            bg=C["entry_bg"], fg=C["entry_fg"], insertbackground=C["entry_fg"],
            relief="sunken", bd=2, font=FONT_SMALL, wrap="word",
        )
        self._lyrics_text.pack(fill="x")

        sep = tk.Frame(inner, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(12, 8))

        btn_row = tk.Frame(inner, bg=C["window"])
        btn_row.pack(fill="x")
        _btn(btn_row, "◀ BACK", self._build_name_screen).pack(side="left")

        # v2.0 sample tool shortcut
        _btn(btn_row, "SAMPLE TOOL (v2.0)", launch_sample_tool).pack(side="left", padx=8)

        _btn(btn_row, "ANALYZE + START ▶", self._lyrics_confirmed).pack(side="right")

    def _lyrics_confirmed(self):
        from wizard.lyrics_analysis import analyze
        lyrics = self._lyrics_text.get("1.0", "end").strip()
        suggestions = analyze(lyrics)
        # pre-fill answers; user can still change each one step by step
        self.answers = suggestions
        self._show_step()

    # ── wizard steps ─────────────────────────────────────────────────────────

    def _show_step(self):
        if self.step_index >= len(STEPS):
            self._finish()
            return
        self._clear()

        key, label, options = STEPS[self.step_index]

        outer = Win98Frame(self, padx=0, pady=0)
        outer.pack(padx=12, pady=12)

        TitleBar(outer, f"step {self.step_index + 1}/{len(STEPS)} — {key}").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=24, pady=18)
        inner.pack()

        tk.Label(
            inner, text=label, bg=C["window"], fg=C["label"],
            font=FONT_STEP, wraplength=420, justify="left",
        ).pack(anchor="w", pady=(0, 10))

        pre = self.answers.get(key, options[0])
        # if pre-fill is not in options list, fall back to first option
        if pre not in options:
            pre = options[0]
        self._choice_var = tk.StringVar(value=pre)

        for opt in options:
            is_suggested = opt == pre and key in self.answers
            color = C["value"] if is_suggested else "#dddddd"
            suffix = "  ← suggested" if is_suggested else ""
            tk.Radiobutton(
                inner, text=opt + suffix, variable=self._choice_var, value=opt,
                bg=C["window"], fg=color, selectcolor=C["radio_sel"],
                activebackground=C["window"], activeforeground=C["value"],
                font=FONT_BODY, anchor="w", cursor="hand2",
            ).pack(fill="x", pady=1)

        sep = tk.Frame(inner, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(12, 8))

        btn_row = tk.Frame(inner, bg=C["window"])
        btn_row.pack(fill="x")
        if self.step_index > 0:
            _btn(btn_row, "◀ BACK", self._back).pack(side="left")
        _btn(btn_row, "NEXT ▶", self._next).pack(side="right")

    def _next(self):
        key = STEPS[self.step_index][0]
        self.answers[key] = self._choice_var.get()
        if key == "release_type" and self.answers[key].lower() != "single":
            tip = suggest_track_count(self.answers[key].lower())
            if tip:
                messagebox.showinfo("pipeonjoy — track tip", tip)
        self.step_index += 1
        self._show_step()

    def _back(self):
        self.step_index -= 1
        self._show_step()

    # ── finish ────────────────────────────────────────────────────────────────

    def _finish(self):
        release_type = self.answers.get("release_type", "Single").lower()
        release_name = self._release_name_var.get().strip()
        song_name    = self._song_name_var.get().strip()
        out_folder   = create_output_folder(release_type, release_name, song_name)

        self._clear()
        outer = Win98Frame(self, padx=0, pady=0)
        outer.pack(padx=12, pady=12)
        TitleBar(outer, "pipeonjoy — spec complete").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=24, pady=18)
        inner.pack()

        tk.Label(inner, text="▌ SONG SPEC LOCKED", bg=C["window"],
                 fg=C["value"], font=("Courier New", 14, "bold")).pack(anchor="w")
        tk.Label(inner, text=f"output → {out_folder}", bg=C["window"],
                 fg=C["path"], font=FONT_SMALL, wraplength=420).pack(anchor="w", pady=(4, 0))

        if release_type != "single":
            tip = suggest_track_count(release_type)
            tk.Label(inner, text=tip, bg=C["window"], fg=C["warn"],
                     font=FONT_SMALL, wraplength=420).pack(anchor="w", pady=(6, 0))

        sep = tk.Frame(inner, bg=C["border"], height=1)
        sep.pack(fill="x", pady=(12, 8))

        box = tk.Frame(inner, bg=C["entry_bg"], relief="sunken", bd=2,
                       padx=10, pady=8)
        box.pack(fill="x")
        for k, v in self.answers.items():
            tk.Label(box, text=f"{k:<22} {v}", bg=C["entry_bg"],
                     fg=C["label"], font=FONT_SMALL, anchor="w").pack(fill="x")

        _btn(inner, "▶ NEW SONG", self._restart).pack(anchor="e", pady=(14, 0))

    def _restart(self):
        self.answers  = {}
        self.step_index = 0
        self._release_name_var.set("")
        self._song_name_var.set("")
        self._build_name_screen()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()


# ── widget helpers ────────────────────────────────────────────────────────────

def _field(parent, label_text, var):
    tk.Label(parent, text=label_text, bg=C["window"], fg=C["label"],
             font=FONT_BODY, anchor="w").pack(fill="x")
    tk.Entry(parent, textvariable=var, bg=C["entry_bg"], fg=C["entry_fg"],
             insertbackground=C["entry_fg"], relief="sunken", bd=2,
             font=FONT_MONO, width=38).pack(fill="x", pady=(2, 10))


def _btn(parent, text, cmd):
    return tk.Button(
        parent, text=text, command=cmd,
        bg=C["btn_bg"], fg=C["btn_fg"], activebackground=C["btn_active"],
        activeforeground=C["value"], relief="raised", bd=2,
        font=("Courier New", 10, "bold"), cursor="hand2", padx=10, pady=4,
    )


def main():
    app = PipeOnJoy()
    app.mainloop()


if __name__ == "__main__":
    main()
