"""Main FastAPI application."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, devices, scenes
from app.services.mijia import mijia_service
from app.config import HOST, PORT, LOG_LEVEL, API_SECRET

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")


def verify_secret(secret: str = Query(None)) -> bool:
    """Verify the API secret."""
    if not API_SECRET:
        return True  # No secret configured, allow all
    return secret == API_SECRET


def get_auth_error_html() -> str:
    """Return HTML page for unauthorized access."""
    return """<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>访问被拒绝</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: #f8fafc;
            color: #1e293b;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { color: #ef4444; margin-bottom: 16px; }
        p { color: #64748b; margin-bottom: 24px; }
        .hint {
            background: #fef3c7;
            border: 1px solid #f59e0b;
            padding: 16px;
            border-radius: 8px;
            color: #92400e;
        }
        code {
            background: #f1f5f9;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 访问被拒绝</h1>
        <p>请提供有效的 API Secret 才能访问此服务</p>
        <div class="hint">
            <p><strong>方式一：</strong>在 URL 后添加 <code>?secret=你的密钥</code></p>
            <p style="margin-top:12px"><strong>方式二：</strong>设置环境变量 <code>MIJIA_API_SECRET=你的密钥</code> 并重启服务</p>
        </div>
    </div>
</body>
</html>"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Starting Mijia HTTP API Server...")
    if API_SECRET:
        logger.info("API Secret is configured - authentication enabled")
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
async def root(secret: str = Query(None)):
    """Serve index page with optional secret authentication."""
    if not verify_secret(secret):
        return get_auth_error_html()
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
