import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, TokenBlocklist, AuditLog
from app.core.config import settings

logger = logging.getLogger("dentalai.auth")

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with automatic salt generation."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.warning("Password verification exception: %s", e)
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token with JTI and expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = uuid.uuid4().hex
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Creates a signed JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh"
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def is_token_blocked(jti: str, db: Session) -> bool:
    """Checks whether the token JTI has been added to the logout blocklist."""
    if not jti:
        return False
    blocked = db.query(TokenBlocklist).filter(TokenBlocklist.token_jti == jti).first()
    return blocked is not None

def block_token(jti: str, expires_at: datetime, db: Session):
    """Adds a token JTI to the blocklist upon logout."""
    if not jti:
        return
    existing = db.query(TokenBlocklist).filter(TokenBlocklist.token_jti == jti).first()
    if not existing:
        block = TokenBlocklist(token_jti=jti, expires_at=expires_at)
        db.add(block)
        db.commit()

def log_audit(
    db: Session,
    action: str,
    user: Optional[User] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    status_code: Optional[int] = 200
):
    """
    Inserts a record into the audit log.
    STRICT PRIVACY RULE: Never logs sensitive patient PII, names, phone numbers, or image bytes.
    """
    try:
        user_id = user.id if user else None
        uname = user.username if user else (username or "anonymous")
        audit_entry = AuditLog(
            user_id=user_id,
            username=uname,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status_code=status_code
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to write audit log entry: %s", e)

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Dependency: Verifies JWT Bearer token and returns authenticated active User."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header with Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth.credentials
    payload = decode_token(token)
    
    jti = payload.get("jti")
    if is_token_blocked(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked upon logout. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with token was not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been disabled."
        )
    
    return user

def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency: Returns authenticated User if Bearer token present, else None."""
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_token(auth.credentials)
        jti = payload.get("jti")
        if is_token_blocked(jti, db):
            return None
        username = payload.get("sub")
        if not username:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user if user and user.is_active else None
    except Exception:
        return None

def require_roles(allowed_roles: List[str]):
    """
    Factory dependency for Role-Based Access Control (RBAC).
    Allowed roles: 'admin', 'dentist', 'staff'.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{current_user.role}' lacks permission for this resource. Required: {allowed_roles}"
            )
        return current_user
    return role_checker

