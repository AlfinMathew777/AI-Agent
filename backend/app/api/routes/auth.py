import uuid
import sqlite3
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db_connection
from app.core.security.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.auth import UserCreate, UserRead, Token, TenantCreate, TenantRead, UserLogin

router = APIRouter()

@router.post("/auth/register", response_model=UserRead)
async def register(payload: UserCreate):
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Simple Validation (Constraint catch is better but explicit check is fine)
    c.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
        
    password_hash = get_password_hash(payload.password)
    
    # 2. Create Tenant (Owner Flow)
    # For now, every registration creates a new tenant "Hotel of <User>"
    # In real SaaS, register might just join existing, or separate "Create Organization" flow
    tenant_id = str(uuid.uuid4())
    default_tenant_name = f"Hotel of {payload.email.split('@')[0]}"
    try:
        c.execute("INSERT INTO tenants (id, name) VALUES (?, ?)", (tenant_id, default_tenant_name))
        
        # 3. Create User
        user_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO users (id, tenant_id, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, tenant_id, payload.email, password_hash, payload.full_name, payload.role))
        
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")
        
    conn.close()
    
    return UserRead(
        id=user_id,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        tenant_id=tenant_id,
        created_at=datetime.now(timezone.utc) # Approximate for response
    )

@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = c.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['id'], "tenant_id": user['tenant_id'], "role": user['role']},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token, 
        token_type="bearer", 
        role=user['role'],
        tenant_id=user['tenant_id']
    )
