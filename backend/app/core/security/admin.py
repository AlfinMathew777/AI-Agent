import os
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from app.api.deps import get_current_user
from app.schemas.auth import TokenData

# Keep fallback for local dev if environment allows
api_key_header = APIKeyHeader(name="x-admin-key", auto_error=False)

async def verify_admin(
    user: TokenData = Depends(get_current_user), 
    api_key: str = Security(api_key_header)
):
    # 1. Priority: Checked valid JWT User
    if user:
        if user.role in ["admin", "owner"]:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

    # 2. Fallback: Check Dev Key (if allowed)
    ALLOW_DEV = os.getenv("ALLOW_DEV_ADMIN_KEY", "false").lower() == "true"
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

    if ALLOW_DEV and ADMIN_API_KEY and api_key == ADMIN_API_KEY:
        return True
        
    # If we got here, neither valid JWT nor valid Dev Key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Admin Access)"
    )
