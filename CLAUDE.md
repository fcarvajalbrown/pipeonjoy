# CLAUDE.md

Guidance for Claude Code when working in this repo.

## Architecture decisions

All significant product and technical decisions are recorded in [`docs/decisions.md`](docs/decisions.md).
Read it before proposing changes that touch platform targets, audio engine, MIDI routing, distribution, or monetization.
When a decision changes, update that file — do not leave it stale.

## Identity

- **Author:** Felipe Carvajal Brown
- **Company:** Felipe Carvajal Brown Software
- **Email:** fcarvajalbrown@gmail.com
- **License:** GNU GPL v3

## Rules

**Work sequentially** — one tool call at a time, never parallel.

**Never assume** — if any detail is unclear, ask before implementing.

**Never force-push** without telling the user and waiting for confirmation.

**One commit per logical change** — no layer-split commits.

**"Add to AGENTS.md"** means write to that file locally and stop — do not commit or push unless explicitly asked.

## Commits

`<type>(<scope>): <description>` — lowercase, present-tense imperative.
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.

No `Co-Authored-By` trailers. No AI attribution in commit messages or PR descriptions.

## What this is

pipeonjoy is an AI-free vaporwave composition wizard. It walks the user through ~45 music-theory decisions (mode, key, groove, structure, instrument roles, vocal contour) one at a time in a Windows-98-styled tkinter GUI, optionally pre-filling suggestions by analyzing lyrics using the NRC Emotion Lexicon + VADER + CMU Pronouncing Dictionary. Final output is a MIDI file rendered through sfizz (sample-based) + surgepy (Surge XT synth).

## Architecture

```
main.py                     # tkinter GUI entry point — Win98/vaporwave skin
wizard/
  release.py                # release-type logic (single/EP/album) → outputs/ folder
  lyrics_analysis.py        # NRC + VADER + pronouncing → music param suggestions
  sample_analysis.py        # v2.0 stub — CC sample download, slow-down, key detect
audio/
  engine.py                 # sfizz + surgepy + sounddevice real-time playback
  instruments.py            # SFZ / Surge preset loader
  mixer.py                  # combines instrument audio buffers
theory/
  modes.py                  # mode/scale interval tables
  chords.py                 # chord progression builder
  rhythm.py                 # drum + bass pattern templates
  melody.py                 # vocal reference contour generator
generator/
  midi_export.py            # final .mid export after all answers collected
assets/
  sfz/                      # MT Power Drum Kit, Black & Blue Basses, guitar SFZ
  surge/                    # Surge XT presets
  nam/                      # Neural Amp Modeler .nam models (guitar amp coloring)
outputs/                    # generated MIDI + WAV per song (gitignored)
  singles/<song>/
  eps/<release>/<song>/
  albums/<release>/<song>/
```

## Build & develop

Always use the `.venv` at the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
pip install -e ".[dev]"
python main.py
```

## Tests

```bash
pytest tests/ -v
```

## Code style

- Comments: 1-line max, no block comments.
- Bug fixes: root cause only — never patch tests to make them pass.
- Never write code just to make it run; code must reflect real behavior.

## v2.0 features (not yet implemented)

See `wizard/sample_analysis.py` for the stub. Goals:
1. Download CC0/Public Domain audio via yt-dlp or Free Music Archive API
2. Load into librosa, let user select + slow down a section
3. Detect key with Krumhansl-Schmuckler algorithm
4. Pre-fill root key + mode in the wizard from the detected key
