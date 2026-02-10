"""
Add comprehensive dummy data for testing all features.
Run this after initial seeding to add more realistic test data.
"""

from datetime import datetime, date, timedelta, time
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import (
    Center, User, Parent, Child, FamilyLink, Lead, IntroVisit,
    Batch, Enrollment, Payment, Discount, ClassSession, Attendance,
    Curriculum, Skill, SkillProgress, ReportCard
)
from app.utils.enums import (
    UserRole, UserStatus, LeadStatus, LeadSource,
    PlanType, EnrollmentStatus, PaymentMethod, DiscountType,
    SessionStatus, AttendanceStatus, SkillLevel
)


def add_dummy_data():
    """Add comprehensive dummy data for testing"""
    db: Session = SessionLocal()

    try:
        print("Adding comprehensive dummy data...")

        # Get existing center and user
        center = db.query(Center).first()
        if not center:
            print("Error: No center found. Run seed_data.py first!")
            return

        admin_user = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        trainer = db.query(User).filter(User.role == UserRole.TRAINER).first()

        # Add more children and parents
        parents_data = [
            ("Rajesh Kumar", "+91 98765 44444", "rajesh@gmail.com"),
            ("Priya Sharma", "+91 98765 55555", "priya@gmail.com"),
            ("Amit Patel", "+91 98765 66666", "amit@gmail.com"),
            ("Sneha Gupta", "+91 98765 77777", "sneha@gmail.com"),
            ("Vikram Singh", "+91 98765 88888", "vikram@gmail.com"),
            ("Anita Reddy", "+91 98765 99999", "anita@gmail.com"),
            ("Suresh Menon", "+91 98765 12121", "suresh@gmail.com"),
            ("Kavita Desai", "+91 98765 13131", "kavita@gmail.com"),
            ("Rahul Verma", "+91 98765 14141", "rahul@gmail.com"),
            ("Meera Iyer", "+91 98765 15151", "meera@gmail.com"),
        ]

        children_data = [
            ("Aarav", "Kumar", date(2020, 3, 15), "Little Angels School"),
            ("Anaya", "Sharma", date(2019, 7, 22), "Bright Minds Academy"),
            ("Vivaan", "Patel", date(2021, 1, 10), "Sunshine Kindergarten"),
            ("Diya", "Gupta", date(2020, 5, 8), "Rainbow School"),
            ("Arjun", "Singh", date(2019, 11, 30), "Happy Kids School"),
            ("Sara", "Reddy", date(2020, 9, 18), "Little Stars Preschool"),
            ("Kabir", "Menon", date(2021, 2, 25), "Smart Kids Academy"),
            ("Isha", "Desai", date(2020, 6, 12), "Tiny Tots School"),
            ("Reyansh", "Verma", date(2019, 8, 5), "Golden Gate School"),
            ("Myra", "Iyer", date(2020, 12, 20), "Little Champs"),
        ]

        parents_list = []
        children_list = []

        for i, (name, phone, email) in enumerate(parents_data):
            parent = Parent(
                center_id=center.id,
                name=name,
                phone=phone,
                email=email,
                notes=f"Parent {i+1} - Active member"
            )
            db.add(parent)
            db.flush()
            parents_list.append(parent)

        for i, (first_name, last_name, dob, school) in enumerate(children_data):
            child = Child(
                center_id=center.id,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                school=school,
                interests=["Gymnastics", "Dancing", "Sports"][i % 3],
                notes=f"Enthusiastic learner, age {(date.today() - dob).days // 365}"
            )
            db.add(child)
            db.flush()
            children_list.append(child)

            # Link child to parent
            family_link = FamilyLink(
                center_id=center.id,
                child_id=child.id,
                parent_id=parents_list[i].id,
                relationship_type="mother" if i % 2 == 0 else "father",
                is_primary_contact=True
            )
            db.add(family_link)

        print(f"[OK] Created {len(parents_list)} parents and {len(children_list)} children")

        # Add leads in various states
        lead_statuses = [
            LeadStatus.DISCOVERY,
            LeadStatus.INTRO_SCHEDULED,
            LeadStatus.INTRO_ATTENDED,
            LeadStatus.FOLLOW_UP,
            LeadStatus.ENROLLED,
        ]

        for i in range(5):
            lead = Lead(
                center_id=center.id,
                child_id=children_list[i].id,
                status=lead_statuses[i],
                source=LeadSource.WALK_IN if i % 2 == 0 else LeadSource.REFERRAL,
                discovery_notes=f"Lead {i+1} - {lead_statuses[i].value}",
                assigned_to_user_id=admin_user.id if admin_user else None
            )
            db.add(lead)

        print(f"[OK] Created 5 leads in various states")

        # Add more batches
        batches_data = [
            ("Tiny Tots (2-3 years)", 2, 3, ["Mon", "Wed", "Fri"], time(9, 0), time(10, 0), 10),
            ("Little Movers (3-4 years)", 3, 4, ["Tue", "Thu"], time(10, 30), time(11, 30), 12),
            ("Junior Gym (4-6 years)", 4, 6, ["Mon", "Wed", "Fri"], time(15, 0), time(16, 0), 15),
            ("Advanced Kids (6-8 years)", 6, 8, ["Tue", "Thu", "Sat"], time(16, 30), time(17, 30), 12),
        ]

        batches_list = []
        for name, age_min, age_max, days, start_time, end_time, capacity in batches_data:
            batch = Batch(
                center_id=center.id,
                name=name,
                age_min=age_min,
                age_max=age_max,
                days_of_week=days,
                start_time=start_time,
                end_time=end_time,
                capacity=capacity,
                active=True
            )
            db.add(batch)
            db.flush()
            batches_list.append(batch)

        print(f"[OK] Created {len(batches_list)} batches")

        # Add enrollments (some expiring soon for renewals testing)
        today = date.today()
        enrollment_configs = [
            (children_list[0], batches_list[0], PlanType.MONTHLY, today - timedelta(days=20), today + timedelta(days=10), None),
            (children_list[1], batches_list[1], PlanType.QUARTERLY, today - timedelta(days=60), today + timedelta(days=5), None),
            (children_list[2], batches_list[2], PlanType.MONTHLY, today - timedelta(days=25), today + timedelta(days=25), None),
            (children_list[3], batches_list[0], PlanType.PAY_PER_VISIT, today - timedelta(days=10), None, 10),
            (children_list[4], batches_list[1], PlanType.WEEKLY, today - timedelta(days=5), today + timedelta(days=2), None),
            (children_list[5], batches_list[2], PlanType.MONTHLY, today - timedelta(days=15), today + timedelta(days=15), None),
            (children_list[6], batches_list[3], PlanType.QUARTERLY, today - timedelta(days=50), today + timedelta(days=40), None),
        ]

        enrollments_list = []
        for child, batch, plan_type, start_date, end_date, visits in enrollment_configs:
            enrollment = Enrollment(
                center_id=center.id,
                child_id=child.id,
                batch_id=batch.id,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                visits_included=visits,
                visits_used=0 if visits else None,
                days_selected=batch.days_of_week,
                status=EnrollmentStatus.ACTIVE,
                notes=f"{plan_type.value} enrollment"
            )
            db.add(enrollment)
            db.flush()
            enrollments_list.append(enrollment)

            # Add payment for each enrollment
            payment = Payment(
                center_id=center.id,
                enrollment_id=enrollment.id,
                amount=Decimal("5000.00") if plan_type == PlanType.MONTHLY else Decimal("12000.00"),
                currency="INR",
                method=PaymentMethod.UPI,
                reference=f"UPI{1000 + enrollment.id}",
                paid_at=start_date,
                discount_total=Decimal("0"),
                net_amount=Decimal("5000.00") if plan_type == PlanType.MONTHLY else Decimal("12000.00")
            )
            db.add(payment)

        print(f"[OK] Created {len(enrollments_list)} enrollments with payments")

        # Add class sessions for today and this week
        today_weekday = today.strftime("%a")
        sessions_list = []

        for batch in batches_list:
            # Create sessions for the next 7 days
            for days_ahead in range(7):
                session_date = today + timedelta(days=days_ahead)
                session_day = session_date.strftime("%a")

                if session_day in batch.days_of_week:
                    session = ClassSession(
                        center_id=center.id,
                        batch_id=batch.id,
                        session_date=session_date,
                        start_time=batch.start_time,
                        end_time=batch.end_time,
                        trainer_user_id=trainer.id if trainer else None,
                        status=SessionStatus.SCHEDULED if days_ahead > 0 else SessionStatus.COMPLETED
                    )
                    db.add(session)
                    db.flush()
                    sessions_list.append(session)

        print(f"[OK] Created {len(sessions_list)} class sessions for the next 7 days")

        # Add attendance records for today's sessions
        today_sessions = [s for s in sessions_list if s.session_date == today]
        attendance_count = 0

        for session in today_sessions:
            # Get enrollments for this batch
            batch_enrollments = [e for e in enrollments_list if e.batch_id == session.batch_id]

            for enrollment in batch_enrollments[:5]:  # Add attendance for first 5 students
                attendance = Attendance(
                    center_id=center.id,
                    class_session_id=session.id,
                    child_id=enrollment.child_id,
                    status=AttendanceStatus.PRESENT if attendance_count % 3 != 0 else AttendanceStatus.ABSENT,
                    marked_by_user_id=trainer.id if trainer else None,
                    marked_at=datetime.now(),
                    notes="Regular attendance" if attendance_count % 3 != 0 else "Was sick"
                )
                db.add(attendance)
                attendance_count += 1

                # Increment visits for pay-per-visit enrollments
                if enrollment.plan_type == PlanType.PAY_PER_VISIT and attendance.status == AttendanceStatus.PRESENT:
                    enrollment.visits_used += 1

        print(f"[OK] Created {attendance_count} attendance records")

        # Add curriculum and skills
        curriculum = Curriculum(
            name="Gymnastics Foundation Program",
            description="Core gymnastics skills for children aged 2-8",
            is_global=True
        )
        db.add(curriculum)
        db.flush()

        skills_data = [
            ("Forward Roll", "Basic tumbling skill", "Tumbling", 1),
            ("Backward Roll", "Reverse tumbling", "Tumbling", 2),
            ("Cartwheel", "Side rotation skill", "Tumbling", 3),
            ("Handstand", "Balance and strength", "Balance", 4),
            ("Bridge", "Back flexibility", "Flexibility", 5),
            ("Split", "Leg flexibility", "Flexibility", 6),
            ("Beam Walk", "Balance beam basics", "Balance", 7),
            ("Bar Hang", "Upper body strength", "Strength", 8),
            ("Jumping Jacks", "Coordination", "Warm-up", 9),
            ("Monkey Walk", "Animal movements", "Fun Skills", 10),
        ]

        skills_list = []
        for name, description, category, order in skills_data:
            skill = Skill(
                curriculum_id=curriculum.id,
                name=name,
                description=description,
                category=category,
                display_order=order
            )
            db.add(skill)
            db.flush()
            skills_list.append(skill)

        print(f"[OK] Created curriculum with {len(skills_list)} skills")

        # Add skill progress for enrolled children
        progress_count = 0
        skill_levels = [SkillLevel.NOT_STARTED, SkillLevel.IN_PROGRESS, SkillLevel.ACHIEVED, SkillLevel.MASTERED]

        for enrollment in enrollments_list[:5]:  # First 5 enrollments
            for i, skill in enumerate(skills_list):
                # Randomly assign progress levels
                level = skill_levels[min(i // 3, 3)]  # Progress through levels

                progress = SkillProgress(
                    center_id=center.id,
                    child_id=enrollment.child_id,
                    skill_id=skill.id,
                    level=level,
                    last_updated_at=datetime.now(),
                    updated_by_user_id=trainer.id if trainer else None,
                    notes=f"Good progress on {skill.name}"
                )
                db.add(progress)
                progress_count += 1

        print(f"[OK] Created {progress_count} skill progress records")

        # Add report cards for some children
        for i, enrollment in enumerate(enrollments_list[:3]):
            report = ReportCard(
                center_id=center.id,
                child_id=enrollment.child_id,
                period_start=today - timedelta(days=30),
                period_end=today,
                generated_at=datetime.now(),
                generated_by_user_id=admin_user.id if admin_user else None,
                summary_notes=f"Great progress this month! {enrollment.child.first_name} is doing well.",
                skill_snapshot={
                    "summary": {
                        "not_started": 2,
                        "in_progress": 4,
                        "achieved": 3,
                        "mastered": 1
                    },
                    "skills": [
                        {
                            "skill_id": skill.id,
                            "skill_name": skill.name,
                            "category": skill.category,
                            "level": skill_levels[(i + j) % 4].value,
                            "notes": f"Good work on {skill.name}"
                        }
                        for j, skill in enumerate(skills_list)
                    ]
                }
            )
            db.add(report)

        print(f"[OK] Created 3 report cards")

        # Commit all changes
        db.commit()

        print("\n" + "="*60)
        print("[SUCCESS] DUMMY DATA SUCCESSFULLY ADDED!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  • {len(parents_list)} new parents")
        print(f"  • {len(children_list)} new children")
        print(f"  • 5 new leads (various statuses)")
        print(f"  • {len(batches_list)} batches")
        print(f"  • {len(enrollments_list)} enrollments (some expiring soon)")
        print(f"  • {len(sessions_list)} class sessions (next 7 days)")
        print(f"  • {attendance_count} attendance records")
        print(f"  • 1 curriculum with {len(skills_list)} skills")
        print(f"  • {progress_count} skill progress records")
        print(f"  • 3 report cards")
        print("\n[OK] You can now test all features with realistic data!")
        print("="*60)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error adding dummy data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_dummy_data()
