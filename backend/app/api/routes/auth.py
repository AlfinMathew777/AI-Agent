import uuid
import sqlite3
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db_connection
from app.core.security.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.auth import UserCreate, UserRead, Token, TenantCreate, TenantRead, UserLogin
from app.core.errors import handle_errors, UnauthorizedError, DatabaseError

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
@handle_errors
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user by email/username and password.

    On success, returns a JWT access token; on failure, raises an appropriate
    HotelAPIError that will be converted into a consistent JSON error response
    by the @handle_errors decorator.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
        user = cur.fetchone()

        # Don’t reveal whether the email exists – return the same message on failure
        if not user:
            raise UnauthorizedError("Incorrect email or password")

        # Verify the submitted password against the stored hash
        if not verify_password(form_data.password, user["password_hash"]):
            raise UnauthorizedError("Incorrect email or password")

        # Create JWT access token with custom claims
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user["id"]),
                "tenant_id": str(user["tenant_id"]),
                "role": user["role"],
            },
            expires_delta=access_token_expires,
        )

        # Return only the fields defined on the Token schema
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "tenant_id": user["tenant_id"],
        }

    except sqlite3.Error as db_error:
        # Wrap database errors so your error handler can format them consistently
        raise DatabaseError(str(db_error), operation="login") from db_error
    except Exception as e:
        import traceback
        print("[Auth] Login failed:", repr(e))
        traceback.print_exc()
        raise e
    finally:
        conn.close()
