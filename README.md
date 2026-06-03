# pipeonjoy

> Vaporwave composition wizard — AI-free, lyrics-driven, modal.

**pipeonjoy** walks you through ~45 music-theory decisions before generating a MIDI file. No LLM. No cloud. Everything runs locally.

---

## What it does

1. You name your release (single / EP / album) and song title.
2. Paste lyrics (optional) — the wizard analyzes emotion, syllable density, and phrasing patterns using the **NRC Emotion Lexicon**, **VADER**, and the **CMU Pronouncing Dictionary** to pre-fill suggestions.
3. Step through decisions one at a time: scale/mode (including Phrygian Dominant, Double Harmonic / Byzantine), chord progressions, tempo feel, time signature, polyrhythm, groove, instrument roles, vocal contour, and more.
4. Each step plays a short audio preview through high-quality open-source instruments.
5. When all steps are complete, the wizard exports a `.mid` file and a rendered `.wav` to `outputs/`.

For EPs and albums, the wizard recommends returning to make the remaining tracks and stores each one in the correct subfolder under `outputs/`.

---

## Musical scope

- **Post-punk / vaporwave / dark electronic** — Joy Division, Boards of Canada, Salem, 18 Carat Affair
- **Modal options** including Aeolian, Dorian, Phrygian, Phrygian Dominant (Armenian / Hijaz), Double Harmonic (Byzantine), Locrian, Mixolydian
- **Rhythmic options** including polyrhythm (3-over-4, Gojira-style), metric modulation, syncopation, displacement
- **Key change strategies** including chromatic mediant, jazz ii–V–I pivot, deceptive cadence, direct/brutal Gojira-style
- **Atmospheric FX** including vinyl crackle, reversed pads, tape echo

---

## Instrument stack

| Role | Engine | Library |
|------|--------|---------|
| Drums | sfizz (pysfizz) | MT Power Drum Kit SFZ |
| Bass guitar | sfizz | Black And Blue Basses (sfzinstruments.github.io) |
| Clean guitar | sfizz | SFZInstruments clean guitar |
| Synth pads / leads | surgepy (Surge XT) | 1000+ factory presets |
| Guitar amp coloring | NAM | Community-trained `.nam` models |

All instruments are open source or Creative Commons licensed.

---

## Install

```bash
git clone https://github.com/felipecarvajalbrown/pipeonjoy
cd pipeonjoy
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python main.py
```

Requires Python 3.11+.

---

## Outputs

```
outputs/
  singles/<song-title>/       ← single
  eps/<ep-name>/<song>/       ← EP track
  albums/<album>/<song>/      ← album track
```

Each folder receives a `.mid` and optionally a `.wav`.

---

## v2.0 roadmap

- Download CC0 / Public Domain audio from the web
- Load, slow down, and select a section in-app
- Auto-detect the key using the Krumhansl-Schmuckler algorithm
- Pre-fill root key + mode from the detected key

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Author

Felipe Carvajal Brown — Felipe Carvajal Brown Software  
fcarvajalbrown@gmail.com
