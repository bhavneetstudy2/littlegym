from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.auth import UserResponse
from app.utils.enums import UserRole, UserStatus

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: UserRole
    center_id: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: UserStatus


@router.get("", response_model=List[UserResponse])
def list_users(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List users. CENTER_ADMIN sees their own center. SUPER_ADMIN can filter by center_id."""
    if current_user.role == UserRole.SUPER_ADMIN:
        query = db.query(User)
        if center_id:
            query = query.filter(User.center_id == center_id)
    elif current_user.role == UserRole.CENTER_ADMIN:
        query = db.query(User).filter(User.center_id == current_user.center_id)
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return query.order_by(User.name).all()


@router.post("", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user. CENTER_ADMIN can only create users for their center."""
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # CENTER_ADMIN can only create users for their own center
    if current_user.role == UserRole.CENTER_ADMIN:
        if data.role in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
            raise HTTPException(status_code=403, detail="CENTER_ADMIN cannot create SUPER_ADMIN or CENTER_ADMIN accounts")
        data.center_id = current_user.center_id

    # Validate center_id is set for non-super-admin users
    if data.role != UserRole.SUPER_ADMIN and not data.center_id:
        raise HTTPException(status_code=400, detail="center_id is required for non-super-admin users")

    # Check email uniqueness
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        role=data.role,
        status=UserStatus.ACTIVE,
        center_id=data.center_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user details."""
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # CENTER_ADMIN can only edit users from their own center
    if current_user.role == UserRole.CENTER_ADMIN and user.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = data.email
    if data.phone is not None:
        user.phone = data.phone
    if data.role is not None:
        if current_user.role == UserRole.CENTER_ADMIN and data.role in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
            raise HTTPException(status_code=403, detail="CENTER_ADMIN cannot assign this role")
        user.role = data.role
    if data.password is not None:
        user.password_hash = get_password_hash(data.password)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate or deactivate a user."""
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == UserRole.CENTER_ADMIN and user.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own status")

    user.status = data.status
    db.commit()
    db.refresh(user)
    return user
