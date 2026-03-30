"""Main FastAPI application."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, devices, scenes
from app.services.mijia import mijia_service
from app.config import HOST, PORT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Starting Mijia HTTP API Server...")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="米家 API HTTP 服务",
    description="基于 mijia-api 库的 HTTP API 服务，支持 Docker 部署",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(scenes.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve index page."""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
else:
    # Production mode
    pass
