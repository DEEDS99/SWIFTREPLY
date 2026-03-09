@echo off
REM ═══════════════════════════════════════════════════════════════
REM  SwiftReply — Windows Build Script
REM  Produces: SwiftReply-1.0.0_windows_setup.exe + .msi
REM
REM  Requirements:
REM    - Rust (https://rustup.rs) + target: x86_64-pc-windows-msvc
REM    - Node.js 18+ and npm
REM    - Python 3.11+ and pip
REM    - Visual Studio Build Tools (C++ workload)
REM    - WebView2 Runtime (included in Windows 10/11)
REM ═══════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║   SwiftReply — Windows Builder        ║
echo  ╚═══════════════════════════════════════╝
echo.

set SCRIPT_DIR=%~dp0
set ROOT=%SCRIPT_DIR%..
set FRONTEND=%ROOT%\frontend
set BACKEND=%ROOT%\backend
set OUTPUT=%ROOT%\dist\windows

cd /d "%ROOT%"

REM ── Step 1: Bundle Python backend ──────────────────────────────
echo [1/4] Bundling Python backend with PyInstaller...
cd /d "%BACKEND%"
pip install pyinstaller --quiet
pip install -r requirements.txt --quiet
pyinstaller swiftreply.spec --distpath "%ROOT%\backend-bundled" --clean -y
if errorlevel 1 ( echo ERROR: PyInstaller failed & exit /b 1 )
echo       Backend bundled OK

REM ── Step 2: Install frontend deps ──────────────────────────────
echo [2/4] Installing frontend dependencies...
cd /d "%FRONTEND%"
call npm install --silent
if errorlevel 1 ( echo ERROR: npm install failed & exit /b 1 )

REM ── Step 3: Copy backend into Tauri resources ──────────────────
echo [3/4] Copying backend bundle into Tauri resources...
if not exist "%FRONTEND%\src-tauri\resources\backend" mkdir "%FRONTEND%\src-tauri\resources\backend"
xcopy /E /I /Y "%ROOT%\backend-bundled\swiftreply-backend" "%FRONTEND%\src-tauri\resources\backend"

REM Update tauri.conf.json to include backend as resource
REM (resources array already configured in tauri.conf.json)

REM ── Step 4: Build Tauri Windows app ────────────────────────────
echo [4/4] Building Tauri Windows installer...
cd /d "%FRONTEND%"
call npm run tauri:build:windows
if errorlevel 1 ( echo ERROR: Tauri build failed & exit /b 1 )

REM ── Collect outputs ────────────────────────────────────────────
if not exist "%OUTPUT%" mkdir "%OUTPUT%"
copy "%FRONTEND%\src-tauri\target\x86_64-pc-windows-msvc\release\bundle\nsis\*.exe" "%OUTPUT%\" 2>nul
copy "%FRONTEND%\src-tauri\target\x86_64-pc-windows-msvc\release\bundle\msi\*.msi" "%OUTPUT%\" 2>nul

echo.
echo  ✅ Windows build complete!
echo  📦 Output: %OUTPUT%
echo.
dir "%OUTPUT%"
echo.
pause
