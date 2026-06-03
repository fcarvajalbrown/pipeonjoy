#!/usr/bin/env bash
# Build pipeonjoy.app + pipeonjoy.dmg for macOS (Apple Silicon or Intel).
# Run from the project root:  bash build_scripts/build_mac.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── 0. preflight ─────────────────────────────────────────────────────────────
source .venv/bin/activate
pip install pyinstaller --quiet

command -v fluidsynth >/dev/null 2>&1 || { echo "Error: install FluidSynth first: brew install fluid-synth"; exit 1; }

# Detect Homebrew prefix (Intel vs Apple Silicon)
BREW="$(brew --prefix)"

# Homebrew dylibs FluidSynth depends on
DYLIBS=(
    "$BREW/lib/libfluidsynth.3.dylib"
    "$BREW/opt/glib/lib/libglib-2.0.0.dylib"
    "$BREW/opt/glib/lib/libgthread-2.0.0.dylib"
    "$BREW/opt/gettext/lib/libintl.8.dylib"
    "$BREW/opt/libsndfile/lib/libsndfile.1.dylib"
    "$BREW/opt/portaudio/lib/libportaudio.2.dylib"
    "$BREW/opt/readline/lib/libreadline.8.dylib"
)

# ── 1. PyInstaller ────────────────────────────────────────────────────────────
echo "▶ Running PyInstaller..."
pyinstaller pipeonjoy.spec --noconfirm --clean

APP="$ROOT/dist/pipeonjoy.app"
MACOS_DIR="$APP/Contents/MacOS"
FRAMEWORKS="$APP/Contents/Frameworks"
mkdir -p "$FRAMEWORKS"

# ── 2. Copy Homebrew dylibs into Frameworks/ ─────────────────────────────────
echo "▶ Copying dylibs to Frameworks/..."
for dylib in "${DYLIBS[@]}"; do
    if [ -f "$dylib" ]; then
        cp -f "$dylib" "$FRAMEWORKS/"
        echo "  copied $(basename "$dylib")"
    else
        echo "  WARNING: $dylib not found, skipping"
    fi
done

# ── 3. Patch load commands so dylibs reference each other inside the bundle ───
echo "▶ Patching rpath (install_name_tool)..."

patch_binary() {
    local target="$1"
    for dylib in "${DYLIBS[@]}"; do
        local basename
        basename="$(basename "$dylib")"
        local new_ref="@executable_path/../Frameworks/$basename"

        # Replace absolute Homebrew paths with @executable_path-relative refs
        # Try both /opt/homebrew and /usr/local prefixes
        for prefix in "$BREW" "/usr/local" "/opt/homebrew"; do
            local old
            old="$(otool -L "$target" 2>/dev/null | awk '{print $1}' | grep "${basename}$" | head -1)"
            if [ -n "$old" ]; then
                install_name_tool -change "$old" "$new_ref" "$target" 2>/dev/null || true
            fi
        done
    done
}

# Patch the main executable
patch_binary "$MACOS_DIR/pipeonjoy"

# Patch each bundled dylib (they reference each other)
for dylib in "${DYLIBS[@]}"; do
    bundled="$FRAMEWORKS/$(basename "$dylib")"
    if [ -f "$bundled" ]; then
        # Fix the dylib's own install name
        install_name_tool -id "@executable_path/../Frameworks/$(basename "$dylib")" "$bundled" 2>/dev/null || true
        patch_binary "$bundled"
    fi
done

# ── 4. Ad-hoc code sign (no Apple Developer account required) ─────────────────
echo "▶ Ad-hoc code signing..."
codesign --deep --force --sign - "$APP" 2>/dev/null || true
echo "  Note: app is ad-hoc signed. On first launch users may need to:"
echo "  right-click → Open  (to bypass Gatekeeper on first run)"

# ── 5. Create DMG ────────────────────────────────────────────────────────────
if command -v create-dmg &>/dev/null; then
    echo "▶ Creating DMG..."
    rm -f "$ROOT/dist/pipeonjoy.dmg"
    create-dmg \
        --volname "pipeonjoy 0.1.0" \
        --window-size 660 420 \
        --icon-size 120 \
        --icon "pipeonjoy.app" 200 180 \
        --app-drop-link 450 180 \
        --background-color "#1a0a2e" \
        "$ROOT/dist/pipeonjoy.dmg" \
        "$APP"
    echo "✓ DMG → dist/pipeonjoy.dmg"
else
    echo "▶ Skipping DMG (install create-dmg: brew install create-dmg)"
    echo "✓ App bundle → dist/pipeonjoy.app"
fi

echo ""
echo "Build complete."
echo "App size: $(du -sh "$APP" | cut -f1)"
