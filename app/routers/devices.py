"""Devices router - Simplified single instance mode."""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.services.mijia import mijia_service

logger = logging.getLogger("devices")

router = APIRouter(prefix="/api/v1/devices", tags=["设备"])


def handle_error(e: Exception):
    """Handle service errors."""
    error_msg = str(e)
    if "Not authenticated" in error_msg:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    raise HTTPException(status_code=400, detail=error_msg)


# ============ Homes ============

@router.get("/homes")
async def get_homes():
    """获取所有家庭."""
    try:
        return mijia_service.get_homes()
    except Exception as e:
        handle_error(e)


# ============ Devices ============

@router.get("/")
async def get_devices(home_id: str = Query(None, description="家庭ID")):
    """获取所有设备或指定家庭的设备."""
    try:
        return mijia_service.get_devices(home_id)
    except Exception as e:
        handle_error(e)


@router.get("/shared")
async def get_shared_devices():
    """获取共享设备."""
    try:
        return mijia_service.get_shared_devices()
    except Exception as e:
        handle_error(e)


@router.get("/{did}")
async def get_device(did: str):
    """获取指定设备."""
    try:
        return mijia_service.get_device(did)
    except Exception as e:
        handle_error(e)


@router.get("/{did}/info")
async def get_device_info_by_did(did: str):
    """获取设备型号信息（通过did）."""
    try:
        return mijia_service.get_device_info_by_did(did)
    except Exception as e:
        handle_error(e)


@router.get("/info/{model}")
async def get_device_info_by_model(model: str):
    """获取设备信息."""
    try:
        return mijia_service.get_device_info(model)
    except Exception as e:
        handle_error(e)


# ============ Properties ============

@router.get("/{did}/properties")
async def get_device_properties(did: str):
    """获取设备所有属性."""
    try:
        return mijia_service.get_device_properties(did)
    except Exception as e:
        handle_error(e)


@router.get("/{did}/properties/{prop_name}")
async def get_device_property(did: str, prop_name: str):
    """获取设备单个属性."""
    try:
        return mijia_service.get_device_property(did, prop_name)
    except Exception as e:
        handle_error(e)


@router.put("/{did}/properties/{prop_name}")
async def set_device_property(did: str, prop_name: str, value: float | bool | str):
    """设置设备属性."""
    try:
        return mijia_service.set_device_property(did, prop_name, value)
    except Exception as e:
        handle_error(e)


# ============ Actions ============

@router.post("/{did}/actions/{action_name}")
async def execute_action(did: str, action_name: str, **params):
    """执行设备动作."""
    try:
        return mijia_service.execute_action(did, action_name, **params)
    except Exception as e:
        handle_error(e)


# ============ Consumables ============

@router.get("/{did}/consumables")
async def get_consumables(did: str, home_id: str = Query(None)):
    """获取设备耗材信息."""
    try:
        return mijia_service.get_consumables(home_id)
    except Exception as e:
        handle_error(e)
