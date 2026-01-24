from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticate user and return JWT token.

    Args:
        login_data: Email and password
        db: Database session

    Returns:
        Access token and user data

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token

    Returns:
        User data
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout():
    """
    Logout endpoint (client-side token removal).

    Note: With JWT, actual logout is handled client-side by removing the token.
    This endpoint is for consistency and future server-side token management.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}
