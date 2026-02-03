from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.security.auth import decode_access_token
from app.schemas.auth import TokenData
from app.db.session import get_db_connection
import sqlite3

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    role: str = payload.get("role")
    
    if user_id is None or tenant_id is None:
        raise credentials_exception
        
    return TokenData(user_id=user_id, tenant_id=tenant_id, role=role)

async def get_current_active_user(token_data: TokenData = Depends(get_current_user)):
    # Here we could check if user is active/banned in DB
    return token_data

async def get_current_tenant(token_data: TokenData = Depends(get_current_user)) -> str:
    return token_data.tenant_id

async def verify_admin_role(user: TokenData = Depends(get_current_user)):
    if user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return user

from fastapi import Header
async def get_tenant_header(x_tenant_id: str = Header(default="default-tenant-0000")) -> str:
    # In a real app, strict validation of existence would happen here.
    return x_tenant_id

async def get_current_user_optional():
    """Optional version of get_current_user that returns None instead of raising on missing token."""
    try:
        return await get_current_user()
    except HTTPException:
        return None