<p align="center">
  <img src="assets/logo.svg" alt="pipeonjoy" width="420"/>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--v3-b967ff?style=flat-square" alt="License: GPL v3"/></a>
  <img src="https://img.shields.io/badge/python-3.11+-01cdfe?style=flat-square" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-ff77cc?style=flat-square" alt="Platform"/>
</p>

<p align="center"><strong>Vaporwave composition wizard — AI-free, lyrics-driven, modal.</strong></p>

---

**pipeonjoy** walks you through ~45 music-theory decisions before generating a MIDI file and a rendered WAV. No LLM. No cloud. Everything runs locally and air-gapped.

---

## What it does

1. **Name your release** — single, EP, or album; each gets its own output folder.
2. **Paste lyrics** (optional) — emotion, syllable density, and phrasing are analyzed using the NRC Emotion Lexicon, VADER, and the CMU Pronouncing Dictionary to pre-fill suggestions. No LLM.
3. **Step through ~45 decisions** one at a time: scale/mode, key, tempo, groove, polyrhythm, song structure, drum patterns, bass role, guitar texture, synth character, vocal contour, and more.
4. **Hear every option** — each radio button plays a live FluidSynth preview using a real soundfont the moment you click it.
5. **Export** — a 32-bar MIDI sketch + mastered WAV land in `outputs/` when you're done.

For EPs and albums the wizard reminds you to return and make the remaining tracks, storing each one in the correct subfolder.

---

## Musical scope

- **Post-punk / vaporwave / dark electronic** — Joy Division, Boards of Canada, Salem, 18 Carat Affair
- **Modes**: Aeolian, Dorian, Phrygian, Phrygian Dominant (Armenian / Hijaz), Double Harmonic (Byzantine), Locrian, Mixolydian
- **Rhythm**: polyrhythm (3-over-4, Gojira-style), metric modulation, syncopation, rhythmic displacement
- **Harmony**: chromatic mediant, jazz ii–V–I pivot, deceptive cadence, direct/brutal key changes
- **Atmosphere**: vinyl crackle, reversed pads, tape echo, wash reverb

Both extremes work — and everything in between:

| Simple | Complex |
|--------|---------|
| E minor · 4/4 · 120 BPM | F# Phrygian Dominant · 7/8 |
| i–VII–VI–VII · root-lock bass | 3-over-4 polyrhythm · Hook-style bass |
| Power chord guitar · verse–chorus | Chromatic mediant modulation · tape echo |
| → Joy Division, Bauhaus | → Gojira meets Salem meets Armenian folk |

---

## Instrument stack

| Role | Engine | Source |
|------|--------|--------|
| Drums | FluidSynth (GM ch. 10) | VintageDreams SF2 (bundled with FluidSynth) |
| Bass guitar | FluidSynth GM program 33 | same soundfont |
| Chords / pads | FluidSynth GM programs 88–92 | same soundfont |
| Preview synthesis | additive fallback | pure Python (no dependencies) |

Swap in any SF2 soundfont by dropping it in `assets/sfz/`.

---

## Install

```bash
git clone https://github.com/fcarvajalbrown/pipeonjoy
cd pipeonjoy
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# macOS: install FluidSynth for realistic instrument previews + WAV export
brew install fluid-synth

python main.py
```

Requires **Python 3.11+**.  
FluidSynth is optional — the wizard falls back to additive synthesis if it is absent.

---

## Outputs

```
outputs/
  singles/<song-title>/       ← sketch.mid  sketch.wav
  eps/<ep-name>/<song>/
  albums/<album>/<song>/
```

---

## v2.0 roadmap

- Download CC0 / Public Domain audio from the web (yt-dlp / Free Music Archive)
- Load, slow down, and select a section in-app (librosa)
- Auto-detect key via Krumhansl-Schmuckler algorithm → pre-fill root key + mode
- Interactive story-arc graph editor (energy curve across sections)
- Portable executable builds (PyInstaller — macOS `.app`, Windows `.exe`)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). One rule above all: **no LLM calls at runtime** and **no network calls at runtime** — pipeonjoy must remain 100% air-gappable.

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Author

Felipe Carvajal Brown — Felipe Carvajal Brown Software  
fcarvajalbrown@gmail.com
