# SwiftReply — Platform Build Guide
## Windows .exe · macOS .dmg · Android .apk

---

## What You Get

| Platform | Output File | Size | How to Install |
|---|---|---|---|
| 🪟 Windows | `SwiftReply-1.0.0_x64-setup.exe` | ~40MB | Double-click installer |
| 🪟 Windows | `SwiftReply-1.0.0_x64.msi` | ~35MB | Windows Installer package |
| 🍎 macOS | `SwiftReply_1.0.0_universal.dmg` | ~50MB | Open → drag to /Applications |
| 🤖 Android | `SwiftReply-1.0.0-debug.apk` | ~25MB | Sideload (testing/internal) |
| 🤖 Android | `SwiftReply-1.0.0-release.aab` | ~22MB | Upload to Google Play Store |

---

## Method A — Automated (GitHub Actions, Recommended)

Every time you push a version tag, GitHub automatically builds all platforms:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions runs `.github/workflows/build-all-platforms.yml` and:
1. Builds Windows `.exe` + `.msi` on `windows-latest`
2. Builds macOS universal `.dmg` on `macos-latest`
3. Builds Android `.apk` + `.aab` on `ubuntu-latest`
4. Creates a GitHub Release with all files attached

**No machine setup required** — GitHub provides the build environment.

---

## Method B — Build Locally

### Prerequisites by Platform

#### Windows Build (run on Windows machine)
```powershell
# 1. Install Rust
winget install Rustlang.Rustup
rustup target add x86_64-pc-windows-msvc

# 2. Install Visual Studio Build Tools (free)
winget install Microsoft.VisualStudio.2022.BuildTools
# Select: "Desktop development with C++"

# 3. Install Node.js
winget install OpenJS.NodeJS.LTS

# 4. Install Python 3.11
winget install Python.Python.3.11
```

```powershell
# Build
cd scripts
.\build-windows.bat
# Output: dist\windows\SwiftReply-1.0.0_x64-setup.exe
```

#### macOS Build (run on Mac)
```bash
# 1. Install Xcode Command Line Tools
xcode-select --install

# 2. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup target add x86_64-apple-darwin aarch64-apple-darwin

# 3. Install Node.js (if not installed)
brew install node
```

```bash
# Build
cd scripts
./build-macos.sh
# Output: dist/macos/SwiftReply_1.0.0_universal.dmg
```

#### Android Build (run on any OS)
```bash
# 1. Install Java 17
brew install openjdk@17          # macOS
sudo apt install openjdk-17-jdk  # Ubuntu/Debian

# 2. Install Android Studio (includes SDK + Gradle)
#    Download from: https://developer.android.com/studio
#    OR install SDK command line tools only

# 3. Set ANDROID_HOME
export ANDROID_HOME=$HOME/Library/Android/sdk  # macOS
export ANDROID_HOME=$HOME/Android/Sdk          # Linux

# 4. Add to PATH
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

```bash
# Build
cd scripts
./build-android.sh
# Output: dist/android/SwiftReply-1.0.0-debug.apk
#         dist/android/SwiftReply-1.0.0-release.aab
```

---

## Understanding the Stack

### Desktop (Windows + macOS): Tauri
**Why Tauri over Electron:**
- 10x smaller bundle (~5MB vs ~150MB)
- Uses OS WebView (Edge on Windows, WebKit on macOS) — no bundled Chromium
- Rust backend — fast, memory-safe
- System tray support built-in
- Auto-updates built-in

**What Tauri does:**
```
Your React App (web UI)
        ↓
Tauri Shell (Rust)
  ├── Creates native window using OS WebView
  ├── System tray (minimize to tray instead of closing)
  ├── Launches bundled Python FastAPI backend on startup
  ├── Handles OS notifications
  └── Packages everything as .exe or .dmg
```

### Mobile (Android + iOS): Capacitor
**Why Capacitor over React Native:**
- Uses the same React codebase with zero changes
- Full WebView — same rendering as browser
- Access to native APIs (camera, push notifications, contacts)
- Simpler than React Native, no bridge compilation

**What Capacitor does:**
```
Your React App (web UI)
        ↓
Capacitor Shell
  ├── Wraps in Android WebView (Chromium-based)
  ├── Bridges JS ↔ native (camera, notifications, etc.)
  └── Packages as .apk / .aab / .ipa
```

### Backend: PyInstaller
Bundles the entire Python FastAPI backend into a standalone executable:
```
Python 3.11 + FastAPI + dependencies
        ↓
PyInstaller
        ↓
swiftreply-backend.exe (Windows)
swiftreply-backend     (macOS/Linux)
```
No Python installation needed on end-user machine.

---

## Tauri Resources (Backend Bundling)

The Tauri app bundles the Python backend as a "resource":

```
SwiftReply.exe
  └── resources/
      └── backend/
          └── swiftreply-backend.exe   ← PyInstaller output
```

On launch, `src-tauri/src/main.rs` spawns the backend process:
```rust
Command::new("resources/backend/swiftreply-backend.exe")
  .env("PORT", "8000")
  .spawn()
```

The React UI then connects to `http://localhost:8000` as usual.

---

## Code Signing (Required for Distribution)

### Windows — Authenticode Signing
Without signing, Windows Defender SmartScreen shows a warning.

```powershell
# Option A: Buy a code signing certificate (~$200-500/yr)
# Digicert, Sectigo, GlobalSign all work

# Option B: Self-signed (for internal distribution)
New-SelfSignedCertificate `
  -DnsName "swiftreply.com" `
  -Type CodeSigning `
  -CertStoreLocation Cert:\CurrentUser\My

# Apply in tauri.conf.json:
# "windows": { "certificateThumbprint": "YOUR_THUMBPRINT" }
```

### macOS — Apple Developer ID
Without signing + notarization, Gatekeeper blocks the app.

```bash
# Requires Apple Developer Account ($99/yr)
# 1. Create "Developer ID Application" certificate in Xcode
# 2. Set in tauri.conf.json:
#    "macOS": { "signingIdentity": "Developer ID Application: Your Name (TEAMID)" }

# 3. Notarize after building:
xcrun notarytool submit SwiftReply.dmg \
  --apple-id "your@email.com" \
  --password "@keychain:AC_PASSWORD" \
  --team-id "YOUR_TEAM_ID" \
  --wait
xcrun stapler staple SwiftReply.dmg
```

### Android — Keystore
```bash
# Generate production keystore (one time — keep this file safe!)
keytool -genkey -v \
  -keystore swiftreply-release.keystore \
  -alias swiftreply \
  -keyalg RSA -keysize 2048 \
  -validity 10000

# Set as GitHub Secrets for CI:
# ANDROID_KEYSTORE_BASE64 = base64 -i swiftreply-release.keystore
# ANDROID_KEYSTORE_PASSWORD = your-password
# ANDROID_KEY_ALIAS = swiftreply
# ANDROID_KEY_PASSWORD = your-password
```

---

## GitHub Secrets Setup

Go to your repo → Settings → Secrets → Actions → New secret:

| Secret | Description |
|---|---|
| `TAURI_PRIVATE_KEY` | Tauri updater private key (optional, for auto-updates) |
| `TAURI_KEY_PASSWORD` | Tauri private key password |
| `ANDROID_KEYSTORE_BASE64` | `base64 -i release.keystore` output |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias (e.g. `swiftreply`) |
| `ANDROID_KEY_PASSWORD` | Key password |

---

## App Store / Play Store Submission

### Google Play Store
1. Create account at [play.google.com/console](https://play.google.com/console) ($25 one-time fee)
2. Create new app → "SwiftReply"
3. Fill in store listing (description, screenshots, icon)
4. Upload `SwiftReply-release.aab` to "Internal testing" first
5. Test, then promote to "Production"

### Apple App Store
1. Enroll in Apple Developer Program ($99/yr)
2. Create app in App Store Connect
3. Build with Xcode: `npx cap open ios` → Product → Archive
4. Upload via Xcode Organizer or `xcrun altool`
5. Submit for review (~1-2 days)

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Tauri build fails: "cargo not found" | Run `rustup update` and ensure `~/.cargo/bin` is in PATH |
| Windows: "LINK: error" | Install Visual Studio Build Tools with C++ workload |
| macOS: "Developer cannot be verified" | Right-click → Open (first time only) or sign the app |
| Android: "SDK not found" | Set `ANDROID_HOME` env variable correctly |
| Android: Gradle OOM | Add `org.gradle.jvmargs=-Xmx4g` to `android/gradle.properties` |
| APK installs but shows blank screen | Check `VITE_API_URL` points to your production backend |
| Backend not starting in desktop app | Check app logs: Windows Event Viewer, macOS Console.app |
