"""
Create The Little Gym Chandigarh with complete demo data
"""
import sys
import os
from datetime import datetime, time, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import (
    Center, User, Batch, BatchMapping, ClassType,
    Child, Parent, FamilyLink, Lead
)
from app.utils.enums import UserRole, LeadStatus, LeadSource


def create_chandigarh_center():
    """Create Chandigarh center with complete demo data"""
    db = SessionLocal()

    try:
        print("=== Creating The Little Gym Chandigarh ===\n")

        # Check if Chandigarh already exists
        existing = db.query(Center).filter(Center.code == "CHD").first()
        if existing:
            print("[INFO] Chandigarh center already exists, using existing one")
            center = existing
        else:
            # Create Chandigarh center
            print("[1/6] Creating Chandigarh center...")
            center = Center(
                name="The Little Gym Chandigarh",
                code="CHD",
                city="Chandigarh",
                state="Punjab",
                address="SCO 123, Sector 17, Chandigarh",
                phone="+91-172-1234567",
                email="chandigarh@thelittlegym.in",
                timezone="Asia/Kolkata",
                active=True
            )
            db.add(center)
            db.commit()
            db.refresh(center)
            print(f"  [OK] Created center: {center.name} (ID: {center.id})")

        # Get class types
        class_types = db.query(ClassType).filter(ClassType.active == True).all()
        class_type_map = {ct.name: ct for ct in class_types}

        # Create batches for Chandigarh
        print("\n[2/6] Creating batches...")
        batch_configs = [
            {
                "name": "Giggle Worms Morning",
                "class_type": "Giggle Worms",
                "age_min": 0,
                "age_max": 1,
                "days": ["Monday", "Wednesday"],
                "start": "10:00",
                "end": "10:45",
                "capacity": 8
            },
            {
                "name": "Birds MWF Batch",
                "class_type": "Birds",
                "age_min": 2,
                "age_max": 3,
                "days": ["Monday", "Wednesday", "Friday"],
                "start": "11:00",
                "end": "11:45",
                "capacity": 12
            },
            {
                "name": "Bugs Afternoon",
                "class_type": "Bugs",
                "age_min": 3,
                "age_max": 4,
                "days": ["Monday", "Wednesday", "Friday"],
                "start": "15:00",
                "end": "15:45",
                "capacity": 12
            },
            {
                "name": "Beasts Evening",
                "class_type": "Beasts",
                "age_min": 4,
                "age_max": 6,
                "days": ["Tuesday", "Thursday", "Saturday"],
                "start": "16:00",
                "end": "17:00",
                "capacity": 12
            },
            {
                "name": "Super Beasts Advanced",
                "class_type": "Super Beasts",
                "age_min": 6,
                "age_max": 9,
                "days": ["Tuesday", "Thursday", "Saturday"],
                "start": "17:15",
                "end": "18:15",
                "capacity": 12
            },
        ]

        batches = []
        for config in batch_configs:
            # Check if batch already exists
            existing_batch = db.query(Batch).filter(
                Batch.center_id == center.id,
                Batch.name == config["name"],
                Batch.is_archived == False
            ).first()

            if not existing_batch:
                start_parts = config["start"].split(":")
                end_parts = config["end"].split(":")

                batch = Batch(
                    center_id=center.id,
                    name=config["name"],
                    age_min=config["age_min"],
                    age_max=config["age_max"],
                    days_of_week=config["days"],
                    start_time=time(int(start_parts[0]), int(start_parts[1])),
                    end_time=time(int(end_parts[0]), int(end_parts[1])),
                    capacity=config["capacity"],
                    active=True,
                                    )
                db.add(batch)
                db.flush()

                # Create batch mapping
                if config["class_type"] in class_type_map:
                    mapping = BatchMapping(
                        center_id=center.id,
                        batch_id=batch.id,
                        class_type_id=class_type_map[config["class_type"]].id,
                        curriculum_id=None,
                                            )
                    db.add(mapping)

                batches.append(batch)
                print(f"  [OK] Created batch: {config['name']}")
            else:
                batches.append(existing_batch)
                print(f"  [SKIP] Batch already exists: {config['name']}")

        db.commit()

        # Create demo leads
        print("\n[3/6] Creating demo leads...")
        demo_leads_data = [
            {
                "child_name": "Aarav",
                "child_last": "Sharma",
                "child_dob": "2020-03-15",
                "parent_name": "Rajesh Sharma",
                "parent_phone": "+91-98765-43210",
                "parent_email": "rajesh.sharma@example.com",
                "source": LeadSource.WALK_IN,
                "status": LeadStatus.DISCOVERY,
                "school": "Little Buds Preschool"
            },
            {
                "child_name": "Ananya",
                "child_last": "Patel",
                "child_dob": "2019-08-22",
                "parent_name": "Priya Patel",
                "parent_phone": "+91-98765-43211",
                "parent_email": "priya.patel@example.com",
                "source": LeadSource.INSTAGRAM,
                "status": LeadStatus.INTRO_SCHEDULED,
                "school": "Sunshine Academy"
            },
            {
                "child_name": "Arjun",
                "child_last": "Singh",
                "child_dob": "2018-12-10",
                "parent_name": "Amit Singh",
                "parent_phone": "+91-98765-43212",
                "parent_email": "amit.singh@example.com",
                "source": LeadSource.REFERRAL,
                "status": LeadStatus.FOLLOW_UP,
                "school": "Green Valley School"
            },
            {
                "child_name": "Diya",
                "child_last": "Kapoor",
                "child_dob": "2020-05-18",
                "parent_name": "Neha Kapoor",
                "parent_phone": "+91-98765-43213",
                "parent_email": "neha.kapoor@example.com",
                "source": LeadSource.FACEBOOK,
                "status": LeadStatus.DISCOVERY,
                "school": None
            },
            {
                "child_name": "Ishaan",
                "child_last": "Mehta",
                "child_dob": "2019-11-03",
                "parent_name": "Vikram Mehta",
                "parent_phone": "+91-98765-43214",
                "parent_email": "vikram.mehta@example.com",
                "source": LeadSource.GOOGLE,
                "status": LeadStatus.INTRO_ATTENDED,
                "school": "Rainbow Kids"
            },
        ]

        created_leads = 0
        for lead_data in demo_leads_data:
            # Check if lead already exists (by phone)
            existing_parent = db.query(Parent).filter(
                Parent.center_id == center.id,
                Parent.phone == lead_data["parent_phone"]
            ).first()

            if not existing_parent:
                # Create child
                child = Child(
                    center_id=center.id,
                    first_name=lead_data["child_name"],
                    last_name=lead_data["child_last"],
                    dob=datetime.strptime(lead_data["child_dob"], "%Y-%m-%d").date() if lead_data["child_dob"] else None,
                    school=lead_data["school"],
                    interests=["gymnastics", "play"],
                                    )
                db.add(child)
                db.flush()

                # Create parent
                parent = Parent(
                    center_id=center.id,
                    name=lead_data["parent_name"],
                    phone=lead_data["parent_phone"],
                    email=lead_data["parent_email"],
                                    )
                db.add(parent)
                db.flush()

                # Create family link
                family_link = FamilyLink(
                    center_id=center.id,
                    child_id=child.id,
                    parent_id=parent.id,
                    relationship_type="parent",
                    is_primary_contact=True,
                                    )
                db.add(family_link)

                # Create lead
                lead = Lead(
                    center_id=center.id,
                    child_id=child.id,
                    status=lead_data["status"],
                    source=lead_data["source"],
                    discovery_notes=f"Interested in {lead_data['status'].value} program",
                                    )
                db.add(lead)

                created_leads += 1
                print(f"  [OK] Created lead: {lead_data['child_name']} {lead_data['child_last']} ({lead_data['status'].value})")

        db.commit()
        print(f"  [SUMMARY] Created {created_leads} new leads")

        # Create a user for Chandigarh
        print("\n[4/6] Creating Chandigarh center admin...")
        existing_user = db.query(User).filter(
            User.center_id == center.id,
            User.email == "admin.chd@thelittlegym.in"
        ).first()

        if not existing_user:
            from app.core.security import get_password_hash

            user = User(
                center_id=center.id,
                name="Chandigarh Admin",
                email="admin.chd@thelittlegym.in",
                phone="+91-172-7654321",
                password_hash=get_password_hash("password123"),
                role=UserRole.CENTER_ADMIN,
                status="ACTIVE",
                            )
            db.add(user)
            db.commit()
            print(f"  [OK] Created user: {user.email}")
            print(f"       Password: password123")
        else:
            print(f"  [SKIP] User already exists: {existing_user.email}")

        # Summary
        print("\n[5/6] Summary for Chandigarh:")
        total_batches = db.query(Batch).filter(Batch.center_id == center.id, Batch.is_archived == False).count()
        total_leads = db.query(Lead).filter(Lead.center_id == center.id, Lead.is_archived == False).count()
        total_users = db.query(User).filter(User.center_id == center.id).count()

        print(f"  - Total Batches: {total_batches}")
        print(f"  - Total Leads: {total_leads}")
        print(f"  - Total Users: {total_users}")

        print("\n[SUCCESS] Chandigarh center setup complete!")
        print(f"\nCenter ID: {center.id}")
        print(f"Center Name: {center.name}")
        print(f"Center Code: {center.code}")

    except Exception as e:
        print(f"\n[ERROR] Failed to create Chandigarh center: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_chandigarh_center()
