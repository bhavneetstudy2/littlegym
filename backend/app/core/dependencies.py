from typing import Optional
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
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

        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Active user

    Raises:
        HTTPException: If user is inactive
    """
    if current_user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_center_id(current_user: User = Depends(get_current_active_user)) -> Optional[int]:
    """
    Get center_id for current user (None for super admin).

    Args:
        current_user: Current authenticated user

    Returns:
        Center ID or None for super admin
    """
    return current_user.center_id


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to enforce role-based access.

    Args:
        allowed_roles: Roles allowed to access the endpoint

    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_super_admin(current_user: User = Depends(get_current_active_user)):
    """
    Require super admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User if super admin

    Raises:
        HTTPException: If user is not super admin
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
