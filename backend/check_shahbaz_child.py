"""
Check Shahbaz child record status
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check active enrollments count
result = db.execute(text("""
    SELECT COUNT(*) as cnt FROM enrollments
    WHERE center_id = 3 AND status = 'ACTIVE' AND is_archived = false
""")).fetchone()
print(f"Active enrollments count: {result.cnt}")

# Check if Shahbaz has any child record
result = db.execute(text("""
    SELECT c.id, c.first_name, c.is_archived
    FROM children c
    WHERE c.center_id = 3 AND c.first_name ILIKE '%shahbaz%'
""")).fetchall()
print(f"\nChildren with Shahbaz name:")
for r in result:
    print(f"  ID: {r.id}, Name: {r.first_name}, Archived: {r.is_archived}")

# Check Shahbaz's enrollments specifically
result = db.execute(text("""
    SELECT e.id, e.status, e.is_archived, b.name as batch
    FROM enrollments e
    JOIN batches b ON e.batch_id = b.id
    WHERE e.child_id = (SELECT id FROM children WHERE first_name ILIKE '%shahbaz%' AND center_id = 3 LIMIT 1)
""")).fetchall()
print(f"\nShahbaz enrollments:")
for r in result:
    print(f"  ID: {r.id}, Batch: {r.batch}, Status: {r.status}, Archived: {r.is_archived}")

db.close()
