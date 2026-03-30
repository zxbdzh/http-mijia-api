"""Auth router - Simplified single instance mode."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse

from app.services.mijia import mijia_service
from app.dependencies import verify_api_secret

logger = logging.getLogger("auth")

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.get("/status")
async def get_auth_status(_: bool = Depends(verify_api_secret)):
    """Get current authentication status."""
    return mijia_service.get_auth_status()


@router.post("/login")
async def start_login(_: bool = Depends(verify_api_secret)):
    """Start QR code login - returns QR code immediately."""
    return await mijia_service.start_login()


@router.get("/login/status")
async def get_login_status(_: bool = Depends(verify_api_secret)):
    """Get current login status."""
    return mijia_service.get_login_status()


@router.post("/login/cancel")
async def cancel_login(_: bool = Depends(verify_api_secret)):
    """Cancel ongoing login."""
    mijia_service.cancel_login()
    return {"success": True, "message": "Login cancelled"}


@router.post("/logout")
async def logout(_: bool = Depends(verify_api_secret)):
    """Logout."""
    return mijia_service.logout()


@router.websocket("/ws/login")
async def websocket_login(websocket: WebSocket):
    """WebSocket for real-time login status."""
    await websocket.accept()
    try:
        while True:
            status = mijia_service.get_login_status()
            await websocket.send_json(status)
            
            if status["status"] in ["success", "error"]:
                break
            
            import asyncio
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
