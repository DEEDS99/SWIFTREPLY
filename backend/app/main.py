"""
SwiftReply — Main FastAPI Application Engine
============================================
AI-powered WhatsApp Business messaging platform.
Handles text, image, audio, and video via Google Gemini.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.db.database import engine, Base
from app.routes import auth, conversations, messages, contacts, analytics, templates, ai_routes, evolution_webhook, broadcast, users
from app.services.websocket_manager import router as ws_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "true").lower() == "true" else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("swiftreply")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 SwiftReply starting up...")
    # Create tables (Alembic handles migrations in production)
    async with engine.begin() as conn:
        pass  # Tables managed by Alembic
    logger.info("✅ Database connected")
    logger.info("✅ SwiftReply is ready")
    yield
    logger.info("🛑 SwiftReply shutting down...")


app = FastAPI(
    title="SwiftReply API",
    description="AI-Powered WhatsApp Business Messaging Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- CORS ---
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:3000",
    "http://localhost:5173",
    "capacitor://localhost",   # Capacitor mobile
    "ionic://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static files for media uploads ---
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- API Routes ---
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(evolution_webhook.router, prefix="/api", tags=["Evolution"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(ai_routes.router, prefix="/api/ai", tags=["AI"])
app.include_router(broadcast.router, prefix="/api/broadcasts", tags=["Broadcast"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(ws_router, tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": "SwiftReply", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
