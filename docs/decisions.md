# Architecture & Product Decisions

Single living record of every significant decision made for pipeonjoy.
Add a new entry whenever a meaningful choice is locked in. Never delete old entries — mark them superseded instead.

---

## ADR-001 · Python + tkinter + PyInstaller as the application stack

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
pipeonjoy needs a GUI that runs locally, with no server, no cloud, and no subscription. It must ship as a double-click app for musicians who are not developers.

**Decision:**  
Python 3.11+ for logic and GUI (tkinter for the Win98/vaporwave skin), PyInstaller for portable distribution. No Electron, no web stack, no React.

**Consequences:**  
- Zero network surface: fully air-gappable by design.
- tkinter is ugly by default but fully styleable; the Win98 vaporwave skin is a feature, not a limitation.
- PyInstaller produces ~50 MB bundles (acceptable). Requires dylib bundling on macOS and DLL bundling on Windows.
- No hot-reload or live editing; rebuild required after Python changes.

---

## ADR-002 · No LLM at runtime — ever

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
Music composition tools increasingly lean on LLMs for suggestions. This creates cloud dependency, latency, subscription cost, and unpredictability.

**Decision:**  
All analysis and suggestion logic uses rule-based systems only: NRC Emotion Lexicon for emotion detection, VADER for sentiment, CMU Pronouncing Dictionary for syllable density. The `analyze()` function in `wizard/lyrics_analysis.py` must remain LLM-free permanently.

**Consequences:**  
- "AI-free" is a marketing differentiator, not a constraint.
- Suggestions are explainable and reproducible.
- No API key, no network call, no usage fee passed to the user.
- Rule coverage will never match an LLM's breadth; this is acceptable.

---

## ADR-003 · FluidSynth + VintageDreams SF2 for instrument previews

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
Every wizard step needs a live audio preview so the user hears each option before picking it. Pure synthesis (sine waves) sounds unconvincing.

**Decision:**  
FluidSynth (via `pyfluidsynth`) renders MIDI events through `VintageDreams.sf2` (bundled in `assets/sfz/`). Additive synthesis fallback in `audio/engine.py` is retained for environments where FluidSynth is unavailable.

**Consequences:**  
- Realistic but lightweight: 307 KB soundfont, no sample library downloads.
- FluidSynth is a C library; macOS needs `brew install fluid-synth`, Windows needs DLL bundling.
- For the PyInstaller bundle, all Homebrew dylibs are copied into `Contents/Frameworks/` and rpath-patched by `build_scripts/build_mac.sh`.
- Swap in a better soundfont anytime by dropping an `.sf2` into `assets/sfz/` — the engine picks the first valid file.

---

## ADR-004 · macOS as primary platform, Windows as v0.2

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
Broad DAW market surveys put Windows at ~63% and macOS at ~32%. However, pipeonjoy targets vaporwave, post-punk, and dark electronic producers — a demographic that skews heavily toward macOS for three concrete reasons:

1. Logic Pro (macOS-exclusive) is the #2 DAW globally and dominant in the indie/artistic production space this tool serves.
2. Apple Silicon (M1–M4) has become the default hardware for creative professionals.
3. CoreMIDI provides native virtual MIDI ports; Windows requires a separate loopMIDI install.

**Decision:**  
macOS Apple Silicon is the primary build target. All CI, testing, and build infrastructure runs macOS-first. Windows support is planned for v0.2 and will require a separate DLL bundling step (documented in `build_scripts/build_win.ps1`). Linux is community-supported only.

**Consequences:**  
- The `build_scripts/build_mac.sh` script is the authoritative release pipeline.
- Windows users can run from source today (`pip install -e .` + loopMIDI install).
- The $5 itch.io release ships macOS only at launch; Windows added in v0.2.

---

## ADR-005 · Virtual MIDI port (A+B): rtmidi + file delivery

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
Musicians need to hear wizard previews through their own DAW synths, and need MIDI clips in their DAW without manual file import friction.

**Decision:**  
Implement two complementary features:

**A — Virtual MIDI port:** `audio/midi_port.py` opens a persistent CoreMIDI virtual output named `"pipeonjoy"` at app launch. Every preview event (chord, bass run, drum pattern, guitar riff) fires to FluidSynth AND simultaneously to the virtual port in real-time via a background thread. CC 123 (All Notes Off) sent on all channels when the user navigates away from a step. Status indicator shown at the bottom of each wizard step.

**B — "Send to DAW" delivery:** After MIDI export, a DAW picker (Ableton Live / Logic Pro / Reaper / Open with default) lets the user send the `.mid` file to the target app in one click. Last choice saved to `~/.pipeonjoy/config.json`. On macOS: `open -a "App Name" file.mid`. On Windows: `subprocess.Popen` to DAW executable.

**Not in scope now:**  
- Reaper ReaScript programmatic clip insertion (v2.0)
- Plugin (VST3/AU/CLAP) — see ADR-006

**Consequences:**  
- macOS: zero additional user setup (CoreMIDI is always available).
- Windows: users need loopMIDI; pipeonjoy shows a setup dialog with download link if no virtual MIDI port is found.
- DAW-agnostic by design: any app that accepts MIDI input works with the virtual port.

---

## ADR-006 · Standalone first, thin plugin in v2.0

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
Users asked whether pipeonjoy could be distributed as both a standalone app and a DAW plugin (VST3/AU/CLAP).

**Decision:**  
Both forms are valid and complementary. The standalone does the thinking; the plugin receives MIDI from the virtual port and plays it through DAW synths. They coexist — same pattern as Surge XT.

v0.x: standalone only (Python + PyInstaller).  
v2.0: thin VST3/AU/CLAP plugin built with JUCE or DPF (C++) that subscribes to the `pipeonjoy` virtual MIDI port and optionally records incoming MIDI into a clip. The plugin does not embed the full Python wizard.

**Consequences:**  
- The virtual MIDI port (ADR-005) is the bridge between standalone and plugin.
- The plugin is a separate C++ build target, not a Python build. Architecture stays cleanly separated.
- No timeline commitment on the plugin; it follows user demand.

---

## ADR-007 · Monetization: $5 on itch.io + Ko-fi, macOS launch only

**Status:** Accepted  
**Date:** 2026-06-03

**Context:**  
pipeonjoy is GPL v3 (source always free). Charging for the convenience binary (pre-compiled, pre-bundled, double-click) is standard open-source practice.

**Decision:**  
Primary storefront: **itch.io** at $5 (pay-what-you-want, minimum $5). itch.io is the right fit: indie creative tool audience, built-in discovery for music/art tools, low fees (default 10%, configurable to lower), and community-first culture that matches the vaporwave/post-punk audience.

Secondary: **Ko-fi** as a tip jar and community hub for supporters who prefer not to use itch.io.

Future consideration: **Lemon Squeezy** if EU VAT compliance becomes a burden (it acts as Merchant of Record, handles all tax filing automatically — materially better than itch.io for international sales at scale).

**Not used:** Gumroad (10% fee, declining reputation), Buy Me a Coffee (donation-only, no real product storefront).

**v0.1 launch:** macOS `.app` only. Windows added to itch.io in v0.2.

**Consequences:**  
- GitHub Releases remain free (source + binary) — the itch.io price is for the packaged experience, not the software itself. GPL requires this.
- itch.io page needs a clear "free from source" note to avoid confusion.
- At $5 and 10% itch.io fee, net per sale is $4.50. At Ko-fi's 5% fee, net is $4.75.

---

## ADR-008 · v2.0 sample analysis: CC0 download → slow-down → key detection

**Status:** Proposed  
**Date:** 2026-06-03

**Context:**  
A powerful wizard enhancement would let users drag in a reference track, slow it down to vaporwave tempo, and auto-detect the key — pre-filling `root_key` and `mode` from the actual audio.

**Decision:**  
Deferred to v2.0. Stub lives in `wizard/sample_analysis.py`. Implementation will use:
- `yt-dlp` with Creative Commons filter for CC0/Public Domain downloads
- `librosa` for time-stretching and chroma analysis
- Krumhansl-Schmuckler algorithm for key detection

**Consequences:**  
- Adds `librosa` and `yt-dlp` as optional dependencies (heavy; not bundled in v0.x).
- Network call is explicit and user-initiated — does not violate the air-gap principle of ADR-002.

---

*Last updated: 2026-06-03 — Felipe Carvajal Brown*
