# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for pipeonjoy.
Run from the project root with the .venv active:
    pyinstaller pipeonjoy.spec --noconfirm
Then use build_scripts/build_mac.sh (or build_win.ps1) to bundle dylibs and package.
"""

import sys
from pathlib import Path

ROOT = Path(".").resolve()

# ── data files to bundle ──────────────────────────────────────────────────────
datas = [
    # soundfont
    (str(ROOT / "assets" / "sfz" / "VintageDreams.sf2"), "assets/sfz"),
    # logo
    (str(ROOT / "assets" / "logo.svg"), "assets"),
    # NRC emotion lexicon (bypasses NLTK dependency)
    (str(ROOT / ".venv" / "lib" / "python3.13" / "site-packages" / "nrclex" / "data" / "nrc_en.json"),
     "nrclex/data"),
    # VADER lexicon
    (str(ROOT / ".venv" / "lib" / "python3.13" / "site-packages" / "vaderSentiment"),
     "vaderSentiment"),
    # wizard / audio / generator source packages
    (str(ROOT / "wizard"),    "wizard"),
    (str(ROOT / "audio"),     "audio"),
    (str(ROOT / "generator"), "generator"),
]

# ── analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],          # dylibs injected by build_mac.sh after this step
    datas=datas,
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "fluidsynth",
        "sounddevice",
        "mido",
        "mido.backends",
        "mido.backends.rtmidi",
        "numpy",
        "nrclex",
        "vaderSentiment",
        "vaderSentiment.vaderSentiment",
        "pronouncing",
        "pydub",
        "pydub.effects",
        "wizard.steps",
        "wizard.release",
        "wizard.lyrics_analysis",
        "wizard.sample_analysis",
        "audio.engine",
        "generator.midi_export",
        "generator.wav_render",
    ],
    hookspath=[],
    excludes=["matplotlib", "scipy", "PIL", "IPython", "jupyter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# ── macOS .app bundle ─────────────────────────────────────────────────────────
if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="pipeonjoy",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,          # windowed app — no terminal window
        icon=None,              # add .icns here when available
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="pipeonjoy",
    )

    app = BUNDLE(
        coll,
        name="pipeonjoy.app",
        bundle_identifier="com.felipecarvajalbrown.pipeonjoy",
        version="0.1.0",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
            "CFBundleDisplayName": "pipeonjoy",
            "CFBundleShortVersionString": "0.1.0",
            "NSHumanReadableCopyright": "© 2026 Felipe Carvajal Brown. GPL v3.",
            "LSMinimumSystemVersion": "11.0",
        },
    )

# ── Windows .exe ──────────────────────────────────────────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="pipeonjoy",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon=None,              # add .ico here when available
    )
