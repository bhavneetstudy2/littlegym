"""
Verify all students with active enrollments
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("Active students summary:")
print("="*70)

# Get all students with active enrollments
result = db.execute(text("""
    SELECT c.id, c.first_name, c.enquiry_id,
           COUNT(e.id) as active_enrollments,
           STRING_AGG(b.name, ', ') as batches,
           SUM(e.visits_used) as total_attended,
           SUM(e.visits_included) as total_included
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false AND e.status = 'ACTIVE'
    JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = :cid AND c.is_archived = false
    GROUP BY c.id, c.first_name, c.enquiry_id
    ORDER BY c.first_name
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"Total students with active enrollments: {len(result)}")
print("\nFirst 20 students:")
for r in result[:20]:
    print(f"  {r.enquiry_id or 'N/A'} | {r.first_name} | {r.batches} | {r.total_attended}/{r.total_included}")

# Check for Shahbaz specifically
print("\nShahbaz in list:", any(r.first_name.lower() == 'shahbaz' for r in result))

db.close()
