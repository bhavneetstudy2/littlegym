"""
List students starting with S
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

result = db.execute(text("""
    SELECT c.first_name, c.enquiry_id, b.name as batch, e.visits_used, e.visits_included
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false AND e.status = 'ACTIVE'
    JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = 3 AND c.is_archived = false
    AND c.first_name ILIKE 's%'
    ORDER BY c.first_name
""")).fetchall()

print("Students starting with S:")
for r in result:
    eid = r.enquiry_id or "N/A"
    print(f"  {eid} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included}")

db.close()
