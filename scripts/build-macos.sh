#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  SwiftReply — macOS Build Script
#  Produces: SwiftReply_1.0.0_universal.dmg (Intel + Apple Silicon)
#
#  Requirements:
#    - macOS 11+ (Big Sur or later)
#    - Xcode Command Line Tools: xcode-select --install
#    - Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
#    - Rust targets:
#        rustup target add x86_64-apple-darwin
#        rustup target add aarch64-apple-darwin
#    - Node.js 18+ and npm
#    - Python 3.11+
#    - (Optional) Apple Developer ID for notarization
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
FRONTEND="$ROOT/frontend"
BACKEND="$ROOT/backend"
OUTPUT="$ROOT/dist/macos"

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   SwiftReply — macOS Builder          ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

cd "$ROOT"

# ── Step 1: Bundle Python backend ──────────────────────────────
echo "  [1/5] Bundling Python backend..."
cd "$BACKEND"
pip3 install pyinstaller --quiet
pip3 install -r requirements.txt --quiet
pyinstaller swiftreply.spec \
    --distpath "$ROOT/backend-bundled" \
    --clean -y \
    --target-arch universal2  # Universal binary (Intel + M1/M2)
echo "        Backend bundled ✓"

# ── Step 2: Install frontend deps ──────────────────────────────
echo "  [2/5] Installing frontend dependencies..."
cd "$FRONTEND"
npm install --silent
echo "        Dependencies installed ✓"

# ── Step 3: Add Rust universal targets ─────────────────────────
echo "  [3/5] Adding Rust cross-compile targets..."
rustup target add x86_64-apple-darwin  2>/dev/null || true
rustup target add aarch64-apple-darwin 2>/dev/null || true
echo "        Rust targets ready ✓"

# ── Step 4: Copy backend resources ─────────────────────────────
echo "  [4/5] Copying backend into Tauri resources..."
mkdir -p "$FRONTEND/src-tauri/resources/backend"
cp -r "$ROOT/backend-bundled/swiftreply-backend/" "$FRONTEND/src-tauri/resources/backend/"
chmod +x "$FRONTEND/src-tauri/resources/backend/swiftreply-backend"
echo "        Resources copied ✓"

# ── Step 5: Build universal macOS app ──────────────────────────
echo "  [5/5] Building universal macOS app (Intel + Apple Silicon)..."
cd "$FRONTEND"
npm run tauri:build:mac
echo "        macOS app built ✓"

# ── Collect outputs ─────────────────────────────────────────────
mkdir -p "$OUTPUT"
find "$FRONTEND/src-tauri/target" -name "*.dmg" -exec cp {} "$OUTPUT/" \; 2>/dev/null || true
find "$FRONTEND/src-tauri/target" -name "*.app" -maxdepth 6 -exec cp -r {} "$OUTPUT/" \; 2>/dev/null || true

echo ""
echo "  ✅ macOS build complete!"
echo "  📦 Output: $OUTPUT"
echo ""
ls -lh "$OUTPUT" 2>/dev/null || echo "  (Check src-tauri/target/ for outputs)"
echo ""

# Optional: Notarize for Gatekeeper (requires Apple Developer Account)
# xcrun notarytool submit "$OUTPUT/*.dmg" \
#   --apple-id "$APPLE_ID" \
#   --password "$APPLE_APP_PASSWORD" \
#   --team-id "$APPLE_TEAM_ID" \
#   --wait
