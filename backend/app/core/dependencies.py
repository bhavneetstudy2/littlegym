from typing import Optional
import time
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.utils.enums import UserRole
from app.config import settings

security = HTTPBearer()


@dataclass
class CachedUser:
    """Lightweight user object for cached auth — avoids DB query per request."""
    id: int
    name: str
    email: str
    phone: str | None
    role: str
    status: str
    center_id: int | None


# In-memory user cache: avoids a DB round-trip (~400ms to remote Supabase)
# on every authenticated request. TTL = 5 min.
_user_cache: dict[int, tuple[CachedUser, float]] = {}
_USER_CACHE_TTL = 300


def _user_from_cache(user_id: int, db: Session) -> CachedUser | User | None:
    """Get user by ID, using in-memory cache to skip DB when possible."""
    now = time.time()
    cached = _user_cache.get(user_id)
    if cached:
        user, cached_at = cached
        if now - cached_at < _USER_CACHE_TTL:
            return user

    # Cache miss or expired — query DB
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        cached_user = CachedUser(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            status=user.status,
            center_id=user.center_id,
        )
        _user_cache[user_id] = (cached_user, now)
        return cached_user
    return None


def invalidate_user_cache(user_id: int = None):
    """Call after user data changes (role update, status change, etc.)."""
    if user_id:
        _user_cache.pop(user_id, None)
    else:
        _user_cache.clear()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token (cached)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = verify_token(token)

        if payload is None:
            raise credentials_exception

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)

    except JWTError:
        raise credentials_exception

    user = _user_from_cache(user_id, db)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user)
):
    """Get current active user."""
    if current_user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_center_id(current_user=Depends(get_current_active_user)) -> Optional[int]:
    """Get center_id for current user (None for super admin)."""
    return current_user.center_id


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to enforce role-based access.
    SUPER_ADMIN always has access regardless of the allowed_roles list.
    """
    def role_checker(current_user=Depends(get_current_active_user)):
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_super_admin(current_user=Depends(get_current_active_user)):
    """Require super admin role."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
