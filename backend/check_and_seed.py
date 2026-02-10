"""Check database and seed if needed."""
from app.core.database import SessionLocal
from app.models import Center, User
from app.utils.enums import UserRole, UserStatus
from app.core.security import get_password_hash

db = SessionLocal()

# Check existing centers
centers = db.query(Center).all()
print(f"Existing centers: {len(centers)}")
for c in centers:
    print(f"  - {c.id}: {c.name}")

# Check users
users = db.query(User).all()
print(f"Existing users: {len(users)}")
for u in users:
    print(f"  - {u.id}: {u.email} ({u.role.value})")

# Add centers if none exist
if len(centers) == 0:
    print("\nNo centers found. Adding centers...")

    center1 = Center(
        name="The Little Gym - Mumbai Central",
        city="Mumbai",
        timezone="Asia/Kolkata",
        address="123 Main Street, Mumbai, Maharashtra 400001",
        phone="+91 22 1234 5678"
    )
    db.add(center1)

    center2 = Center(
        name="The Little Gym - Delhi North",
        city="Delhi",
        timezone="Asia/Kolkata",
        address="456 Park Road, Delhi 110001",
        phone="+91 11 9876 5432"
    )
    db.add(center2)

    center3 = Center(
        name="The Little Gym - Chandigarh",
        city="Chandigarh",
        timezone="Asia/Kolkata",
        address="Sector 17, Chandigarh 160017",
        phone="+91 172 2700000"
    )
    db.add(center3)

    db.commit()
    print("Centers added successfully!")

    # Refresh to get IDs
    centers = db.query(Center).all()
    for c in centers:
        print(f"  - {c.id}: {c.name}")

# Add super admin if not exists
admin = db.query(User).filter(User.email == "admin@thelittlegym.in").first()
if not admin:
    print("\nAdding super admin user...")
    admin = User(
        name="Super Admin",
        email="admin@thelittlegym.in",
        phone="+91-9999999999",
        password_hash=get_password_hash("admin123"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        center_id=None
    )
    db.add(admin)
    db.commit()
    print("Super admin created: admin@thelittlegym.in / admin123")
else:
    print(f"\nSuper admin exists: {admin.email}")

db.close()
print("\nDone!")
