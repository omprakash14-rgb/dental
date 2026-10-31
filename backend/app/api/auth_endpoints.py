import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.database import get_db
from app.db.models import User, AuditLog
from app.core.config import settings
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    block_token,
    log_audit,
    get_current_user,
    require_roles,
    security_bearer
)

logger = logging.getLogger("dentalai.auth_api")
router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: Optional[str] = Field("dentist", description="'admin', 'dentist', or 'staff'")

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    status_code: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register New User")
def register_user(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    clean_username = user_in.username.strip().lower()
    clean_email = user_in.email.strip().lower()
    
    # Check duplicate username
    if db.query(User).filter(User.username == clean_username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{clean_username}' is already registered."
        )
    # Check duplicate email
    if db.query(User).filter(User.email == clean_email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{clean_email}' is already registered."
        )
    
    # Assign role (if first user in system, automatically promote to admin)
    total_users = db.query(func.count(User.id)).scalar() or 0
    assigned_role = "admin" if total_users == 0 else (user_in.role if user_in.role in ["admin", "dentist", "staff"] else "dentist")
    
    new_user = User(
        username=clean_username,
        email=clean_email,
        hashed_password=hash_password(user_in.password),
        role=assigned_role,
        full_name=user_in.full_name.strip(),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    client_ip = request.client.host if request.client else "unknown"
    log_audit(db, action="USER_REGISTER", user=new_user, resource_type="user", resource_id=str(new_user.id), ip_address=client_ip, status_code=201)
    
    logger.info("Registered user %s with role '%s'", clean_username, assigned_role)
    return new_user

@router.post("/login", response_model=TokenResponse, summary="Authenticate and Issue JWT Tokens")
def login_user(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    clean_username = login_in.username.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    
    user = db.query(User).filter(User.username == clean_username).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        log_audit(db, action="LOGIN_FAILED", username=clean_username, resource_type="auth", ip_address=client_ip, status_code=401)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        log_audit(db, action="LOGIN_BLOCKED_INACTIVE", user=user, resource_type="auth", ip_address=client_ip, status_code=403)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact your administrator."
        )
    
    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    
    log_audit(db, action="LOGIN_SUCCESS", user=user, resource_type="auth", ip_address=client_ip, status_code=200)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
def refresh_token_endpoint(refresh_in: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(refresh_in.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type for refresh.")
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is no longer active.")
    
    token_payload = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role
    }
    new_access = create_access_token(token_payload)
    new_refresh = create_refresh_token(token_payload)
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }

@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout", summary="Logout and Invalidate Token")
def logout_user(
    request: Request,
    auth=Depends(security_bearer),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if auth and auth.credentials:
        try:
            payload = decode_token(auth.credentials)
            jti = payload.get("jti")
            exp_ts = payload.get("exp")
            if jti and exp_ts:
                expires_at = datetime.fromtimestamp(exp_ts, timezone.utc)
                block_token(jti, expires_at, db)
        except Exception as e:
            logger.warning("Could not block token on logout: %s", e)
    
    client_ip = request.client.host if request.client else "unknown"
    log_audit(db, action="LOGOUT", user=current_user, resource_type="auth", ip_address=client_ip, status_code=200)
    return {"status": "success", "message": "Successfully logged out and token invalidated."}

@router.get("/users", response_model=List[UserResponse], summary="List All Users (Admin Only)")
def list_users(
    admin_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="Inspect Security Audit Logs (Admin Only)")
def get_audit_logs(
    limit: int = 100,
    admin_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs

