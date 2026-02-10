"""
Final verification of attendance data
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FINAL DATA VERIFICATION")
print("="*70)

# Overall stats
stats = db.execute(text("""
    SELECT
        COUNT(*) as total_enrollments,
        SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active,
        SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as expired,
        SUM(CASE WHEN visits_used <= visits_included THEN 1 ELSE 0 END) as within_limit,
        SUM(CASE WHEN visits_used > visits_included THEN 1 ELSE 0 END) as over_limit
    FROM enrollments
    WHERE center_id = :cid AND is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nEnrollment Summary:")
print(f"  Total: {stats.total_enrollments}")
print(f"  Active: {stats.active} | Expired: {stats.expired}")
print(f"  Within booked limit: {stats.within_limit} ({stats.within_limit/stats.total_enrollments*100:.1f}%)")
print(f"  Over booked limit: {stats.over_limit} ({stats.over_limit/stats.total_enrollments*100:.1f}%)")

# Show the over-limit cases
if stats.over_limit > 0:
    print(f"\nCases with attendance > booked (likely renewals or extensions):")
    over = db.execute(text("""
        SELECT c.enquiry_id, c.first_name, b.name as batch,
               e.visits_used, e.visits_included,
               (e.visits_used - e.visits_included) as extra
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        JOIN batches b ON e.batch_id = b.id
        WHERE e.visits_used > e.visits_included
          AND e.center_id = :cid AND e.is_archived = false
        ORDER BY extra DESC
    """), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

    for r in over:
        print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} (+{r.extra})")

# Sample data from each batch
print(f"\n{'='*70}")
print("Sample Students by Batch:")
print("="*70)

batches = db.execute(text("SELECT id, name FROM batches WHERE center_id = :cid"),
                     {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for batch in batches:
    students = db.execute(text("""
        SELECT c.enquiry_id, c.first_name, e.visits_used, e.visits_included, e.status
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        WHERE e.batch_id = :bid AND e.center_id = :cid AND e.is_archived = false
        ORDER BY e.status, c.enquiry_id
        LIMIT 5
    """), {"bid": batch.id, "cid": CHANDIGARH_CENTER_ID}).fetchall()

    print(f"\n{batch.name} ({len(students)} shown):")
    for s in students:
        status_icon = "[A]" if s.status == "ACTIVE" else "[E]"
        print(f"  {status_icon} {s.enquiry_id} | {s.first_name} | {s.visits_used}/{s.visits_included} | {s.status}")

# Check for duplicate attendance (should be none now)
print(f"\n{'='*70}")
print("Duplicate Attendance Check:")
print("="*70)

dups = db.execute(text("""
    SELECT COUNT(*) as cnt
    FROM (
        SELECT a.child_id, cs.batch_id, cs.session_date
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.center_id = :cid AND a.is_archived = false AND a.status = 'PRESENT'
        GROUP BY a.child_id, cs.batch_id, cs.session_date
        HAVING COUNT(*) > 1
    ) sub
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

if dups.cnt == 0:
    print("[OK] No duplicate attendance records found")
else:
    print(f"[WARNING] Found {dups.cnt} dates with duplicate attendance")

db.close()
print("\n" + "="*70)
print("[COMPLETE] Verification complete!")
print("="*70)
