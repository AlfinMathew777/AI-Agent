import uuid
import sqlite3
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db_connection
from app.core.security.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.auth import UserCreate, UserRead, Token, TenantCreate, TenantRead, UserLogin, UserPermissions, VALID_ROLES
from app.core.errors import handle_errors, UnauthorizedError, DatabaseError
from app.core.roles import get_allowed_pages, get_allowed_features, STAFF_ROLES, MANAGEMENT_ROLES
from app.api.deps import get_current_user
from app.schemas.auth import TokenData

router = APIRouter()


@router.post("/auth/register", response_model=UserRead)
async def register(payload: UserCreate):
    """Register a new user. Creates a new tenant for the user."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Validate role
    if payload.role not in VALID_ROLES:
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )
    
    # Check if email already exists
    c.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
        
    password_hash = get_password_hash(payload.password)
    
    # Create Tenant (Owner Flow)
    tenant_id = str(uuid.uuid4())
    default_tenant_name = f"Hotel of {payload.email.split('@')[0]}"
    try:
        c.execute("INSERT INTO tenants (id, name) VALUES (?, ?)", (tenant_id, default_tenant_name))
        
        # Create User
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
        created_at=datetime.now(timezone.utc)
    )


@router.post("/auth/login", response_model=Token)
@handle_errors
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user by email/username and password.
    Returns JWT token with role-based permissions.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
        user = cur.fetchone()

        if not user:
            raise UnauthorizedError("Incorrect email or password")

        if not verify_password(form_data.password, user["password_hash"]):
            raise UnauthorizedError("Incorrect email or password")

        # Get role-based permissions
        user_role = user["role"]
        allowed_pages = get_allowed_pages(user_role)
        allowed_features = get_allowed_features(user_role)

        # Create JWT access token with extended claims
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user["id"]),
                "tenant_id": str(user["tenant_id"]),
                "role": user_role,
                "email": user["email"],
                "full_name": user["full_name"],
            },
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user_role,
            "tenant_id": user["tenant_id"],
            "user_id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "allowed_pages": allowed_pages,
            "allowed_features": allowed_features,
        }

    except sqlite3.Error as db_error:
        raise DatabaseError(str(db_error), operation="login") from db_error
    except Exception as e:
        import traceback
        print("[Auth] Login failed:", repr(e))
        traceback.print_exc()
        raise e
    finally:
        conn.close()


@router.get("/auth/me", response_model=UserPermissions)
async def get_current_user_permissions(current_user: TokenData = Depends(get_current_user)):
    """Get current user's role and permissions."""
    user_role = current_user.role or "guest"
    return UserPermissions(
        role=user_role,
        allowed_pages=get_allowed_pages(user_role),
        allowed_features=get_allowed_features(user_role),
        is_staff=user_role in STAFF_ROLES,
        is_management=user_role in MANAGEMENT_ROLES,
    )
