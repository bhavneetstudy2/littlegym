"""
Check attendance count issues
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("CHECKING ATTENDANCE COUNT ISSUES")
print("="*70)

# Find enrollments with attended > booked
result = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.status,
           e.start_date, e.end_date, c.id as child_id, b.id as batch_id
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY e.visits_used DESC
    LIMIT 15
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(result)} enrollments with attended > booked:")
for r in result:
    print(f"\n  ID:{r.id} | {r.enquiry_id} | {r.first_name} | {r.batch}")
    print(f"    {r.visits_used}/{r.visits_included} | {r.status} | {r.start_date} to {r.end_date}")

    # Check attendance records for this child+batch
    att = db.execute(text("""
        SELECT COUNT(DISTINCT cs.session_date) as unique_dates,
               COUNT(DISTINCT a.id) as unique_records,
               COUNT(*) as total_records
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.is_archived = false AND a.status = 'PRESENT'
    """), {"child": r.child_id, "bid": r.batch_id}).fetchone()
    print(f"    Attendance: {att.total_records} records, {att.unique_records} unique, {att.unique_dates} dates")

    # Check if there are duplicate attendance records
    dups = db.execute(text("""
        SELECT cs.session_date, COUNT(*) as cnt
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.is_archived = false AND a.status = 'PRESENT'
        GROUP BY cs.session_date
        HAVING COUNT(*) > 1
    """), {"child": r.child_id, "bid": r.batch_id}).fetchall()

    if dups:
        print(f"    DUPLICATES FOUND: {len(dups)} dates with multiple records")
        for dup in dups[:5]:
            print(f"      {dup.session_date}: {dup.cnt} records")

db.close()
print("\n" + "="*70)
