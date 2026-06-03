# Build pipeonjoy.exe for Windows.
# Run from the project root in PowerShell:  .\build_scripts\build_win.ps1
# Requires: Python 3.11+, FluidSynth Windows binary, pyinstaller
param()
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

# ── 0. preflight ─────────────────────────────────────────────────────────────
Write-Host "Activating venv..."
& ".venv\Scripts\Activate.ps1"
pip install pyinstaller --quiet

# FluidSynth for Windows: download from https://github.com/nicowillis/fluidsynth/releases
# or https://github.com/FluidSynth/fluidsynth/releases
# Place fluidsynth.dll and its companion DLLs in build_scripts\win_libs\
$WinLibs = Join-Path $PSScriptRoot "win_libs"
if (-not (Test-Path "$WinLibs\fluidsynth.dll")) {
    Write-Warning @"
FluidSynth DLL not found at build_scripts\win_libs\fluidsynth.dll
Download the Windows binary from:
  https://github.com/FluidSynth/fluidsynth/releases
Extract and copy fluidsynth.dll + companion DLLs to build_scripts\win_libs\
Then re-run this script.
"@
    exit 1
}

# ── 1. Inject Windows DLLs into spec binaries list ───────────────────────────
Write-Host "Copying Windows DLLs to project root (PyInstaller picks them up)..."
$dlls = Get-ChildItem "$WinLibs\*.dll"
foreach ($dll in $dlls) {
    Copy-Item $dll.FullName -Destination $Root -Force
}

# ── 2. PyInstaller ────────────────────────────────────────────────────────────
Write-Host "Running PyInstaller..."
pyinstaller pipeonjoy.spec --noconfirm --clean

# ── 3. Clean up temp DLLs from root ──────────────────────────────────────────
foreach ($dll in $dlls) {
    Remove-Item (Join-Path $Root $dll.Name) -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable: dist\pipeonjoy.exe"
Write-Host ""
Write-Host "To create an installer, use Inno Setup or NSIS."
Write-Host "Or zip dist\pipeonjoy.exe and distribute directly."
