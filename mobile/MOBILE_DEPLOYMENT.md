# SwiftReply — Mobile Deployment Guide (iOS + Android)

SwiftReply uses **Capacitor** to wrap the React web app as a native iOS and Android app.
The same codebase runs on web, iOS, Android, macOS, and Windows.

---

## Prerequisites

| Platform | Required |
|---|---|
| iOS | macOS + Xcode 15+ + Apple Developer Account ($99/yr) |
| Android | Android Studio + JDK 17 |
| Both | Node.js 18+, npm |

---

## Quick Build

```bash
cd frontend

# 1. Build the web app
npm run build

# 2. Sync to native projects
npx cap sync

# 3. Open in Xcode (iOS)
npx cap open ios

# 4. Open in Android Studio (Android)
npx cap open android
```

---

## First Time Setup

```bash
cd frontend
npm install

# Add platforms (first time only)
npx cap add ios
npx cap add android
npx cap sync
```

---

## iOS — App Store Distribution

1. Open Xcode: `npx cap open ios`
2. Select your team in Signing & Capabilities
3. Set Bundle ID: `com.yourcompany.swiftreply`
4. Product → Archive
5. Distribute App → App Store Connect
6. Submit for review

**Push Notifications (optional):**
```bash
npm install @capacitor/push-notifications
npx cap sync ios
```
Enable Push Notifications capability in Xcode.

---

## Android — Play Store Distribution

1. Open Android Studio: `npx cap open android`
2. Edit `android/app/build.gradle`:
   ```gradle
   applicationId "com.yourcompany.swiftreply"
   versionCode 1
   versionName "1.0"
   ```
3. Build → Generate Signed Bundle/APK
4. Upload to Google Play Console

---

## Desktop (macOS + Windows + Linux)

### Option A — Capacitor macOS (Electron-style)
```bash
npm install @capacitor-community/electron
npx cap add @capacitor-community/electron
npx cap open @capacitor-community/electron
```

### Option B — Tauri (lighter weight, Rust-based)
```bash
npm install --save-dev @tauri-apps/cli
npx tauri init
npx tauri build
# Produces: .app (macOS), .exe (Windows), .deb/.AppImage (Linux)
```

### Option C — PWA (Progressive Web App — works on all devices)
The app already works as a PWA. Users can install it from the browser:
- Chrome: Address bar → Install icon
- Safari iOS: Share → Add to Home Screen

---

## Environment Config for Mobile

In `capacitor.config.ts`, set the server URL for production:

```typescript
const config: CapacitorConfig = {
  appId: 'com.yourcompany.swiftreply',
  appName: 'SwiftReply',
  webDir: 'dist',
  server: {
    url: 'https://swiftreply-frontend.onrender.com',  // Production
    cleartext: false,
  },
}
```

For local dev, remove the `server.url` to use the bundled web files.

---

## Updating the App

```bash
npm run build
npx cap sync    # Copies dist/ to native iOS/Android projects
# Then rebuild in Xcode/Android Studio
```

---

## App Icons & Splash Screens

```bash
npm install @capacitor/assets --save-dev

# Add your icon (1024x1024 PNG) and splash (2732x2732 PNG) to assets/
npx @capacitor/assets generate
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| CORS errors on mobile | Ensure `capacitor://localhost` is in backend CORS origins |
| API calls fail | Set `VITE_API_URL` to your full production URL, not `/api` |
| WS not connecting | Use `wss://` (not `ws://`) in production |
| iOS build fails | Run `pod install` in `ios/App` directory |
| Android Gradle error | Update `compileSdkVersion` to 34 in `build.gradle` |
