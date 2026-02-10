"""
Seed script for Master Data Management (MDM) - Global data
Populates ClassTypes, Curricula, and Skills
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import ClassType, Curriculum, Skill


def seed_class_types():
    """Seed global class types"""
    db = SessionLocal()

    try:
        # Delete existing class types
        db.query(ClassType).delete()
        db.commit()

        class_types_data = [
            {
                "name": "Giggle Worms",
                "description": "Parent-child class for babies (0-10 months)",
                "age_min": 0,
                "age_max": 1,
                "duration_minutes": 45,
                "active": True
            },
            {
                "name": "Funny Bugs",
                "description": "Parent-child class for walkers (10-19 months)",
                "age_min": 1,
                "age_max": 2,
                "duration_minutes": 45,
                "active": True
            },
            {
                "name": "Birds",
                "description": "Parent-child class (19 months - 3 years)",
                "age_min": 2,
                "age_max": 3,
                "duration_minutes": 45,
                "active": True
            },
            {
                "name": "Bugs",
                "description": "Independent class (3-4 years)",
                "age_min": 3,
                "age_max": 4,
                "duration_minutes": 45,
                "active": True
            },
            {
                "name": "Beasts",
                "description": "Independent class (4-6 years)",
                "age_min": 4,
                "age_max": 6,
                "duration_minutes": 60,
                "active": True
            },
            {
                "name": "Super Beasts",
                "description": "Advanced class (6-9 years)",
                "age_min": 6,
                "age_max": 9,
                "duration_minutes": 60,
                "active": True
            },
            {
                "name": "Good Friends",
                "description": "Social skills development (3-5 years)",
                "age_min": 3,
                "age_max": 5,
                "duration_minutes": 60,
                "active": True
            },
            {
                "name": "Grade School",
                "description": "Sports and fitness for grade schoolers (6-12 years)",
                "age_min": 6,
                "age_max": 12,
                "duration_minutes": 60,
                "active": True
            }
        ]

        created_count = 0
        for ct_data in class_types_data:
            class_type = ClassType(**ct_data)
            db.add(class_type)
            created_count += 1
            print(f"[OK] Created class type: {ct_data['name']} (Ages {ct_data['age_min']}-{ct_data['age_max']})")

        db.commit()
        print(f"\n[SUCCESS] Successfully created {created_count} class types!")

    except Exception as e:
        print(f"[ERROR] Error seeding class types: {e}")
        db.rollback()
    finally:
        db.close()


def seed_curricula():
    """Seed global curricula and skills"""
    db = SessionLocal()

    try:
        # Delete existing curricula (cascade will delete skills)
        db.query(Curriculum).delete()
        db.commit()

        # Create curricula
        curricula_data = [
            {
                "name": "Gymnastics Foundation Level 1",
                "level": "Level 1",
                "age_min": 3,
                "age_max": 5,
                "description": "Basic gymnastics movements and motor skills for preschoolers",
                "is_global": True,
                "active": True,
                "skills": [
                    {"name": "Forward Roll", "category": "Gymnastics", "display_order": 1},
                    {"name": "Cartwheel", "category": "Gymnastics", "display_order": 2},
                    {"name": "Handstand", "category": "Gymnastics", "display_order": 3},
                    {"name": "Balance Beam Walk", "category": "Balance", "display_order": 4},
                    {"name": "Monkey Kick", "category": "Kicks", "display_order": 5},
                    {"name": "Jumping", "category": "Motor Skills", "display_order": 6},
                    {"name": "Hopping", "category": "Motor Skills", "display_order": 7},
                    {"name": "Running", "category": "Motor Skills", "display_order": 8},
                ]
            },
            {
                "name": "Gymnastics Foundation Level 2",
                "level": "Level 2",
                "age_min": 6,
                "age_max": 9,
                "description": "Intermediate gymnastics skills for elementary school children",
                "is_global": True,
                "active": True,
                "skills": [
                    {"name": "Back Roll", "category": "Gymnastics", "display_order": 1},
                    {"name": "Round-off", "category": "Gymnastics", "display_order": 2},
                    {"name": "Handstand Hold", "category": "Gymnastics", "display_order": 3},
                    {"name": "Bridge", "category": "Flexibility", "display_order": 4},
                    {"name": "Split", "category": "Flexibility", "display_order": 5},
                    {"name": "Beam Jump", "category": "Balance", "display_order": 6},
                    {"name": "Vault", "category": "Gymnastics", "display_order": 7},
                ]
            },
            {
                "name": "Motor Skills Development",
                "level": "Beginner",
                "age_min": 1,
                "age_max": 3,
                "description": "Fundamental motor skills for toddlers",
                "is_global": True,
                "active": True,
                "skills": [
                    {"name": "Walking", "category": "Gross Motor", "display_order": 1},
                    {"name": "Running", "category": "Gross Motor", "display_order": 2},
                    {"name": "Climbing", "category": "Gross Motor", "display_order": 3},
                    {"name": "Ball Throwing", "category": "Fine Motor", "display_order": 4},
                    {"name": "Ball Catching", "category": "Fine Motor", "display_order": 5},
                    {"name": "Balancing", "category": "Balance", "display_order": 6},
                ]
            },
        ]

        created_curricula = 0
        created_skills = 0

        for curr_data in curricula_data:
            skills_data = curr_data.pop("skills", [])

            curriculum = Curriculum(**curr_data)
            db.add(curriculum)
            db.flush()  # Get the curriculum ID

            created_curricula += 1
            print(f"[OK] Created curriculum: {curr_data['name']} (Level {curr_data.get('level', 'N/A')})")

            for skill_data in skills_data:
                skill = Skill(
                    curriculum_id=curriculum.id,
                    **skill_data
                )
                db.add(skill)
                created_skills += 1

        db.commit()
        print(f"\n[SUCCESS] Created {created_curricula} curricula and {created_skills} skills!")

    except Exception as e:
        print(f"[ERROR] Error seeding curricula: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Seeding Global Master Data ===\n")
    seed_class_types()
    print()
    seed_curricula()
    print("\n=== MDM Seed Complete ===")
