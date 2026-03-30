"""Scenes router - Simplified single instance mode."""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.mijia import mijia_service
from app.dependencies import verify_api_secret

logger = logging.getLogger("scenes")

router = APIRouter(prefix="/api/v1", tags=["场景"])


def handle_error(e: Exception):
    """Handle service errors."""
    error_msg = str(e)
    if "Not authenticated" in error_msg:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    raise HTTPException(status_code=400, detail=error_msg)


# ============ Scenes ============

@router.get("/scenes")
async def get_scenes(home_id: str = Query(None, description="家庭ID"), _: bool = Depends(verify_api_secret)):
    """获取所有场景或指定家庭的场景."""
    try:
        return mijia_service.get_scenes(home_id)
    except Exception as e:
        handle_error(e)


@router.post("/scenes/{scene_id}")
async def run_scene(scene_id: str, home_id: str = Query(None, description="家庭ID"), _: bool = Depends(verify_api_secret)):
    """执行场景."""
    try:
        # 如果没有提供 home_id，尝试从场景列表中获取
        if home_id is None:
            scenes = mijia_service.get_scenes()
            for scene in scenes:
                if scene.get("id") == scene_id or scene.get("scene_id") == scene_id:
                    home_id = scene.get("home_id")
                    break
        
        # 如果还是没有 home_id，尝试获取第一个家庭
        if home_id is None:
            homes = mijia_service.get_homes()
            if homes:
                home_id = homes[0].get("home_id")
        
        return mijia_service.run_scene(scene_id, home_id)
    except Exception as e:
        handle_error(e)
