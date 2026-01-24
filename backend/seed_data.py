"""
Seed script to populate database with test data.
Run this script to create test centers and users for development.
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.center import Center
from app.models.user import User
from app.utils.enums import UserRole, UserStatus


def seed_database():
    """Seed the database with test data"""
    db: Session = SessionLocal()

    try:
        # Check if data already exists
        existing_center = db.query(Center).first()
        if existing_center:
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        # Create test center
        center1 = Center(
            name="The Little Gym - Mumbai Central",
            city="Mumbai",
            timezone="Asia/Kolkata",
            address="123 Main Street, Mumbai, Maharashtra 400001",
            phone="+91 22 1234 5678"
        )
        db.add(center1)
        db.flush()  # Get the center ID

        center2 = Center(
            name="The Little Gym - Delhi North",
            city="Delhi",
            timezone="Asia/Kolkata",
            address="456 Park Road, Delhi 110001",
            phone="+91 11 9876 5432"
        )
        db.add(center2)
        db.flush()

        print(f"[OK] Created centers: {center1.name}, {center2.name}")

        # Create super admin (no center assignment)
        super_admin = User(
            name="Super Admin",
            email="admin@littlegym.com",
            phone="+91 98765 43210",
            password_hash=get_password_hash("admin123"),
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            center_id=None  # Super admin has no center
        )
        db.add(super_admin)

        # Create center admin for Mumbai
        center_admin = User(
            name="Raj Kumar",
            email="raj@mumbai.littlegym.com",
            phone="+91 98765 11111",
            password_hash=get_password_hash("center123"),
            role=UserRole.CENTER_ADMIN,
            status=UserStatus.ACTIVE,
            center_id=center1.id
        )
        db.add(center_admin)

        # Create trainer for Mumbai
        trainer = User(
            name="Priya Sharma",
            email="priya@mumbai.littlegym.com",
            phone="+91 98765 22222",
            password_hash=get_password_hash("trainer123"),
            role=UserRole.TRAINER,
            status=UserStatus.ACTIVE,
            center_id=center1.id
        )
        db.add(trainer)

        # Create counselor for Mumbai
        counselor = User(
            name="Amit Patel",
            email="amit@mumbai.littlegym.com",
            phone="+91 98765 33333",
            password_hash=get_password_hash("counselor123"),
            role=UserRole.COUNSELOR,
            status=UserStatus.ACTIVE,
            center_id=center1.id
        )
        db.add(counselor)

        # Create center admin for Delhi
        delhi_admin = User(
            name="Sanjay Gupta",
            email="sanjay@delhi.littlegym.com",
            phone="+91 98765 44444",
            password_hash=get_password_hash("center123"),
            role=UserRole.CENTER_ADMIN,
            status=UserStatus.ACTIVE,
            center_id=center2.id
        )
        db.add(delhi_admin)

        db.commit()

        print("\n[OK] Database seeded successfully!")
        print("\n" + "="*60)
        print("TEST CREDENTIALS:")
        print("="*60)
        print("\n1. SUPER ADMIN (Access to all centers)")
        print("   Email: admin@littlegym.com")
        print("   Password: admin123")
        print("\n2. CENTER ADMIN (Mumbai Central)")
        print("   Email: raj@mumbai.littlegym.com")
        print("   Password: center123")
        print("\n3. TRAINER (Mumbai Central)")
        print("   Email: priya@mumbai.littlegym.com")
        print("   Password: trainer123")
        print("\n4. COUNSELOR (Mumbai Central)")
        print("   Email: amit@mumbai.littlegym.com")
        print("   Password: counselor123")
        print("\n5. CENTER ADMIN (Delhi North)")
        print("   Email: sanjay@delhi.littlegym.com")
        print("   Password: center123")
        print("="*60)

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
