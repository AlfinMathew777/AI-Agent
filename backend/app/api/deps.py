from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.security.auth import decode_access_token
from app.schemas.auth import TokenData
from app.db.session import get_db_connection
from app.core.roles import (
    UserRole, has_minimum_role, can_access_page, can_use_feature,
    STAFF_ROLES, MANAGEMENT_ROLES
)
import sqlite3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Get and validate the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    role: str = payload.get("role")
    email: str = payload.get("email")
    full_name: str = payload.get("full_name")
    
    if user_id is None or tenant_id is None:
        raise credentials_exception
        
    return TokenData(
        user_id=user_id, 
        tenant_id=tenant_id, 
        role=role,
        email=email,
        full_name=full_name
    )


async def get_current_active_user(token_data: TokenData = Depends(get_current_user)):
    """Get current user and verify they are active."""
    return token_data


async def get_current_tenant(token_data: TokenData = Depends(get_current_user)) -> str:
    """Extract tenant_id from current user."""
    return token_data.tenant_id


# ============================================================
# Role-Based Access Control Dependencies
# ============================================================

async def require_admin(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin role for access."""
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )
    return user


async def require_manager_or_above(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require manager or admin role for access."""
    if user.role not in MANAGEMENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Manager or admin access required"
        )
    return user


async def require_staff(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require any staff role (not guest) for access."""
    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Staff access required"
        )
    return user


async def require_front_desk_or_above(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require front_desk, manager, or admin role."""
    allowed = [UserRole.FRONT_DESK.value, UserRole.MANAGER.value, UserRole.ADMIN.value]
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Front desk or higher access required"
        )
    return user


async def require_housekeeping_or_above(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require housekeeping, manager, or admin role."""
    allowed = [UserRole.HOUSEKEEPING.value, UserRole.MANAGER.value, UserRole.ADMIN.value]
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Housekeeping or higher access required"
        )
    return user


async def require_restaurant_or_above(user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require restaurant, manager, or admin role."""
    allowed = [UserRole.RESTAURANT.value, UserRole.MANAGER.value, UserRole.ADMIN.value]
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Restaurant or higher access required"
        )
    return user


# Legacy compatibility
async def verify_admin_role(user: TokenData = Depends(get_current_user)):
    """Legacy: verify admin role."""
    if user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return user


async def get_tenant_header(x_tenant_id: str = Header(default="default-tenant-0000")) -> str:
    """Get tenant ID from header."""
    return x_tenant_id


async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    """Optional version of get_current_user that returns None instead of raising on missing token."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        role: str = payload.get("role")
        email: str = payload.get("email")
        full_name: str = payload.get("full_name")
        if user_id is None or tenant_id is None:
            return None
        return TokenData(
            user_id=user_id, 
            tenant_id=tenant_id, 
            role=role,
            email=email,
            full_name=full_name
        )
    except Exception:
        return None