"""
Fix duplicate attendance records
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("Finding and fixing duplicate attendance records...")
print("="*70)

# Find duplicates (same child + same session)
duplicates = db.execute(text("""
    SELECT child_id, class_session_id, COUNT(*) as cnt
    FROM attendance
    WHERE center_id = :cid AND is_archived = false
    GROUP BY child_id, class_session_id
    HAVING COUNT(*) > 1
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"Found {len(duplicates)} duplicate attendance records")

# Delete duplicates keeping one
for dup in duplicates:
    # Get all attendance ids for this child+session
    records = db.execute(text("""
        SELECT id FROM attendance
        WHERE child_id = :child AND class_session_id = :sid AND is_archived = false
        ORDER BY id
    """), {"child": dup.child_id, "sid": dup.class_session_id}).fetchall()

    # Keep the first, archive the rest
    for rec in records[1:]:
        db.execute(text("UPDATE attendance SET is_archived = true WHERE id = :aid"), {"aid": rec.id})

db.commit()
print(f"Archived {sum(d.cnt - 1 for d in duplicates)} duplicate records")

# Recalculate visits_used
print("\nRecalculating visits_used...")
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT' AND a.is_archived = false
    ), 0)
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

# Verify Shahbaz
print("\n" + "="*70)
print("Verification - Shahbaz:")
print("="*70)
for r in db.execute(text("""
    SELECT c.id, c.first_name, c.enquiry_id,
           e.id as enr_id, b.name as batch, e.visits_used, e.visits_included,
           (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE enrollment_id = e.id) as paid
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = :cid AND c.first_name ILIKE '%shahbaz%'
    ORDER BY c.enquiry_id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} | Paid: Rs.{r.paid}")

# Also verify Abeer
print("\nVerification - Abeer:")
for r in db.execute(text("""
    SELECT c.id, c.first_name, c.enquiry_id,
           e.id as enr_id, b.name as batch, e.visits_used, e.visits_included,
           (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE enrollment_id = e.id) as paid
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = :cid AND c.first_name ILIKE '%abeer%'
    ORDER BY c.enquiry_id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} | Paid: Rs.{r.paid}")

db.close()
print("\nDone!")
