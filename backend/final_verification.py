"""
Final data verification
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("=" * 70)
print("FINAL DATA VERIFICATION - Chandigarh Center")
print("=" * 70)

# Summary stats
result = db.execute(text("""
    SELECT
        (SELECT COUNT(*) FROM children WHERE center_id = :cid AND is_archived = false) as total_children,
        (SELECT COUNT(*) FROM enrollments WHERE center_id = :cid AND is_archived = false) as total_enrollments,
        (SELECT COUNT(*) FROM enrollments WHERE center_id = :cid AND is_archived = false AND status = 'ACTIVE') as active_enrollments,
        (SELECT COUNT(*) FROM attendance WHERE center_id = :cid AND is_archived = false) as total_attendance,
        (SELECT COALESCE(SUM(amount), 0) FROM payments p JOIN enrollments e ON p.enrollment_id = e.id WHERE e.center_id = :cid) as total_paid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nSummary:")
print(f"  Total children: {result.total_children}")
print(f"  Total enrollments: {result.total_enrollments}")
print(f"  Active enrollments: {result.active_enrollments}")
print(f"  Total attendance records: {result.total_attendance}")
print(f"  Total paid: Rs.{result.total_paid:,.2f}")

# Key students verification
print("\n" + "-" * 70)
print("Key Students Verification:")
print("-" * 70)

key_students = ['Shahbaz', 'Abeer', 'Viraj', 'Yuveer']
for name in key_students:
    print(f"\n{name.upper()}:")
    for r in db.execute(text("""
        SELECT c.enquiry_id, c.first_name, b.name as batch, e.status, e.visits_used, e.visits_included,
               (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE enrollment_id = e.id) as paid
        FROM children c
        JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
        LEFT JOIN batches b ON e.batch_id = b.id
        WHERE c.center_id = :cid AND c.first_name ILIKE :name
        ORDER BY c.enquiry_id
    """), {"cid": CHANDIGARH_CENTER_ID, "name": f"%{name}%"}).fetchall():
        print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.status} | {r.visits_used}/{r.visits_included} | Paid: Rs.{r.paid}")

# Batches summary
print("\n" + "-" * 70)
print("Batches Summary:")
print("-" * 70)

for r in db.execute(text("""
    SELECT b.name,
           COUNT(DISTINCT CASE WHEN e.status = 'ACTIVE' THEN e.id END) as active_students,
           COUNT(DISTINCT e.id) as total_students,
           SUM(e.visits_used) as total_attendance
    FROM batches b
    LEFT JOIN enrollments e ON e.batch_id = b.id AND e.is_archived = false
    WHERE b.center_id = :cid
    GROUP BY b.name
    ORDER BY b.name
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {r.name}: {r.active_students} active / {r.total_students} total students, {r.total_attendance or 0} attendance")

db.close()
print("\n" + "=" * 70)
print("Verification complete!")
print("=" * 70)
