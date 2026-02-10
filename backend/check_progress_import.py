"""
Check skill progress import status
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("SKILL PROGRESS IMPORT STATUS")
print("="*70)

# Check which children have progress
print("\nChildren with skill progress:")
result = db.execute(text("""
    SELECT DISTINCT c.id, c.first_name, c.enquiry_id,
           (SELECT COUNT(*) FROM skill_progress WHERE child_id = c.id) as progress_count
    FROM children c
    JOIN skill_progress sp ON sp.child_id = c.id
    WHERE c.center_id = :cid
    ORDER BY c.first_name
    LIMIT 20
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for r in result:
    eid = r.enquiry_id or "N/A"
    print(f"  {eid}: {r.first_name} - {r.progress_count} skills")

# Check if Mehar exists by enquiry_id
print("\nChecking TLGC0001 (Mehar in tracker):")
result = db.execute(text("""
    SELECT id, first_name, enquiry_id FROM children
    WHERE center_id = :cid AND enquiry_id = 'TLGC0001'
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()
print(f"  Result: {result}")

# Check sample skill_progress records to see which children they belong to
print("\nSample skill_progress records:")
result = db.execute(text("""
    SELECT sp.id, sp.child_id, c.first_name, c.enquiry_id, s.name as skill, sp.level
    FROM skill_progress sp
    JOIN children c ON sp.child_id = c.id
    JOIN skills s ON sp.skill_id = s.id
    WHERE sp.center_id = :cid
    LIMIT 10
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for r in result:
    eid = r.enquiry_id or "N/A"
    print(f"  Child {r.child_id} ({eid} - {r.first_name}): {r.skill} = {r.level}")

db.close()
