"""
NexHost V6 - Main Application
ClawCloud Run: Single Container, Port 5000, SQLite
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from config import settings
from database import init_db
from api import router
from ai_router import ai_router as ai_router_instance

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path("/app/frontend/dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting NexHost V6...")
    await init_db()
    logger.info("✅ Database ready")
    yield
    logger.info("🛑 Shutting down...")
    try:
        await ai_router_instance.close_all()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes (prefix /api is added here) ──────────────
app.include_router(router, prefix="/api")

# ── Static: uploads ─────────────────────────────────────
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Static: React assets ─────────────────────────────────
assets_dir = FRONTEND_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# ── Health check (before SPA catch-all) ──────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── SPA: serve index.html for all non-API routes ─────────
@app.get("/")
async def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"name": settings.APP_NAME, "status": "running"})


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Don't catch API routes
    if full_path.startswith("api/") or full_path.startswith("uploads/"):
        return JSONResponse({"error": "Not found"}, status_code=404)

    # Try exact static file first (favicon, manifest, etc.)
    static_file = FRONTEND_DIR / full_path
    if static_file.exists() and static_file.is_file():
        return FileResponse(str(static_file))

    # Fallback: SPA index.html
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))

    return JSONResponse({"error": "Frontend not built"}, status_code=503)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
