#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  SwiftReply — Android Build Script
#  Produces:
#    dist/android/SwiftReply-1.0.0-debug.apk    (sideload / testing)
#    dist/android/SwiftReply-1.0.0-release.aab  (Google Play Store)
#
#  Requirements:
#    - Node.js 18+ and npm
#    - Java 17+: sudo apt install openjdk-17-jdk  (Linux)
#                brew install openjdk@17           (macOS)
#    - Android Studio OR Android SDK command line tools
#    - ANDROID_HOME env var pointing to SDK
#    - (For release) Keystore file — see instructions below
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
FRONTEND="$ROOT/frontend"
OUTPUT="$ROOT/dist/android"
APP_VERSION="1.0.0"

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   SwiftReply — Android Builder        ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# ── Check ANDROID_HOME ─────────────────────────────────────────
if [ -z "$ANDROID_HOME" ]; then
    # Try common locations
    if [ -d "$HOME/Library/Android/sdk" ]; then
        export ANDROID_HOME="$HOME/Library/Android/sdk"
    elif [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
    else
        echo "  ❌ ANDROID_HOME not set. Install Android Studio and set:"
        echo "     export ANDROID_HOME=\$HOME/Library/Android/sdk   # macOS"
        echo "     export ANDROID_HOME=\$HOME/Android/Sdk            # Linux"
        exit 1
    fi
fi
export PATH="$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0"
echo "  ANDROID_HOME: $ANDROID_HOME"

# ── Step 1: Install frontend deps ──────────────────────────────
echo "  [1/4] Installing frontend dependencies..."
cd "$FRONTEND"
npm install --silent
echo "        Done ✓"

# ── Step 2: Build React web app ────────────────────────────────
echo "  [2/4] Building React web app..."
npm run build
echo "        Build complete ✓"

# ── Step 3: Sync to Android project ────────────────────────────
echo "  [3/4] Syncing to Android project..."
# Add android platform if not present
if [ ! -d "$FRONTEND/android" ]; then
    echo "        Adding Android platform..."
    npx cap add android
fi
npx cap sync android
echo "        Sync complete ✓"

# ── Step 4: Build APK and AAB ──────────────────────────────────
echo "  [4/4] Building Android APK (debug) and AAB (release)..."
cd "$FRONTEND/android"

# Ensure gradlew is executable
chmod +x gradlew

# Build debug APK (for direct installation / testing)
echo "        Building debug APK..."
./gradlew assembleDebug --quiet

# Build release AAB (for Google Play Store)
echo "        Building release AAB..."
./gradlew bundleRelease --quiet

echo "        Build complete ✓"

# ── Collect outputs ─────────────────────────────────────────────
mkdir -p "$OUTPUT"

# Debug APK
find "$FRONTEND/android/app/build/outputs/apk/debug" -name "*.apk" | while read f; do
    cp "$f" "$OUTPUT/SwiftReply-${APP_VERSION}-debug.apk"
    echo "  📦 APK: $OUTPUT/SwiftReply-${APP_VERSION}-debug.apk"
done

# Release AAB
find "$FRONTEND/android/app/build/outputs/bundle/release" -name "*.aab" | while read f; do
    cp "$f" "$OUTPUT/SwiftReply-${APP_VERSION}-release.aab"
    echo "  📦 AAB: $OUTPUT/SwiftReply-${APP_VERSION}-release.aab"
done

echo ""
echo "  ✅ Android build complete!"
echo ""
echo "  ┌─ How to install APK on device ─────────────────────────┐"
echo "  │  Enable 'Install from unknown sources' on device       │"
echo "  │  adb install $OUTPUT/SwiftReply-${APP_VERSION}-debug.apk │"
echo "  └────────────────────────────────────────────────────────┘"
echo ""
echo "  ┌─ How to publish AAB to Play Store ─────────────────────┐"
echo "  │  1. Sign the AAB with your keystore (see below)        │"
echo "  │  2. Upload to Google Play Console                      │"
echo "  │  3. Create a release in 'Production' track             │"
echo "  └────────────────────────────────────────────────────────┘"
echo ""

# ── Generate debug keystore if missing ─────────────────────────
if [ ! -f "$FRONTEND/android/app/debug.keystore" ]; then
    echo "  Generating debug keystore..."
    keytool -genkey -v \
        -keystore "$FRONTEND/android/app/debug.keystore" \
        -alias androiddebugkey \
        -keyalg RSA -keysize 2048 \
        -validity 10000 \
        -storepass android -keypass android \
        -dname "CN=SwiftReply Debug, OU=, O=, L=, S=, C=" \
        2>/dev/null
    echo "  Debug keystore created ✓"
fi

echo "  ┌─ Generate production keystore (one time) ──────────────┐"
echo "  │  keytool -genkey -v                                    │"
echo "  │    -keystore swiftreply-release.keystore               │"
echo "  │    -alias swiftreply                                   │"
echo "  │    -keyalg RSA -keysize 2048 -validity 10000           │"
echo "  │                                                        │"
echo "  │  Then set environment variables:                       │"
echo "  │    KEYSTORE_PATH=swiftreply-release.keystore           │"
echo "  │    KEYSTORE_PASSWORD=yourpassword                      │"
echo "  │    KEY_ALIAS=swiftreply                                │"
echo "  │    KEY_PASSWORD=yourpassword                           │"
echo "  └────────────────────────────────────────────────────────┘"
