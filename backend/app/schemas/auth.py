from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TenantCreate(BaseModel):
    name: str

class TenantRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "owner" # owner, admin, staff

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    tenant_id: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None

class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    tenant_id: str
    created_at: datetime
