# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-03

### Added
- Win98-style vaporwave tkinter GUI with deep-purple / hot-pink / cyan palette
- 45-step composition wizard covering mode, key, tempo, groove, polyrhythm, structure, drums, bass, guitar, synth, and vocal reference
- 10-question Quick Mode for rapid sketching
- Lyrics analysis engine: NRC Emotion Lexicon + VADER + CMU Pronouncing Dictionary → pre-filled suggestions (no LLM)
- FluidSynth + VintageDreams SF2 live preview — every radio option plays a distinct sound on selection
- Additive synthesis fallback when FluidSynth is unavailable
- Per-step help text explaining the musical meaning of each choice
- 32-bar MIDI export (drums, bass, chords) from wizard answers
- WAV render via FluidSynth CLI + pydub normalize/compress/fade master chain
- Release-type output folder logic: `outputs/singles/`, `outputs/eps/`, `outputs/albums/`
- Single-instance lockfile to prevent duplicate windows
- Splash screen with simple vs. complex song examples
- v2.0 sample analysis stub: CC0 download → slow-down → key detection (planned)
