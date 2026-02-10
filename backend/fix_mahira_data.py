"""
Fix Mahira data issues
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FIXING MAHIRA DATA")
print("="*70)

# Check both Mahiras
print("\nCurrent state:")
for r in db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name,
           (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enr_count
    FROM children c
    WHERE c.first_name ILIKE '%mahira%' AND c.center_id = :cid
    ORDER BY c.enquiry_id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  Child {r.id}: {r.enquiry_id} - {r.first_name} ({r.enr_count} enrollments)")

# Archive the wrong Grade School enrollment for TLGC0002
print("\nArchiving wrong Grade School enrollment for TLGC0002...")
result = db.execute(text("""
    UPDATE enrollments
    SET is_archived = true
    WHERE id = 67 AND child_id = (
        SELECT id FROM children WHERE enquiry_id = 'TLGC0002' AND center_id = :cid
    )
    RETURNING id
"""), {"cid": CHANDIGARH_CENTER_ID})
archived = result.fetchone()
if archived:
    print(f"  Archived enrollment ID: {archived.id}")
else:
    print("  No enrollment archived (may have been already removed)")

db.commit()

# Verify final state
print("\nFinal state:")
for r in db.execute(text("""
    SELECT c.enquiry_id, c.first_name, b.name as batch, e.visits_used, e.visits_included
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.first_name ILIKE '%mahira%' AND c.center_id = :cid
    ORDER BY c.enquiry_id, b.name
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included}")

db.close()
print("\nDone!")
