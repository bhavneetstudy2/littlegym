"""
Fix attendance counts to only count within enrollment date ranges
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FIXING ATTENDANCE COUNTS")
print("="*70)

# First, let's see the problem
print("\nBefore fix - Top 10 enrollments with issues:")
before = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.start_date, e.end_date
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY e.visits_used DESC
    LIMIT 10
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for r in before:
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} | {r.start_date} to {r.end_date}")

# Fix: Recalculate visits_used with date range filtering
print("\nRecalculating visits_used with date range filtering...")
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id
          AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT'
          AND a.is_archived = false
          AND cs.session_date >= e.start_date
          AND (e.end_date IS NULL OR cs.session_date <= e.end_date)
    ), 0)
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

print("Done! Recalculated visits_used for all enrollments.")

# Verify
print("\nAfter fix - Checking same enrollments:")
after = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.start_date, e.end_date
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.id IN (46, 8, 145, 148, 13, 62, 35, 41, 61, 157)
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY e.visits_used DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for r in after:
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} | {r.start_date} to {r.end_date}")

# Check for remaining issues
print("\nRemaining enrollments with attended > booked:")
remaining = db.execute(text("""
    SELECT COUNT(*) as cnt
    FROM enrollments e
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"  {remaining.cnt} enrollments still have attended > booked")

if remaining.cnt > 0:
    print("\n  Examples:")
    examples = db.execute(text("""
        SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
               e.visits_included, e.visits_used, e.start_date, e.end_date
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        LEFT JOIN batches b ON e.batch_id = b.id
        WHERE e.visits_used > e.visits_included
          AND e.center_id = :cid AND e.is_archived = false
        ORDER BY e.visits_used DESC
        LIMIT 5
    """), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

    for r in examples:
        print(f"    {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included}")

# Also fix the duplicate attendance records found earlier
print("\n" + "="*70)
print("FIXING DUPLICATE ATTENDANCE RECORDS")
print("="*70)

duplicates = db.execute(text("""
    SELECT a.child_id, cs.batch_id, cs.session_date,
           STRING_AGG(a.id::text, ', ') as att_ids,
           COUNT(*) as cnt
    FROM attendance a
    JOIN class_sessions cs ON a.class_session_id = cs.id
    WHERE a.is_archived = false
      AND a.status = 'PRESENT'
      AND a.center_id = :cid
    GROUP BY a.child_id, cs.batch_id, cs.session_date
    HAVING COUNT(*) > 1
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(duplicates)} dates with duplicate attendance records")

for dup in duplicates:
    att_ids = [int(x) for x in dup.att_ids.split(', ')]
    # Keep the first record, archive the rest
    keep_id = min(att_ids)
    archive_ids = [x for x in att_ids if x != keep_id]

    print(f"  Date {dup.session_date}: keeping attendance ID {keep_id}, archiving {archive_ids}")

    for aid in archive_ids:
        db.execute(text("""
            UPDATE attendance SET is_archived = true WHERE id = :aid
        """), {"aid": aid})

db.commit()

# Recalculate again after removing duplicates
print("\nRecalculating visits_used after removing duplicates...")
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id
          AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT'
          AND a.is_archived = false
          AND cs.session_date >= e.start_date
          AND (e.end_date IS NULL OR cs.session_date <= e.end_date)
    ), 0)
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

print("Done!")

db.close()
print("\n" + "="*70)
