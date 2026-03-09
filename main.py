import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import create_tables

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

app = FastAPI(
    title="SwiftReply API",
    description="WhatsApp Automation SaaS Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception:
    pass

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    logger.info("Starting SwiftReply API...")
    await create_tables()
    logger.info("Database tables created/verified")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SwiftReply API"}

@app.get("/")
async def root():
    return {"message": "SwiftReply API", "docs": "/docs"}
