"""Fix enrollment plan_type based on Duration stored in notes.
Also fix visits_used to match actual attendance records."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # ==========================================
    # FIX 1: Map Duration to plan_type
    # ==========================================
    print("=" * 60)
    print("FIX 1: Mapping Duration to plan_type")
    print("=" * 60)

    # Duration -> PlanType mapping
    duration_map = {
        "Quarterly": "QUARTERLY",
        "Quaterly": "QUARTERLY",   # typo in data
        "Monthly": "MONTHLY",
        "monthly": "MONTHLY",
        "Semi-Annually": "YEARLY",  # closest match (no SEMI_ANNUAL enum)
        "One Time": "PAY_PER_VISIT",
    }

    # Get all enrollments with Duration in notes
    enrollments = db.execute(text("""
        SELECT id, notes FROM enrollments
        WHERE center_id = 3 AND notes IS NOT NULL AND notes LIKE '%Duration%'
    """)).fetchall()

    updated_plans = 0
    for e in enrollments:
        for duration_str, plan_type in duration_map.items():
            if f"Duration: {duration_str}" in (e.notes or ""):
                db.execute(
                    text("UPDATE enrollments SET plan_type = :pt WHERE id = :id"),
                    {"pt": plan_type, "id": e.id}
                )
                updated_plans += 1
                break

    print(f"  Updated {updated_plans} enrollment plan_types")

    # Verify
    plan_counts = db.execute(text("""
        SELECT plan_type, COUNT(*) as cnt
        FROM enrollments WHERE center_id = 3 AND is_archived = false
        GROUP BY plan_type ORDER BY cnt DESC
    """)).fetchall()
    print("\n  Plan type distribution after fix:")
    for r in plan_counts:
        print(f"    {r.plan_type}: {r.cnt}")

    # ==========================================
    # FIX 2: Fix visits_used to match actual attendance
    # ==========================================
    print("\n" + "=" * 60)
    print("FIX 2: Syncing visits_used with actual attendance records")
    print("=" * 60)

    # First, find enrollments where visits_used doesn't match attendance count
    mismatches = db.execute(text("""
        SELECT e.id, e.child_id, c.first_name, e.visits_used,
               (SELECT COUNT(*) FROM attendance a
                WHERE a.child_id = e.child_id
                AND a.center_id = e.center_id
                AND a.status = 'PRESENT') as actual_present
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        WHERE e.center_id = 3 AND e.is_archived = false
        AND e.visits_used != (
            SELECT COUNT(*) FROM attendance a
            WHERE a.child_id = e.child_id
            AND a.center_id = e.center_id
            AND a.status = 'PRESENT'
        )
    """)).fetchall()

    print(f"  Found {len(mismatches)} enrollments with mismatched visits_used")

    fixed_count = 0
    for m in mismatches:
        db.execute(
            text("UPDATE enrollments SET visits_used = :used WHERE id = :id"),
            {"used": m.actual_present, "id": m.id}
        )
        if fixed_count < 5:
            print(f"    {m.first_name}: {m.visits_used} -> {m.actual_present}")
        fixed_count += 1

    if fixed_count > 5:
        print(f"    ... and {fixed_count - 5} more")

    print(f"  Fixed {fixed_count} enrollment visit counts")

    db.commit()
    print("\nDone! Changes committed.")

except Exception as e:
    db.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
