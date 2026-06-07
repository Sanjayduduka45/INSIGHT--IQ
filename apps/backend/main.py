"""
InsightIQ — Backend API Server

FastAPI application with CORS, structured logging, and all API routes.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.settings import get_settings
from core.security import get_current_user
from api.datasets import router as datasets_router
from api.analytics import router as analytics_router
from api.anomalies import router as anomalies_router
from api.forecasting import router as forecasting_router
from api.chat import router as chat_router
from api.export import router as export_router
from api.settings import router as settings_router

# ── Configure logging ────────────────────────────────────────────────────
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("insightiq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(
        "🚀 InsightIQ Backend starting — %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    logger.info(
        "  Gemini: %s",
        "✅ configured" if settings.has_gemini else "❌ not configured (using fallback)",
    )
    logger.info(
        "  Supabase: %s",
        "✅ configured" if settings.has_supabase else "❌ not configured (using in-memory)",
    )
    yield
    logger.info("InsightIQ Backend shutting down")


# ── Create FastAPI app ───────────────────────────────────────────────────
app = FastAPI(
    title="InsightIQ API",
    description="Universal AI Data Intelligence Platform",
    version=settings.app_version,
    lifespan=lifespan,
)


# ── Global Exception Handler ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions, log them securely, and return a user-friendly error."""
    error_context = {
        "event": "unhandled_exception",
        "method": request.method,
        "url": str(request.url),
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
    }
    # Log structured data internally (in a real app, this goes to Datadog/ELK)
    logger.error("Unhandled Exception: %s", error_context, exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred while processing your request. Our team has been notified."
        },
    )


# ── Rate Limiting ────────────────────────────────────────────────────────
_request_history = defaultdict(list)
RATE_LIMIT_REQUESTS = 180
RATE_LIMIT_WINDOW_SECONDS = 60


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Only limit API endpoints, ignore docs/health checks
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean history
    history = _request_history[client_ip]
    _request_history[client_ip] = [t for t in history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    
    if len(_request_history[client_ip]) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again in a few moments."}
        )
        
    _request_history[client_ip].append(now)
    return await call_next(request)


# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────────────────────
app.include_router(datasets_router)
app.include_router(analytics_router, dependencies=[Depends(get_current_user)])
app.include_router(anomalies_router, dependencies=[Depends(get_current_user)])
app.include_router(forecasting_router, dependencies=[Depends(get_current_user)])
app.include_router(chat_router, dependencies=[Depends(get_current_user)])
app.include_router(export_router, dependencies=[Depends(get_current_user)])
app.include_router(settings_router)


# ── Health check ─────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy"
    }


@app.get("/version")
async def version_check():
    return {
        "version": settings.app_version
    }


@app.get("/")
async def root():
    return {
        "name": "InsightIQ API",
        "version": settings.app_version,
        "docs": "/docs",
    }
