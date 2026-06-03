"""pipeonjoy — vaporwave composition wizard."""
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from wizard.release import create_output_folder, suggest_track_count
from wizard.sample_analysis import launch_sample_tool
from wizard.steps import STEPS, QUICK_KEYS

# help macOS find the Homebrew FluidSynth dylib
os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

# ── single-instance lock ──────────────────────────────────────────────────────
LOCKFILE = Path(os.environ.get("TMPDIR", "/tmp")) / "pipeonjoy.lock"

def _acquire_lock() -> bool:
    if LOCKFILE.exists():
        try:
            pid = int(LOCKFILE.read_text().strip())
            os.kill(pid, 0)
            return False  # still running
        except (ValueError, OSError):
            pass  # stale lock
    LOCKFILE.write_text(str(os.getpid()))
    return True

def _release_lock():
    try:
        LOCKFILE.unlink()
    except FileNotFoundError:
        pass

# ── vaporwave Win98 palette ───────────────────────────────────────────────────
C = {
    "desktop":   "#1a0a2e",
    "window":    "#2d1b4e",
    "chrome":    "#4a2080",
    "title_txt": "#fffb96",
    "label":     "#00ffcc",
    "label_dim": "#7755aa",
    "help_fg":   "#aaddcc",
    "value":     "#ff77cc",
    "btn_bg":    "#3d1a6e",
    "btn_fg":    "#ff77cc",
    "btn_active":"#5c2a9e",
    "entry_bg":  "#0d0520",
    "entry_fg":  "#00ffcc",
    "radio_sel": "#0d0520",
    "border":    "#7744aa",
    "warn":      "#ffaa44",
    "path":      "#44aaff",
}

FT = ("Courier New", 22, "bold")
FS = ("Courier New", 13, "bold")
FB = ("Courier New", 10)
FK = ("Courier New", 9)
FM = ("Courier New", 11)


# ── widget helpers ────────────────────────────────────────────────────────────

class Win98Frame(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["window"], relief="raised", bd=3,
                         highlightbackground=C["border"], highlightthickness=1, **kw)


class TitleBar(tk.Frame):
    def __init__(self, parent, title: str):
        super().__init__(parent, bg=C["chrome"], relief="raised", bd=1, height=24)
        self.pack_propagate(False)
        tk.Label(self, text=f"  {title}", bg=C["chrome"], fg=C["title_txt"],
                 font=("Courier New", 10, "bold"), anchor="w").pack(side="left", fill="y")


def _lbl(parent, text, size=10, bold=False, color=None, wrap=470):
    color = color or C["label"]
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=C["window"], fg=color,
                    font=("Courier New", size, weight), wraplength=wrap, justify="left")


def _btn(parent, text, cmd, width=None):
    kw = {"width": width} if width else {}
    return tk.Button(parent, text=text, command=cmd,
                     bg=C["btn_bg"], fg=C["btn_fg"],
                     activebackground=C["btn_active"], activeforeground=C["value"],
                     relief="raised", bd=2, font=("Courier New", 10, "bold"),
                     cursor="hand2", padx=8, pady=4, **kw)


def _field(parent, label_text, var):
    tk.Label(parent, text=label_text, bg=C["window"], fg=C["label"],
             font=FB, anchor="w").pack(fill="x")
    tk.Entry(parent, textvariable=var, bg=C["entry_bg"], fg=C["entry_fg"],
             insertbackground=C["entry_fg"], relief="sunken", bd=2,
             font=FM, width=42).pack(fill="x", pady=(2, 10))


def _sep(parent):
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(10, 8))


# ── main app ──────────────────────────────────────────────────────────────────

class PipeOnJoy(tk.Tk):
    def __init__(self, quick_mode: bool = False):
        super().__init__()
        self.title("pipeonjoy")
        self.configure(bg=C["desktop"])
        self.minsize(600, 680)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._quick = quick_mode
        self._active_steps = (
            [s for s in STEPS if s["key"] in QUICK_KEYS]
            if quick_mode else STEPS
        )

        self.answers:  dict = {}
        self.step_idx: int  = 0

        self._release_var = tk.StringVar()
        self._song_var    = tk.StringVar()
        self._choice_var: tk.StringVar | None = None

        self._build_splash()

    # ── splash ────────────────────────────────────────────────────────────────

    def _build_splash(self):
        self._clear()
        outer = Win98Frame(self)
        outer.pack(padx=14, pady=14, fill="both", expand=True)
        TitleBar(outer, "pipeonjoy — before you start").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=30, pady=22)
        inner.pack(fill="both", expand=True)

        _lbl(inner, "PIPEONJOY", size=22, bold=True, color=C["value"]).pack()
        _lbl(inner, "vaporwave composition wizard", color=C["label_dim"], size=9).pack(pady=(2, 18))

        # ── simple example ────────────────────────────────────────────────
        box_s = tk.Frame(inner, bg="#0d1a0d", relief="sunken", bd=2, padx=12, pady=10)
        box_s.pack(fill="x", pady=(0, 8))
        _lbl(box_s, "SIMPLE  (albums can be this and still hit hard)",
             bold=True, color="#44ff88", size=10).pack(anchor="w")
        for line in [
            "Key: E minor  •  Time: 4/4  •  Tempo: 120 BPM",
            "Chord prog: i – VII – VI – VII  •  Root-lock bass",
            "Power chord guitar  •  No polyrhythm  •  Verse → Chorus → Outro",
            "→  think: Joy Division, Bauhaus, early Interpol",
        ]:
            _lbl(box_s, line, color="#99cc99", size=9).pack(anchor="w")

        # ── complex example ───────────────────────────────────────────────
        box_c = tk.Frame(inner, bg="#1a0d0d", relief="sunken", bd=2, padx=12, pady=10)
        box_c.pack(fill="x", pady=(0, 18))
        _lbl(box_c, "COMPLEX  (or go here — the wizard handles it)",
             bold=True, color=C["value"], size=10).pack(anchor="w")
        for line in [
            "Key: F# Phrygian Dominant  •  Time: 7/8  •  3-over-4 polyrhythm",
            "Chromatic mediant modulation  •  Hook-style melodic bass",
            "Byzantine double harmonic scale  •  Tape echo guitar",
            "→  think: Gojira meets Salem meets Armenian folk",
        ]:
            _lbl(box_c, line, color="#cc9999", size=9).pack(anchor="w")

        _lbl(inner, "Both are valid. The wizard works for both.  Good luck.",
             color=C["title_txt"], size=11, bold=True).pack(pady=(4, 16))

        _sep(inner)
        _btn(inner, "LET'S GO  ▶", self._build_name_screen).pack(anchor="e")

    # ── screens ───────────────────────────────────────────────────────────────

    def _build_name_screen(self):
        self._clear()
        outer = Win98Frame(self)
        outer.pack(padx=14, pady=14, fill="both", expand=True)
        TitleBar(outer, "pipeonjoy v0.1.0 — new session").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=28, pady=20)
        inner.pack(fill="both", expand=True)

        _lbl(inner, "PIPEONJOY", size=22, bold=True, color=C["value"]).pack(pady=(0, 3))
        _lbl(inner, "vaporwave composition wizard", color=C["label_dim"], size=9).pack(pady=(0, 18))

        _field(inner, "Release / project name:", self._release_var)
        _field(inner, "Song title:", self._song_var)
        _sep(inner)

        row = tk.Frame(inner, bg=C["window"])
        row.pack(fill="x")
        mode_lbl = "QUICK (10 Q)" if self._quick else "FULL (45 Q)"
        _btn(row, f"MODE: {mode_lbl}", self._toggle_mode).pack(side="left")
        _btn(row, "START  ▶", self._names_confirmed).pack(side="right")

    def _toggle_mode(self):
        from audio.engine import stop
        stop()
        self._quick = not self._quick
        self._active_steps = (
            [s for s in STEPS if s["key"] in QUICK_KEYS]
            if self._quick else STEPS
        )
        self._build_name_screen()

    def _names_confirmed(self):
        if not self._release_var.get().strip() or not self._song_var.get().strip():
            messagebox.showwarning("pipeonjoy", "Both fields are required.")
            return
        self._build_lyrics_screen()

    def _build_lyrics_screen(self):
        self._clear()
        outer = Win98Frame(self)
        outer.pack(padx=14, pady=14, fill="both", expand=True)
        TitleBar(outer, "pipeonjoy — lyrics (optional)").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=28, pady=20)
        inner.pack(fill="both", expand=True)

        _lbl(inner, "Paste your lyrics here (optional):", bold=True).pack(anchor="w")
        _lbl(inner,
             "Emotion, syllable density and phrasing will be analyzed "
             "to pre-fill suggestions — no LLM, pure lexicon + rules. "
             "Leave blank for a seeded-random spec.",
             color=C["label_dim"], size=9).pack(anchor="w", pady=(2, 8))

        self._lyrics_text = tk.Text(
            inner, width=55, height=9,
            bg=C["entry_bg"], fg=C["entry_fg"],
            insertbackground=C["entry_fg"],
            relief="sunken", bd=2, font=FK, wrap="word",
        )
        self._lyrics_text.pack(fill="x")
        _sep(inner)

        row = tk.Frame(inner, bg=C["window"])
        row.pack(fill="x")
        _btn(row, "◀ BACK", self._build_name_screen).pack(side="left")
        _btn(row, "SAMPLE (v2.0)", launch_sample_tool).pack(side="left", padx=8)
        _btn(row, "ANALYZE + START ▶", self._lyrics_confirmed).pack(side="right")

    def _lyrics_confirmed(self):
        from wizard.lyrics_analysis import analyze
        lyrics = self._lyrics_text.get("1.0", "end").strip()
        self.answers = analyze(lyrics)
        self.step_idx = 0
        self._show_step()

    # ── wizard ────────────────────────────────────────────────────────────────

    def _show_step(self):
        from audio.engine import preview_for_step, play

        if self.step_idx >= len(self._active_steps):
            self._finish()
            return

        self._clear()
        step = self._active_steps[self.step_idx]
        key, label, help_text, options = (
            step["key"], step["label"], step["help"], step["options"]
        )
        total = len(self._active_steps)

        outer = Win98Frame(self)
        outer.pack(padx=14, pady=14, fill="both", expand=True)
        TitleBar(outer, f"  step {self.step_idx + 1}/{total} — {key}").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=28, pady=18)
        inner.pack(fill="both", expand=True)

        # question label
        _lbl(inner, label, size=13, bold=True).pack(anchor="w")

        # help box
        help_frame = tk.Frame(inner, bg="#1a0a3e", relief="sunken", bd=1)
        help_frame.pack(fill="x", pady=(6, 10))
        tk.Label(help_frame, text=help_text, bg="#1a0a3e", fg=C["help_fg"],
                 font=FK, wraplength=460, justify="left", padx=8, pady=6,
                 anchor="w").pack(fill="x")

        # pre-fill default
        pre = self.answers.get(key, options[0])
        if pre not in options:
            pre = options[0]
        self._choice_var = tk.StringVar(value=pre)
        self._choice_var.trace_add("write", lambda *_: self._on_choice_change(key))

        # scrollable radio area
        radio_outer = tk.Frame(inner, bg=C["window"])
        radio_outer.pack(fill="x")
        canvas = tk.Canvas(radio_outer, bg=C["window"], highlightthickness=0,
                           height=min(len(options) * 28, 210))
        scrollbar = tk.Scrollbar(radio_outer, orient="vertical", command=canvas.yview)
        radio_frame = tk.Frame(canvas, bg=C["window"])
        radio_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=radio_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for opt in options:
            is_suggested = (opt == pre and key in self.answers)
            suffix = "  ← suggested" if is_suggested else ""
            color  = C["value"] if is_suggested else "#dddddd"
            tk.Radiobutton(
                radio_frame, text=opt + suffix,
                variable=self._choice_var, value=opt,
                bg=C["window"], fg=color, selectcolor=C["radio_sel"],
                activebackground=C["window"], activeforeground=C["value"],
                font=FB, anchor="w", cursor="hand2",
            ).pack(fill="x", pady=1)

        if len(options) > 6:
            canvas.pack(side="left", fill="x", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            canvas.pack(fill="x")

        _sep(inner)

        # button row
        row = tk.Frame(inner, bg=C["window"])
        row.pack(fill="x")
        if self.step_idx > 0:
            _btn(row, "◀ BACK", self._back).pack(side="left")
        _btn(row, "▶ PLAY", lambda: self._play_preview(key)).pack(side="left", padx=6)
        _btn(row, "NEXT ▶", self._next).pack(side="right")

        # autoplay current selection
        self.after(120, lambda: self._play_preview(key))

    def _on_choice_change(self, key: str):
        self._play_preview(key)

    def _play_preview(self, key: str):
        from audio.engine import preview_for_step, play
        if self._choice_var is None:
            return
        val = self._choice_var.get()
        try:
            audio = preview_for_step(key, val, self.answers)
            play(audio)
        except Exception:
            pass  # audio failure should never crash the wizard

    def _next(self):
        key = self._active_steps[self.step_idx]["key"]
        self.answers[key] = self._choice_var.get()

        if key == "release_type" and self.answers[key].lower() != "single":
            tip = suggest_track_count(self.answers[key].lower())
            if tip:
                messagebox.showinfo("pipeonjoy — track tip", tip)

        self.step_idx += 1
        self._show_step()

    def _back(self):
        from audio.engine import stop
        stop()
        self.step_idx -= 1
        self._show_step()

    # ── finish ────────────────────────────────────────────────────────────────

    def _finish(self):
        from audio.engine import stop
        stop()

        release_type = self.answers.get("release_type", "Single").lower()
        release_name = self._release_var.get().strip()
        song_name    = self._song_var.get().strip()
        out_folder   = create_output_folder(release_type, release_name, song_name)

        self._clear()
        outer = Win98Frame(self)
        outer.pack(padx=14, pady=14, fill="both", expand=True)
        TitleBar(outer, "pipeonjoy — spec complete").pack(fill="x")

        inner = tk.Frame(outer, bg=C["window"], padx=28, pady=20)
        inner.pack(fill="both", expand=True)

        _lbl(inner, "▌ SONG SPEC LOCKED", size=14, bold=True, color=C["value"]).pack(anchor="w")
        _lbl(inner, f"output → {out_folder}", color=C["path"], size=9).pack(anchor="w", pady=(4, 0))

        if release_type != "single":
            tip = suggest_track_count(release_type)
            _lbl(inner, tip, color=C["warn"], size=9).pack(anchor="w", pady=(6, 0))

        _sep(inner)

        # summary box
        box = tk.Frame(inner, bg=C["entry_bg"], relief="sunken", bd=2, padx=10, pady=8)
        box.pack(fill="x")
        sb = tk.Scrollbar(box)
        sb.pack(side="right", fill="y")
        lb = tk.Listbox(box, bg=C["entry_bg"], fg=C["label"], font=FK,
                        yscrollcommand=sb.set, relief="flat", height=14,
                        selectbackground=C["chrome"])
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)
        for k, v in self.answers.items():
            lb.insert("end", f"  {k:<22} {v}")

        _sep(inner)

        btn_row = tk.Frame(inner, bg=C["window"])
        btn_row.pack(fill="x")
        _btn(btn_row, "▶ NEW SONG", self._restart).pack(side="left")
        self._export_status = tk.StringVar(value="")
        tk.Label(btn_row, textvariable=self._export_status,
                 bg=C["window"], fg=C["warn"], font=FK).pack(side="left", padx=10)
        _btn(btn_row, "EXPORT MIDI + WAV", lambda: self._export(out_folder)).pack(side="right")

    def _export(self, out_folder: Path):
        self._export_status.set("generating MIDI…")
        self.update_idletasks()

        def _run():
            try:
                from generator.midi_export import build_midi
                from generator.wav_render  import render_wav
                mid = build_midi(self.answers, out_folder)
                self.after(0, lambda: self._export_status.set("rendering WAV…"))
                wav = render_wav(mid, out_folder)
                msg = f"✓ {mid.name}" + (f"  +  {wav.name}" if wav else "  (WAV needs FluidSynth)")
            except Exception as e:
                msg = f"export error: {e}"
            self.after(0, lambda: self._export_status.set(msg))

        threading.Thread(target=_run, daemon=True).start()

    def _restart(self):
        self.answers  = {}
        self.step_idx = 0
        self._release_var.set("")
        self._song_var.set("")
        self._build_name_screen()

    # ── utilities ─────────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _on_close(self):
        from audio.engine import stop
        stop()
        _release_lock()
        self.destroy()


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    if not _acquire_lock():
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("pipeonjoy", "pipeonjoy is already running.")
        root.destroy()
        sys.exit(0)

    app = PipeOnJoy()
    try:
        app.mainloop()
    finally:
        _release_lock()


if __name__ == "__main__":
    main()
