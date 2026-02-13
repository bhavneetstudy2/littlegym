"""
Seed script: Populate activity categories and progression levels for
  1. Gymnastics Curriculum (non-Grade School batches)
  2. Grade School Fitness Curriculum

Run: python seed_activities.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models import Curriculum, ActivityCategory, ProgressionLevel

db = SessionLocal()

# ──────────────────────────────────────────────────
# 1. GYMNASTICS CURRICULUM
# ──────────────────────────────────────────────────
gym_curriculum = db.query(Curriculum).filter(
    Curriculum.name == "Gymnastics Foundation"
).first()

if not gym_curriculum:
    gym_curriculum = Curriculum(
        name="Gymnastics Foundation",
        level="Foundation",
        description="Core gymnastics skills tracked weekly for non-Grade School batches",
        is_global=True,
        active=True,
        curriculum_type="GYMNASTICS",
    )
    db.add(gym_curriculum)
    db.commit()
    db.refresh(gym_curriculum)
    print(f"Created Gymnastics Foundation curriculum (id={gym_curriculum.id})")
else:
    print(f"Gymnastics Foundation curriculum already exists (id={gym_curriculum.id})")

# Activity categories with progression levels (from TLG Chandigarh Excel Tracker sheet)
GYMNASTICS_ACTIVITIES = [
    {
        "name": "Cartwheel",
        "category_group": "Floor Skills",
        "order": 1,
        "levels": [
            (1, "Monkey Jump"),
            (2, "1,2,3 Cartwheel"),
            (3, "Gallop Cartwheel"),
            (4, "Half Cartwheel"),
            (5, "Full Cartwheel"),
            (6, "One-hand Cartwheel"),
            (7, "Aerial Cartwheel"),
        ],
    },
    {
        "name": "Handstand",
        "category_group": "Floor Skills",
        "order": 2,
        "levels": [
            (1, "Donkey Kick"),
            (2, "Doggie with Sore Leg"),
            (3, "Half Handstand"),
            (4, "Wall Handstand"),
            (5, "Free Handstand"),
            (6, "Handstand Hold"),
        ],
    },
    {
        "name": "Forward Roll",
        "category_group": "Floor Skills",
        "order": 3,
        "levels": [
            (1, "Log Roll"),
            (2, "Forward Roll"),
            (3, "Straddle Forward Roll"),
            (4, "Pike Forward Roll"),
            (5, "Forward Roll to Stand"),
            (6, "Dive Forward Roll"),
        ],
    },
    {
        "name": "Backward Roll",
        "category_group": "Floor Skills",
        "order": 4,
        "levels": [
            (1, "Back Safety Roll"),
            (2, "Backward Roll"),
            (3, "Straddle Backward Roll"),
            (4, "Pike Backward Roll"),
            (5, "Backward Roll to Stand"),
        ],
    },
    {
        "name": "Beam Mounts",
        "category_group": "Beam Skills",
        "order": 5,
        "levels": [
            (1, "Front Support"),
            (2, "Squat On"),
            (3, "Straddle Mount"),
            (4, "Jump to Front Support"),
            (5, "Wolf Mount"),
        ],
    },
    {
        "name": "Locomotor Skills",
        "category_group": "Beam Skills",
        "order": 6,
        "levels": [
            (1, "Walk"),
            (2, "Kick Walk"),
            (3, "Dip Walk"),
            (4, "Grapevine Walk"),
            (5, "Sideways Walk"),
            (6, "Chassé"),
        ],
    },
    {
        "name": "Balance on Beam",
        "category_group": "Beam Skills",
        "order": 7,
        "levels": [
            (1, "V Sit"),
            (2, "Leg Swings"),
            (3, "Arabesque"),
            (4, "Scale"),
            (5, "Y Balance"),
        ],
    },
    {
        "name": "Jumps on Beam",
        "category_group": "Beam Skills",
        "order": 8,
        "levels": [
            (1, "Straight Jump"),
            (2, "Tuck Jump"),
            (3, "Star Jump"),
            (4, "Split Jump"),
        ],
    },
    {
        "name": "Turns on Beam",
        "category_group": "Beam Skills",
        "order": 9,
        "levels": [
            (1, "Pivot Turn"),
            (2, "Half Turn"),
            (3, "Full Turn"),
        ],
    },
    {
        "name": "High Beams",
        "category_group": "Beam Skills",
        "order": 10,
        "levels": [
            (1, "Walk on High Beam"),
            (2, "Dip Walk on High Beam"),
            (3, "Skills on High Beam"),
        ],
    },
    {
        "name": "Beam Dismounts",
        "category_group": "Beam Skills",
        "order": 11,
        "levels": [
            (1, "Jump Variations"),
            (2, "Cartwheel Dismount"),
            (3, "Round-off Dismount"),
        ],
    },
    {
        "name": "Bar Mounts",
        "category_group": "Bar Skills",
        "order": 12,
        "levels": [
            (1, "Reach and Swings"),
            (2, "Front Support"),
            (3, "Pullover"),
            (4, "Kip"),
        ],
    },
    {
        "name": "Hangs on Bar",
        "category_group": "Bar Skills",
        "order": 13,
        "levels": [
            (1, "Sole Hang"),
            (2, "Tuck Hang"),
            (3, "Pike Hang"),
            (4, "L Hang"),
            (5, "Grip Hang"),
        ],
    },
    {
        "name": "Bar Skills",
        "category_group": "Bar Skills",
        "order": 14,
        "levels": [
            (1, "Chin Up Hold"),
            (2, "Monkey Swings"),
            (3, "Cast"),
            (4, "Lead Up to High Bar"),
            (5, "Back Hip Circle"),
        ],
    },
    {
        "name": "Bar Dismounts",
        "category_group": "Bar Skills",
        "order": 15,
        "levels": [
            (1, "Front Support to Tummy Roll"),
            (2, "Underswing Dismount"),
            (3, "Flyaway"),
        ],
    },
    {
        "name": "Vaulting",
        "category_group": "Vault",
        "order": 16,
        "levels": [
            (1, "Squat On with Spring Board"),
            (2, "Straddle On with Spring Board"),
            (3, "Flare Vault"),
            (4, "Squat Over"),
            (5, "Straddle Over"),
        ],
    },
]

for activity_def in GYMNASTICS_ACTIVITIES:
    existing = db.query(ActivityCategory).filter(
        ActivityCategory.curriculum_id == gym_curriculum.id,
        ActivityCategory.name == activity_def["name"],
    ).first()

    if existing:
        print(f"  [skip] {activity_def['name']} already exists (id={existing.id})")
        cat = existing
    else:
        cat = ActivityCategory(
            curriculum_id=gym_curriculum.id,
            name=activity_def["name"],
            category_group=activity_def["category_group"],
            measurement_type="LEVEL",
            display_order=activity_def["order"],
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        print(f"  [created] {activity_def['name']} (id={cat.id})")

    # Add progression levels
    for level_num, level_name in activity_def["levels"]:
        existing_level = db.query(ProgressionLevel).filter(
            ProgressionLevel.activity_category_id == cat.id,
            ProgressionLevel.level_number == level_num,
        ).first()
        if not existing_level:
            pl = ProgressionLevel(
                activity_category_id=cat.id,
                level_number=level_num,
                name=level_name,
            )
            db.add(pl)
    db.commit()


# ──────────────────────────────────────────────────
# 2. GRADE SCHOOL FITNESS CURRICULUM
# ──────────────────────────────────────────────────
gs_curriculum = db.query(Curriculum).filter(
    Curriculum.name == "Grade School Fitness"
).first()

if not gs_curriculum:
    gs_curriculum = Curriculum(
        name="Grade School Fitness",
        level="Grade School",
        description="Fitness assessments for Grade School students - measured numerically",
        is_global=True,
        active=True,
        curriculum_type="FITNESS",
    )
    db.add(gs_curriculum)
    db.commit()
    db.refresh(gs_curriculum)
    print(f"\nCreated Grade School Fitness curriculum (id={gs_curriculum.id})")
else:
    print(f"\nGrade School Fitness curriculum already exists (id={gs_curriculum.id})")

GRADE_SCHOOL_ACTIVITIES = [
    {"name": "Push-ups", "group": "Strength", "type": "COUNT", "unit": "reps", "order": 1},
    {"name": "Sit-ups", "group": "Strength", "type": "COUNT", "unit": "reps", "order": 2},
    {"name": "Stretches", "group": "Flexibility", "type": "MEASUREMENT", "unit": None, "order": 3},
    {"name": "Shuttle Run", "group": "Speed & Agility", "type": "TIME", "unit": "seconds", "order": 4},
    {"name": "800 Meters", "group": "Endurance", "type": "TIME", "unit": "seconds", "order": 5},
    {"name": "Speed Test", "group": "Speed & Agility", "type": "TIME", "unit": "seconds", "order": 6},
]

for act_def in GRADE_SCHOOL_ACTIVITIES:
    existing = db.query(ActivityCategory).filter(
        ActivityCategory.curriculum_id == gs_curriculum.id,
        ActivityCategory.name == act_def["name"],
    ).first()

    if existing:
        print(f"  [skip] {act_def['name']} already exists (id={existing.id})")
    else:
        cat = ActivityCategory(
            curriculum_id=gs_curriculum.id,
            name=act_def["name"],
            category_group=act_def["group"],
            measurement_type=act_def["type"],
            measurement_unit=act_def["unit"],
            display_order=act_def["order"],
        )
        db.add(cat)
        print(f"  [created] {act_def['name']}")

db.commit()

print("\nSeed complete!")
print(f"   Gymnastics curriculum ID: {gym_curriculum.id}")
print(f"   Grade School curriculum ID: {gs_curriculum.id}")

db.close()
