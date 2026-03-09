# SwiftReply Backend — PyInstaller spec
# Produces a single-folder bundle containing the FastAPI backend
# Output: backend-bundled/swiftreply-backend/ (or .exe on Windows)
#
# Usage:
#   pip install pyinstaller
#   cd backend
#   pyinstaller swiftreply.spec --distpath ../backend-bundled

import sys
import os
from pathlib import Path

block_cipher = None

# Collect all app modules
a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Include .env.example as reference
        ('../.env.example', '.'),
        # Include alembic migrations
        ('alembic/', 'alembic/'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        # FastAPI + Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware.cors',
        # SQLAlchemy async
        'sqlalchemy.ext.asyncio',
        'sqlalchemy.dialects.postgresql',
        'asyncpg',
        # Alembic
        'alembic',
        'alembic.runtime.migration',
        'alembic.operations',
        # App modules
        'app',
        'app.main',
        'app.db',
        'app.db.database',
        'app.db.models',
        'app.middleware',
        'app.middleware.auth',
        'app.routes',
        'app.routes.auth',
        'app.routes.conversations',
        'app.routes.messages',
        'app.routes.contacts',
        'app.routes.analytics',
        'app.routes.templates',
        'app.routes.ai_routes',
        'app.routes.evolution_webhook',
        'app.routes.broadcast',
        'app.routes.users',
        'app.services',
        'app.services.evolution_service',
        'app.services.gemini_service',
        'app.services.websocket_manager',
        # Other
        'google.generativeai',
        'httpx',
        'jose',
        'passlib',
        'passlib.handlers',
        'passlib.handlers.bcrypt',
        'dotenv',
        'multipart',
        'email_validator',
        'aiofiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='swiftreply-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # Show console window (useful for logging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='swiftreply-backend',
)
