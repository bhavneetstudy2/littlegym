"""
Seed script: Beasts batch curriculum for The Little Gym CRM.

Creates (if not already present):
  - Curriculum: "Gymnastics Foundation"
  - All activity categories grouped by apparatus
  - 3 progression levels per activity: Not Attempted / With Support / Without Support

Usage:
  cd backend
  python seed_beasts_curriculum.py

  # To target a specific center (optional):
  python seed_beasts_curriculum.py --center-id 1

  # To also map a batch to this curriculum:
  python seed_beasts_curriculum.py --center-id 1 --batch-name "Beasts"

Safe to re-run: skips anything that already exists.
"""

import sys
import argparse
import os

# Allow running from the backend directory
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models import (
    Curriculum, ActivityCategory, ProgressionLevel, Batch, BatchMapping
)

# ── Curriculum definition ─────────────────────────────────────────────────────

CURRICULUM_NAME = "Gymnastics Foundation"

# (category_group, skill_name)
SKILLS = [
    # Floor Skills
    ("Floor Skills", "Log Roll"),
    ("Floor Skills", "Forward Roll"),
    ("Floor Skills", "Backward Roll"),
    ("Floor Skills", "Monkey Movement"),
    ("Floor Skills", "Donkey Kick"),
    ("Floor Skills", "Tummy Roll"),

    # Beam / Bar — Balance & Walking
    ("Beam & Bar - Balance", "Side Walk"),
    ("Beam & Bar - Balance", "Back Walk"),
    ("Beam & Bar - Balance", "Front Walk"),
    ("Beam & Bar - Balance", "Kick Walk"),
    ("Beam & Bar - Balance", "Low Beam Walk"),
    ("Beam & Bar - Balance", "High Beam Walk"),
    ("Beam & Bar - Balance", "Balancing"),

    # Beam / Bar — Hanging & Bar Control
    ("Beam & Bar - Hanging", "Hang Hold"),
    ("Beam & Bar - Hanging", "Hang & Swing"),
    ("Beam & Bar - Hanging", "Front Support"),
    ("Beam & Bar - Hanging", "Backseat Circle"),
    ("Beam & Bar - Hanging", "Tommy Roll"),

    # Vault
    ("Vault", "Jump on Springboard"),
    ("Vault", "Balance on Hot Dog"),
]

# Progression levels (level_number, name)
LEVELS = [
    (1, "Not Attempted"),
    (2, "With Support"),
    (3, "Without Support"),
]


def seed(center_id=None, batch_name=None):
    db = SessionLocal()
    try:
        # ── 1. Get or create curriculum ────────────────────────────────────────
        curriculum = db.query(Curriculum).filter(
            Curriculum.name == CURRICULUM_NAME,
            Curriculum.center_id == center_id,   # None = global
        ).first()

        if curriculum:
            print(f"  Curriculum '{CURRICULUM_NAME}' already exists (id={curriculum.id}) — skipping creation")
        else:
            curriculum = Curriculum(
                name=CURRICULUM_NAME,
                description="Core gymnastics skills for the Beasts batch",
                center_id=center_id,
                is_global=(center_id is None),
                active=True,
            )
            db.add(curriculum)
            db.flush()  # get the id
            print(f"  Created curriculum '{CURRICULUM_NAME}' (id={curriculum.id})")

        # ── 2. Create activity categories + progression levels ─────────────────
        created_skills = 0
        created_levels = 0

        for order, (group, skill_name) in enumerate(SKILLS):
            # Check if already exists
            cat = db.query(ActivityCategory).filter(
                ActivityCategory.curriculum_id == curriculum.id,
                ActivityCategory.name == skill_name,
            ).first()

            if not cat:
                cat = ActivityCategory(
                    curriculum_id=curriculum.id,
                    name=skill_name,
                    category_group=group,
                    measurement_type="LEVEL",
                    display_order=order,
                    active=True,
                )
                db.add(cat)
                db.flush()
                created_skills += 1
                print(f"    + Activity: [{group}] {skill_name}")
            else:
                print(f"    ~ Exists:   [{group}] {skill_name} (id={cat.id})")

            # Add progression levels if missing
            for level_num, level_name in LEVELS:
                exists = db.query(ProgressionLevel).filter(
                    ProgressionLevel.activity_category_id == cat.id,
                    ProgressionLevel.level_number == level_num,
                ).first()
                if not exists:
                    db.add(ProgressionLevel(
                        activity_category_id=cat.id,
                        level_number=level_num,
                        name=level_name,
                    ))
                    created_levels += 1

        # ── 3. Optionally map a batch ──────────────────────────────────────────
        if batch_name and center_id:
            batch = db.query(Batch).filter(
                Batch.name.ilike(batch_name),
                Batch.center_id == center_id,
            ).first()
            if not batch:
                print(f"\n  WARNING: Batch '{batch_name}' not found in center {center_id}. Skipping mapping.")
            else:
                # Upsert mapping
                mapping = db.query(BatchMapping).filter(
                    BatchMapping.batch_id == batch.id,
                    BatchMapping.center_id == center_id,
                ).first()
                if mapping:
                    mapping.curriculum_id = curriculum.id
                    print(f"\n  Updated batch mapping: '{batch.name}' -> '{CURRICULUM_NAME}'")
                else:
                    db.add(BatchMapping(
                        batch_id=batch.id,
                        curriculum_id=curriculum.id,
                        center_id=center_id,
                        is_archived=False,
                    ))
                    print(f"\n  Mapped batch '{batch.name}' -> '{CURRICULUM_NAME}'")

        db.commit()
        print(f"\nDone. Created {created_skills} skills, {created_levels} progression levels.")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


def list_centers():
    """Helper: print all centers so user knows what --center-id to pass."""
    from app.models import Center
    db = SessionLocal()
    try:
        centers = db.query(Center).order_by(Center.id).all()
        if not centers:
            print("No centers found.")
        else:
            print("\nAvailable centers:")
            for c in centers:
                print(f"  id={c.id}  name='{c.name}'")
    finally:
        db.close()


def list_batches(center_id):
    db = SessionLocal()
    try:
        batches = db.query(Batch).filter(Batch.center_id == center_id).order_by(Batch.name).all()
        if not batches:
            print(f"No batches found for center {center_id}.")
        else:
            print(f"\nBatches in center {center_id}:")
            for b in batches:
                status = "active" if b.active else "inactive"
                print(f"  id={b.id}  name='{b.name}'  ({status})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Beasts curriculum")
    parser.add_argument("--center-id", type=int, default=None,
                        help="Center ID to attach curriculum to (omit for global)")
    parser.add_argument("--batch-name", type=str, default=None,
                        help="Batch name to auto-map to this curriculum (e.g. 'Beasts')")
    parser.add_argument("--list-centers", action="store_true",
                        help="Print all centers and exit")
    parser.add_argument("--list-batches", type=int, metavar="CENTER_ID",
                        help="Print all batches for a center and exit")
    args = parser.parse_args()

    if args.list_centers:
        list_centers()
        sys.exit(0)

    if args.list_batches:
        list_batches(args.list_batches)
        sys.exit(0)

    print(f"\nSeeding curriculum '{CURRICULUM_NAME}'")
    print(f"  center_id = {args.center_id or 'None (global)'}")
    print(f"  batch     = {args.batch_name or 'not mapping'}\n")

    seed(center_id=args.center_id, batch_name=args.batch_name)
