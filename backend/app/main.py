"""XAF Converter API -- FastAPI application with session management and security."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import export, session, upload, websocket
from .services.session_manager import session_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup: initialize session manager, purge old dirs, start cleanup loop
    logger.info("Starting XAF Converter API...")
    session_manager.initialize()
    await session_manager.start_cleanup_loop()
    logger.info("Session manager initialized, cleanup loop started.")
    yield
    # Shutdown: stop cleanup loop
    logger.info("Shutting down XAF Converter API...")
    await session_manager.stop_cleanup_loop()
    logger.info("Cleanup loop stopped.")


app = FastAPI(
    title="XAF Converter",
    version="1.0.0",
    description="Convert Dutch XAF audit files to CSV, XLSX, JSON, and Parquet.",
    lifespan=lifespan,
)

# R-CORS-1: Strict CORS -- same origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # No cross-origin requests
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Register routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/api/health")
async def health() -> dict:
    """Health-check endpoint."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "active_sessions": session_manager.active_sessions,
    }
