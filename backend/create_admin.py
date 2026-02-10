"""Create super admin user."""
from app.core.database import SessionLocal
from app.models import User
from app.utils.enums import UserRole, UserStatus
from app.core.security import get_password_hash

db = SessionLocal()

# Check if user already exists
existing = db.query(User).filter(User.email == "admin@thelittlegym.in").first()
if existing:
    print("User admin@thelittlegym.in already exists")
else:
    user = User(
        name="Super Admin",
        email="admin@thelittlegym.in",
        phone="+91-9999999999",
        password_hash=get_password_hash("admin123"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        center_id=None
    )
    db.add(user)
    db.commit()
    print("Created user: admin@thelittlegym.in / admin123")

db.close()
