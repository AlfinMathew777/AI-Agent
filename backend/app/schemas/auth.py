from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

# Valid roles for the system
VALID_ROLES = ["guest", "front_desk", "housekeeping", "restaurant", "manager", "admin"]


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
    role: str = "guest"
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(VALID_ROLES)}")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    tenant_id: str
    user_id: str
    email: str
    full_name: Optional[str] = None
    allowed_pages: List[str] = []
    allowed_features: List[str] = []


class TokenData(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    tenant_id: str
    created_at: datetime


class UserPermissions(BaseModel):
    """Response model for user permissions check."""
    role: str
    allowed_pages: List[str]
    allowed_features: List[str]
    is_staff: bool
    is_management: bool
