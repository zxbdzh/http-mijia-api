"""Mijia API service - Single instance mode."""

import os
import json
import time
import logging
import asyncio
import base64
import io
from typing import Optional, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock

import httpx
from qrcode import QRCode
from mijiaAPI import mijiaAPI, mijiaDevice, DeviceNotFoundError, DeviceGetError, DeviceSetError, DeviceActionError

from app.config import AUTH_FILE, DATA_DIR

logger = logging.getLogger("mijia")


@dataclass
class LoginState:
    """Login state for async notification."""
    status: str = "idle"  # idle, waiting, success, error
    message: str = ""
    qr_image: Optional[str] = None
    qr_link: Optional[str] = None
    lp_url: Optional[str] = None
    user_id: Optional[str] = None
    error: Optional[str] = None


class MijiaService:
    """Mijia API service - Single instance, non-blocking login."""
    
    _instance: Optional["MijiaService"] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Auth file path
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        
        # Initialize Mijia API
        self.api = mijiaAPI(AUTH_FILE)
        self.is_authenticated = False
        self.user_id: Optional[str] = None
        
        # Login state for WebSocket notification
        self._login_state = LoginState()
        
        # Device cache
        self._device_cache: dict[str, mijiaDevice] = {}
        
        # Check existing authentication
        self._check_auth()
        self._initialized = True
        logger.info("MijiaService initialized")
    
    def _check_auth(self):
        """Check if already authenticated."""
        try:
            self.api.get_homes_list()
            self.is_authenticated = True
            self.user_id = self.api.auth_data.get("userId")
            logger.info(f"Already authenticated as {self.user_id}")
        except Exception as e:
            logger.info(f"Not authenticated: {e}")
            self.is_authenticated = False
    
    def get_auth_status(self) -> dict:
        """Get current authentication status."""
        if self.is_authenticated:
            return {
                "authenticated": True,
                "user_id": self.user_id,
                "message": "Already logged in"
            }
        return {
            "authenticated": False,
            "message": "Not logged in"
        }
    
    def _generate_qr_code(self, url: str) -> str:
        """Generate QR code as base64 PNG."""
        qr = QRCode(border=1, box_size=10)
        qr.add_data(url)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    
    def _parse_cookies_from_response(self, response: httpx.Response) -> dict:
        """从响应头中手动解析 Set-Cookie，避免 client.cookies 累积问题。"""
        cookies = {}
        for set_cookie in response.headers.get_list("set-cookie"):
            for cookie_str in set_cookie.split(";"):
                cookie_str = cookie_str.strip()
                if "=" in cookie_str:
                    name, value = cookie_str.split("=", 1)
                    cookies[name.strip()] = value.strip()
        return cookies
    
    async def start_login(self) -> dict:
        """Start QR code login - non-blocking."""
        if self.is_authenticated:
            return {
                "status": "success",
                "message": "Already authenticated",
                "user_id": self.user_id
            }
        
        try:
            # Get login URL
            from urllib import parse
            
            headers = {
                "User-Agent": self.api.user_agent,
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"deviceId={self.api.deviceId};"
                          f"pass_o={self.api.pass_o};"
                          f"passToken={self.api.auth_data.get('passToken', '')};"
                          f"userId={self.api.auth_data.get('userId', '')};"
                          f"cUserId={self.api.auth_data.get('cUserId', '')};"
                          f"uLocale={self.api.locale};"
            }
            
            async with httpx.AsyncClient() as client:
                service_ret = await client.get(self.api.service_login_url, headers=headers, timeout=10.0)
                service_text = service_ret.text.replace("&&&START&&&", "")
                service_data = json.loads(service_text)
                location = service_data.get("location", "")
                
                # Check token refresh
                if service_data.get('code') == 0:
                    ret = await client.get(location, timeout=10.0)
                    if ret.status_code == 200 and ret.text == "ok":
                        # 手动解析 cookies，避免 client.cookies 累积
                        cookies = self._parse_cookies_from_response(ret)
                        self.api.auth_data.update(cookies)
                        self.api.auth_data["ssecurity"] = service_data["ssecurity"]
                        self.api._save_auth_data()
                        self.api._init_session()
                        self.is_authenticated = True
                        self.user_id = self.api.auth_data.get("userId")
                        self._login_state = LoginState(
                            status="success",
                            message="Login successful",
                            user_id=self.user_id
                        )
                        return {
                            "status": "success",
                            "message": "Login successful",
                            "user_id": self.user_id
                        }
                
                # Build login URL for QR code
                location_data = dict(parse.parse_qsl(parse.urlparse(location).query))
                location_data.update({
                    "theme": "",
                    "bizDeviceType": "",
                    "_hasLogo": "false",
                    "_qrsize": "240",
                    "_dc": str(int(time.time() * 1000)),
                })
                
                url = self.api.login_url + "?" + parse.urlencode(location_data)
                headers["Accept-Encoding"] = "gzip"
                
                login_ret = await client.get(url, headers=headers, timeout=10.0)
                login_text = login_ret.text.replace("&&&START&&&", "")
                login_data = json.loads(login_text)
            
            login_url = login_data.get("loginUrl")
            qr_link = login_data.get("qr")
            
            if not login_url:
                self._login_state = LoginState(
                    status="error",
                    error="Failed to get login URL"
                )
                return {
                    "status": "error",
                    "error": "Failed to get login URL"
                }
            
            # Generate QR code
            qr_image = self._generate_qr_code(login_url)
            
            self._login_state = LoginState(
                status="waiting",
                message="Please scan QR code with Mi Home app",
                qr_image=qr_image,
                qr_link=qr_link or login_url,
                lp_url=login_data.get("lp")
            )
            
            # Start background polling
            asyncio.create_task(self._do_qrlogin())
            
            return {
                "status": "waiting",
                "message": "Please scan QR code",
                "qr_image": qr_image
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            self._login_state = LoginState(
                status="error",
                error=str(e)
            )
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _do_qrlogin(self):
        """Run QR login polling asynchronously."""
        try:
            if not self._login_state.lp_url:
                self._login_state = LoginState(
                    status="error",
                    error="No login polling URL"
                )
                return
            
            headers = {
                "User-Agent": self.api.user_agent,
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "Connection": "keep-alive",
            }
            
            max_attempts = 60
            poll_interval = 2
            
            async with httpx.AsyncClient() as client:
                for attempt in range(max_attempts):
                    if self._login_state.status in ["success", "error"]:
                        return
                    
                    try:
                        lp_ret = await client.get(self._login_state.lp_url, headers=headers, timeout=5.0)
                        lp_text = lp_ret.text.replace("&&&START&&&", "")
                        
                        if not lp_text.strip():
                            await asyncio.sleep(poll_interval)
                            continue
                        
                        lp_data = json.loads(lp_text)
                        
                        # 调试：打印 lp_data 的所有 key
                        logger.info(f"lp_data keys: {list(lp_data.keys())}")
                        
                        if lp_data.get("userId"):
                            # 更新 auth_data 中的关键字段
                            auth_keys = ["psecurity", "nonce", "ssecurity", "passToken", "userId", "cUserId"]
                            for key in auth_keys:
                                self.api.auth_data[key] = lp_data[key]
                            
                            callback_url = lp_data.get("location", "")
                            cb_cookies = {}
                            if callback_url:
                                cb_ret = await client.get(callback_url, headers=headers, timeout=5.0)
                                # 从 callback 响应中获取 cookies（包含 serviceToken）
                                cb_cookies = self._parse_cookies_from_response(cb_ret)
                            
                            # 手动解析 lp 响应的 cookies
                            cookies = self._parse_cookies_from_response(lp_ret)
                            cookies.update(cb_cookies)
                            self.api.auth_data.update(cookies)
                            
                            # 更新过期时间
                            self.api.auth_data.update({
                                "expireTime": int((datetime.now() + timedelta(days=30)).timestamp() * 1000),
                            })
                            
                            # 打印所有 cookies 以便调试
                            logger.info(f"Parsed cookies: {list(cookies.keys())}")
                            logger.info(f"serviceToken in cookies: {'serviceToken' in cookies}")
                            
                            # 确保 serviceToken 存在
                            if "serviceToken" not in self.api.auth_data:
                                logger.warning("serviceToken not found in cookies")
                                # serviceToken 为可选的，继续尝试
                            
                            logger.debug(f"Auth data keys: {list(self.api.auth_data.keys())}")
                            logger.debug(f"serviceToken present: {'serviceToken' in self.api.auth_data}")
                            
                            self.api._save_auth_data()
                            self.api._init_session()
                            
                            self.is_authenticated = True
                            self.user_id = self.api.auth_data.get("userId")
                            self._login_state = LoginState(
                                status="success",
                                message="Login successful",
                                user_id=self.user_id
                            )
                            logger.info(f"Login successful: {self.user_id}")
                            return
                        
                        await asyncio.sleep(poll_interval)
                        
                    except httpx.TimeoutException:
                        await asyncio.sleep(poll_interval)
                        continue
            
            self._login_state = LoginState(
                status="error",
                error="Login timeout"
            )
            
        except Exception as e:
            logger.error(f"QR login error: {e}")
            self._login_state = LoginState(
                status="error",
                error=str(e)
            )
    
    def get_login_status(self) -> dict:
        """Get current login status for WebSocket."""
        return {
            "status": self._login_state.status,
            "message": self._login_state.message,
            "qr_image": self._login_state.qr_image,
            "user_id": self._login_state.user_id,
            "error": self._login_state.error
        }
    
    def cancel_login(self):
        """Cancel ongoing login."""
        if self._login_state.status == "waiting":
            self._login_state = LoginState()
            logger.info("Login cancelled")
    
    def logout(self) -> dict:
        """Logout."""
        # Clear auth file
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE)
        
        # Reinitialize API
        self.api = mijiaAPI(AUTH_FILE)
        self.is_authenticated = False
        self.user_id = None
        self._login_state = LoginState()
        self._device_cache.clear()
        
        logger.info("Logged out")
        return {"success": True, "message": "Logged out"}
    
    # ============ Device Operations ============
    
    def _require_auth(self):
        """Require authenticated session."""
        if not self.is_authenticated:
            raise ValueError("Not authenticated")
    
    def _get_device_wrapper(self, did: str) -> mijiaDevice:
        """Get or create device wrapper."""
        if did in self._device_cache:
            return self._device_cache[did]
        
        device = mijiaDevice(self.api, did=did)
        self._device_cache[did] = device
        return device
    
    # Homes
    def get_homes(self) -> list:
        """Get all homes."""
        self._require_auth()
        return self.api.get_homes_list()
    
    # Devices
    def get_devices(self, home_id: Optional[str] = None, include_shared: bool = True) -> list:
        """Get all devices or filtered by home. Merges and deduplicates devices."""
        self._require_auth()
        
        # Get regular devices
        devices = self.api.get_devices_list()
        
        # Optionally include shared devices
        if include_shared:
            shared = self.api.get_shared_devices_list()
            devices.extend(shared)
        
        # Deduplicate by did
        seen = set()
        unique_devices = []
        for d in devices:
            did = d.get("did")
            if did and did not in seen:
                seen.add(did)
                unique_devices.append(d)
        
        # Filter by home_id if specified
        if home_id:
            unique_devices = [d for d in unique_devices if d.get("home_id") == home_id]
        
        return unique_devices
    
    def get_shared_devices(self) -> list:
        """Get shared devices."""
        self._require_auth()
        return self.api.get_shared_devices_list()
    
    def get_device(self, did: str) -> dict:
        """Get device by DID."""
        self._require_auth()
        devices = self.api.get_devices_list()
        for device in devices:
            if device.get("did") == did:
                return device
        raise ValueError(f"Device {did} not found")
    
    def get_device_info(self, model: str) -> dict:
        """Get device specification info by model."""
        from mijiaAPI import get_device_info
        return get_device_info(model)
    
    def get_device_info_by_did(self, did: str) -> dict:
        """Get device specification info by DID."""
        self._require_auth()
        # First get the device to find its model
        device = self.get_device(did)
        model = device.get("model")
        if not model:
            raise ValueError(f"Device {did} has no model")
        return self.get_device_info(model)
    
    def get_device_properties(self, did: str, timeout: float = 5.0) -> list:
        """Get all properties of a device with timeout limit per property."""
        self._require_auth()
        try:
            device_wrapper = self._get_device_wrapper(did)
            props = []
            prop_list = list(device_wrapper.prop_list.items())
            
            for prop_name, prop_obj in prop_list:
                try:
                    value = device_wrapper.get(prop_name, timeout=timeout)
                    props.append({
                        "name": prop_name,
                        "value": value,
                        "desc": getattr(prop_obj, 'desc', ''),
                        "type": str(getattr(prop_obj, 'type', 'unknown')),
                        "unit": getattr(prop_obj, 'unit', '')
                    })
                except Exception as e:
                    # 静默失败，避免一个属性超时阻塞整个列表
                    props.append({
                        "name": prop_name,
                        "value": None,
                        "desc": getattr(prop_obj, 'desc', ''),
                        "type": str(getattr(prop_obj, 'type', 'unknown')),
                        "unit": getattr(prop_obj, 'unit', ''),
                        "error": str(e)
                    })
            return props
        except DeviceNotFoundError:
            raise ValueError(f"Device {did} not found")
        except Exception as e:
            raise ValueError(f"Failed to get properties: {e}")
    
    def get_device_property(self, did: str, prop_name: str) -> Any:
        """Get single property."""
        self._require_auth()
        try:
            device_wrapper = self._get_device_wrapper(did)
            return device_wrapper.get(prop_name)
        except DeviceGetError as e:
            raise ValueError(f"Failed to get property '{prop_name}': {e}")
    
    def set_device_property(self, did: str, prop_name: str, value: Any) -> dict:
        """Set device property."""
        self._require_auth()
        try:
            device_wrapper = self._get_device_wrapper(did)
            device_wrapper.set(prop_name, value)
            return {"success": True, "message": f"Property '{prop_name}' set to {value}"}
        except DeviceSetError as e:
            return {"success": False, "error": f"Failed to set property: {e}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    def execute_action(self, did: str, action_name: str, **params) -> dict:
        """Execute device action."""
        self._require_auth()
        try:
            device_wrapper = self._get_device_wrapper(did)
            result = device_wrapper.run_action(action_name, **params)
            return {"success": True, "result": result}
        except DeviceActionError as e:
            return {"success": False, "error": f"Failed to execute action: {e}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    # Scenes
    def get_scenes(self, home_id: Optional[str] = None) -> list:
        """Get all scenes or filtered by home."""
        self._require_auth()
        try:
            scenes = self.api.get_scenes_list()
            if home_id:
                scenes = [s for s in scenes if s.get("home_id") == home_id]
            return scenes
        except Exception as e:
            raise ValueError(f"Failed to get scenes: {e}")
    
    def run_scene(self, scene_id: str, home_id: Optional[str] = None) -> dict:
        """Run a scene."""
        self._require_auth()
        try:
            self.api.run_scene(scene_id=scene_id, home_id=home_id)
            return {"success": True, "message": "Scene executed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Consumables
    def get_consumables(self, home_id: Optional[str] = None) -> list:
        """Get consumables."""
        self._require_auth()
        try:
            return self.api.get_consumable_items(home_id=home_id)
        except Exception as e:
            raise ValueError(f"Failed to get consumables: {e}")


# Global service instance
mijia_service = MijiaService()
