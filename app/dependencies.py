"""Dependencies for authentication and authorization."""

from fastapi import Query, HTTPException
from app.config import API_SECRET


def verify_api_secret(secret: str = Query(None)) -> bool:
    """
    Verify the API secret from query parameter.
    
    Returns True if:
    - No API_SECRET is configured (development mode)
    - The provided secret matches the configured secret
    
    Raises HTTPException if secret is required but not provided or incorrect.
    """
    if not API_SECRET:
        return True  # No secret configured, allow all
    
    if not secret:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "API Secret required",
                "hint": f"请在 URL 后添加 ?secret=你的密钥 来访问此 API"
            }
        )
    
    if secret != API_SECRET:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Invalid API Secret",
                "hint": "提供的密钥不正确"
            }
        )
    
    return True
