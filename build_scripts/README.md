# Building portable releases

## macOS (.app + .dmg)

```bash
# Prerequisites
brew install fluid-synth create-dmg

# From the project root
bash build_scripts/build_mac.sh
```

Output: `dist/pipeonjoy.app` and `dist/pipeonjoy.dmg`

**First-launch note:** the app is ad-hoc signed (no Apple Developer account).
Users on macOS 13+ need to right-click → Open on first launch to bypass Gatekeeper.
For fully trusted distribution, enroll in the Apple Developer Program ($99/yr) and
notarize with `xcrun notarytool`.

## Windows (.exe)

1. Download the FluidSynth Windows binary from  
   https://github.com/FluidSynth/fluidsynth/releases  
   (choose the latest `fluidsynth-*-win10-x64.zip`)

2. Extract and copy `fluidsynth.dll` + companion `.dll` files into  
   `build_scripts/win_libs/`

3. From the project root in PowerShell:
   ```powershell
   .\build_scripts\build_win.ps1
   ```

Output: `dist/pipeonjoy.exe` (single file, ~40–60 MB)

## Linux (AppImage — planned)

Not automated yet. Rough steps:
```bash
pip install pyinstaller
pyinstaller pipeonjoy.spec --noconfirm
# Then use appimagetool or briefcase to wrap dist/pipeonjoy/
```

## What gets bundled

| Asset | Source | Bundle path |
|-------|--------|-------------|
| VintageDreams.sf2 | `assets/sfz/` | `assets/sfz/` |
| nrc_en.json | `.venv/.../nrclex/data/` | `nrclex/data/` |
| libfluidsynth | `/opt/homebrew/lib/` | `Contents/Frameworks/` |
| glib, sndfile, portaudio, … | Homebrew | `Contents/Frameworks/` |

## After the build

Test the app thoroughly before releasing:
- [ ] Splash screen loads
- [ ] Audio plays on mode step
- [ ] Audio plays on guitar step
- [ ] Drum steps are audible
- [ ] MIDI + WAV export works
- [ ] Single-instance lock works (second launch shows warning)
