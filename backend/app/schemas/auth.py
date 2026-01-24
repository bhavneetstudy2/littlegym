from pydantic import BaseModel, EmailStr
from typing import Optional
from app.utils.enums import UserRole, UserStatus


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    center_id: Optional[int] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response with token and user data"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
