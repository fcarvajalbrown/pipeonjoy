# pipeonjoy Roadmap

Items are ordered by priority within each release. Dates are targets, not promises.

---

## v0.1.x — Current (shipped)

- [x] 45-step music-theory wizard (mode, key, tempo, groove, polyrhythm, structure, drums, bass, guitar, synth, vocal reference)
- [x] 10-question Quick Mode
- [x] Win98/vaporwave tkinter GUI
- [x] Live FluidSynth previews — GeneralUser GS soundfont, every option plays on click
- [x] Guitar previews with Overdriven Guitar GM patch
- [x] Vocal reference previews using lead voice / choir GM patches
- [x] Lyrics analysis: NRC Emotion Lexicon + VADER + CMU Pronouncing Dictionary (no LLM)
- [x] Random button (seeded from song name)
- [x] Splash screen with 18 real album examples across three complexity tiers
- [x] 32-bar MIDI export (drums, bass, chords)
- [x] WAV render via FluidSynth CLI + pydub master chain (normalize, compress, fade)
- [x] Release-type output folder logic: `outputs/singles/`, `outputs/eps/`, `outputs/albums/`
- [x] Single-instance lockfile
- [x] PyInstaller build: macOS `.app` + `.dmg`, Windows `.exe` via GitHub Actions
- [x] GitHub Releases: macOS arm64 binary
- [x] Architecture Decision Records: `docs/decisions.md`

---

## v0.2 — Next

**Stem mixer panel** *(first priority)*
- After export, a mixer panel with one fader per instrument (drums, bass, guitar, chords/pad, master)
- Per-instrument play/mute, volume, pan
- Re-render WAV with new levels without re-running the wizard
- Stems stored in `outputs/.../stems/`

**Virtual MIDI port A — live preview into DAW**
- `audio/midi_port.py`: persistent CoreMIDI virtual output named `"pipeonjoy"`
- Every wizard step preview fires simultaneously to FluidSynth AND the virtual port
- All Notes Off (CC 123) sent when navigating between steps — no hanging notes
- Status indicator at bottom of each wizard step
- Windows: setup dialog linking to loopMIDI if no virtual port found

**Virtual MIDI port B — "Send to DAW" file delivery**
- DAW picker on finish screen: Ableton Live / Logic Pro / Reaper / Open with default
- `open -a "Ableton Live" sketch.mid` on macOS, `os.startfile()` on Windows
- Last DAW choice saved to `~/.pipeonjoy/config.json`
- "Reveal in Finder / Explorer" fallback link

**Interactive story arc graph**
- Before the wizard steps, user plots an energy curve across sections (1–5 intensity per section)
- The curve shape pre-fills dynamics decisions (compression, mix density, build/drop placement)
- ASCII canvas editor in the wizard UI

**Windows v0.2 binary release**
- Proper Windows `.exe` with FluidSynth DLLs bundled
- Listed on GitHub Releases

**Sample analysis (CC0 tracks)** *(stub currently in `wizard/sample_analysis.py`)*
- Download CC0 / Public Domain audio via yt-dlp or Free Music Archive API
- Load into librosa, display waveform, user selects + slows down a section
- Key detection via Krumhansl-Schmuckler algorithm
- Detected key pre-fills `root_key` + `mode` in the wizard

---

## v0.3 — Planned

**Thin DAW plugin (VST3 / AU / CLAP)**
- Lightweight C++ plugin (JUCE or DPF) that subscribes to the `pipeonjoy` virtual MIDI port
- Appears in Ableton/Logic/Reaper plugin browser
- Does not embed the full wizard — standalone does the thinking, plugin receives MIDI
- First targets: macOS AU + VST3, Windows VST3

**Reaper ReaScript integration**
- After export, inserts MIDI directly into the active Reaper project via Python ReaScript API
- No drag-and-drop needed for Reaper users

**Per-instrument FX** *(built on stem mixer)*
- Reverb send per track
- Simple EQ (low/mid/high shelf per instrument)
- Re-render with new FX applied

**Oddvoices vocal synthesis integration**
- Replace GM choir/voice patches with Oddvoices (open source singing synthesis)
- User provides phonemes/syllables for the vocal reference line
- Output: an actual synthesized vocal melody guide, not just a MIDI pitch line

---

## v1.0 — Commercial release

**itch.io listing at $5**
- macOS `.dmg` + Windows `.exe` as paid convenience builds
- Source always free (GPL v3) — price is for the packaged experience
- "Pay what you want" minimum $5

**Ko-fi page**
- Tip jar + supporter community for users who prefer not to use itch.io

**Lemon Squeezy** *(if EU VAT compliance needed at scale)*
- Acts as Merchant of Record — handles all international tax filing automatically

**Plugin marketplace listings**
- KVR Audio: standalone utility category
- Plugin Boutique: composition tools category

**Notarized macOS build**
- Apple Developer Program enrollment ($99/yr)
- `xcrun notarytool` notarization — removes Gatekeeper right-click requirement

---

## Backlog (no version assigned)

- Linux AppImage build
- Localization (Spanish first — Chilean market)
- Custom soundfont picker in settings
- Export to Ableton Live Set format (`.als`) directly
- Per-song notes / lyrics field stored with spec JSON
- Light mode (Win98 silver instead of vaporwave purple)
- MIDI import: analyze an existing MIDI and pre-fill wizard from it

---

*Platform priority: macOS arm64 first, Windows x64 second, Linux community-supported.*  
*See `docs/decisions.md` for the reasoning behind each major architectural choice.*
