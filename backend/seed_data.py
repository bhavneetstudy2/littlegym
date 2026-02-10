"""
Seed script to populate database with test data.
Run this script to create test centers and users for development.
"""

from datetime import datetime, date, timedelta, time
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    Center, User, Parent, Child, FamilyLink, Lead, IntroVisit,
    Batch, Enrollment, Payment, Discount, ClassSession, Curriculum, Skill, SkillProgress, ReportCard
)
from app.utils.enums import (
    UserRole, UserStatus, LeadStatus, LeadSource,
    PlanType, EnrollmentStatus, PaymentMethod, DiscountType, SessionStatus, SkillLevel
)


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
        db.flush()  # Get user IDs

        print("[OK] Created users")

        # Create batches for Mumbai center
        batch1 = Batch(
            center_id=center1.id,
            name="Pre-K Gym (3-4 years)",
            age_min=3,
            age_max=4,
            days_of_week=["Mon", "Wed", "Fri"],
            start_time=time(9, 0),
            end_time=time(10, 0),
            capacity=15,
            active=True,
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(batch1)

        batch2 = Batch(
            center_id=center1.id,
            name="Kids Gym (5-7 years)",
            age_min=5,
            age_max=7,
            days_of_week=["Tue", "Thu"],
            start_time=time(16, 0),
            end_time=time(17, 0),
            capacity=12,
            active=True,
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(batch2)
        db.flush()

        print("[OK] Created batches")

        # Create sample parents, children, and leads
        # Lead 1: Discovery stage
        parent1 = Parent(
            center_id=center1.id,
            name="Neha Verma",
            phone="+91 98100 11111",
            email="neha.verma@example.com",
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(parent1)
        db.flush()

        child1 = Child(
            center_id=center1.id,
            first_name="Aarav",
            last_name="Verma",
            dob=date(2020, 5, 15),
            school="Little Stars Kindergarten",
            interests=["gymnastics", "dancing"],
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(child1)
        db.flush()

        family_link1 = FamilyLink(
            center_id=center1.id,
            child_id=child1.id,
            parent_id=parent1.id,
            relationship_type="mother",
            is_primary_contact=True,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(family_link1)

        lead1 = Lead(
            center_id=center1.id,
            child_id=child1.id,
            status=LeadStatus.DISCOVERY,
            source=LeadSource.INSTAGRAM,
            discovery_notes="Interested in gymnastics classes for 3-year-old",
            assigned_to_user_id=counselor.id,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(lead1)

        # Lead 2: Intro visit scheduled
        parent2 = Parent(
            center_id=center1.id,
            name="Rajesh Singh",
            phone="+91 98100 22222",
            email="rajesh.singh@example.com",
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(parent2)
        db.flush()

        child2 = Child(
            center_id=center1.id,
            first_name="Diya",
            last_name="Singh",
            dob=date(2019, 8, 20),
            school="Sunshine School",
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(child2)
        db.flush()

        family_link2 = FamilyLink(
            center_id=center1.id,
            child_id=child2.id,
            parent_id=parent2.id,
            relationship_type="father",
            is_primary_contact=True,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(family_link2)

        lead2 = Lead(
            center_id=center1.id,
            child_id=child2.id,
            status=LeadStatus.INTRO_SCHEDULED,
            source=LeadSource.REFERRAL,
            discovery_notes="Referred by friend, very interested",
            assigned_to_user_id=counselor.id,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(lead2)
        db.flush()

        intro_visit1 = IntroVisit(
            center_id=center1.id,
            lead_id=lead2.id,
            batch_id=batch2.id,
            scheduled_at=datetime.now() + timedelta(days=2),
            trainer_user_id=trainer.id,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(intro_visit1)

        # Lead 3: Enrolled (with active enrollment)
        parent3 = Parent(
            center_id=center1.id,
            name="Priya Reddy",
            phone="+91 98100 33333",
            email="priya.reddy@example.com",
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(parent3)
        db.flush()

        child3 = Child(
            center_id=center1.id,
            first_name="Arjun",
            last_name="Reddy",
            dob=date(2020, 3, 10),
            school="Rainbow Kids",
            interests=["sports", "climbing"],
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(child3)
        db.flush()

        family_link3 = FamilyLink(
            center_id=center1.id,
            child_id=child3.id,
            parent_id=parent3.id,
            relationship_type="mother",
            is_primary_contact=True,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(family_link3)

        lead3 = Lead(
            center_id=center1.id,
            child_id=child3.id,
            status=LeadStatus.ENROLLED,
            source=LeadSource.WALK_IN,
            discovery_notes="Walked in and enrolled immediately",
            assigned_to_user_id=counselor.id,
            created_by_id=counselor.id,
            updated_by_id=counselor.id
        )
        db.add(lead3)
        db.flush()

        # Create enrollment for child3
        enrollment1 = Enrollment(
            center_id=center1.id,
            child_id=child3.id,
            batch_id=batch1.id,
            plan_type=PlanType.MONTHLY,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            days_selected=["Mon", "Wed", "Fri"],
            status=EnrollmentStatus.ACTIVE,
            visits_used=0,
            notes="First enrollment",
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(enrollment1)
        db.flush()

        # Create payment for enrollment
        payment1 = Payment(
            center_id=center1.id,
            enrollment_id=enrollment1.id,
            amount=Decimal("5000.00"),
            currency="INR",
            method=PaymentMethod.UPI,
            reference="UPI123456",
            paid_at=datetime.now(),
            discount_total=Decimal("500.00"),
            net_amount=Decimal("4500.00"),
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(payment1)

        # Create discount for enrollment
        discount1 = Discount(
            center_id=center1.id,
            enrollment_id=enrollment1.id,
            type=DiscountType.FLAT,
            value=Decimal("500.00"),
            reason="First-time enrollment discount",
            approved_by_user_id=center_admin.id,
            applied_at=datetime.now(),
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(discount1)

        print("[OK] Created sample leads and enrollments")

        # Create global curriculum with skills
        curriculum1 = Curriculum(
            name="Gymnastics Foundation Level 1",
            description="Basic gymnastics skills for ages 3-6",
            center_id=None,
            is_global=True,
            active=True,
            created_by_id=super_admin.id,
            updated_by_id=super_admin.id
        )
        db.add(curriculum1)
        db.flush()

        # Add skills to curriculum
        skills_data = [
            {"name": "Forward Roll", "category": "Tumbling", "display_order": 1},
            {"name": "Backward Roll", "category": "Tumbling", "display_order": 2},
            {"name": "Cartwheel", "category": "Tumbling", "display_order": 3},
            {"name": "Handstand", "category": "Balance", "display_order": 4},
            {"name": "Bridge", "category": "Flexibility", "display_order": 5},
            {"name": "Pull-ups on Bar", "category": "Strength", "display_order": 6},
            {"name": "Balance Beam Walk", "category": "Balance", "display_order": 7},
            {"name": "Monkey Kick", "category": "Coordination", "display_order": 8},
        ]

        skills = []
        for skill_data in skills_data:
            skill = Skill(
                curriculum_id=curriculum1.id,
                name=skill_data["name"],
                category=skill_data["category"],
                display_order=skill_data["display_order"],
                created_by_id=super_admin.id,
                updated_by_id=super_admin.id
            )
            db.add(skill)
            skills.append(skill)

        db.flush()

        print("[OK] Created curriculum with skills")

        # Create class sessions for batch1
        session1 = ClassSession(
            center_id=center1.id,
            batch_id=batch1.id,
            session_date=date.today(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            trainer_user_id=trainer.id,
            status=SessionStatus.SCHEDULED,
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(session1)

        session2 = ClassSession(
            center_id=center1.id,
            batch_id=batch1.id,
            session_date=date.today() + timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(10, 0),
            trainer_user_id=trainer.id,
            status=SessionStatus.SCHEDULED,
            created_by_id=center_admin.id,
            updated_by_id=center_admin.id
        )
        db.add(session2)

        db.flush()

        print("[OK] Created class sessions")

        # Create skill progress for child3 (Arjun)
        progress_data = [
            {"skill": skills[0], "level": SkillLevel.ACHIEVED},  # Forward Roll
            {"skill": skills[1], "level": SkillLevel.IN_PROGRESS},  # Backward Roll
            {"skill": skills[2], "level": SkillLevel.IN_PROGRESS},  # Cartwheel
            {"skill": skills[3], "level": SkillLevel.NOT_STARTED},  # Handstand
            {"skill": skills[4], "level": SkillLevel.ACHIEVED},  # Bridge
            {"skill": skills[5], "level": SkillLevel.IN_PROGRESS},  # Pull-ups
            {"skill": skills[6], "level": SkillLevel.MASTERED},  # Balance Beam
            {"skill": skills[7], "level": SkillLevel.IN_PROGRESS},  # Monkey Kick
        ]

        for prog_data in progress_data:
            progress = SkillProgress(
                center_id=center1.id,
                child_id=child3.id,
                skill_id=prog_data["skill"].id,
                level=prog_data["level"],
                last_updated_at=datetime.now(),
                updated_by_user_id=trainer.id,
                created_by_id=trainer.id,
                updated_by_id=trainer.id
            )
            db.add(progress)

        print("[OK] Created skill progress records")

        # Create a report card for child3
        report_card = ReportCard(
            center_id=center1.id,
            child_id=child3.id,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            generated_at=datetime.now(),
            generated_by_user_id=trainer.id,
            summary_notes="Arjun has shown excellent progress in balance and flexibility. Keep practicing tumbling skills.",
            skill_snapshot={
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start": (date.today() - timedelta(days=30)).isoformat(),
                    "end": date.today().isoformat()
                },
                "skills": [
                    {"skill_name": "Forward Roll", "category": "Tumbling", "level": "ACHIEVED"},
                    {"skill_name": "Balance Beam Walk", "category": "Balance", "level": "MASTERED"},
                    {"skill_name": "Bridge", "category": "Flexibility", "level": "ACHIEVED"},
                ],
                "summary": {
                    "total_skills": 8,
                    "not_started": 1,
                    "in_progress": 4,
                    "achieved": 2,
                    "mastered": 1
                }
            },
            created_by_id=trainer.id,
            updated_by_id=trainer.id
        )
        db.add(report_card)

        print("[OK] Created report card")

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
