"""
Full reimport of Tracker data - handles all children
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from datetime import datetime
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3
EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

print("="*70)
print("FULL TRACKER DATA REIMPORT")
print("="*70)

# Get existing curriculum
curriculum = db.execute(text("SELECT id FROM curricula LIMIT 1")).fetchone()
curriculum_id = curriculum.id
print(f"Using curriculum_id: {curriculum_id}")

# Get skill mappings
skill_map = {}
for r in db.execute(text("SELECT id, name FROM skills WHERE curriculum_id = :cid"), {"cid": curriculum_id}).fetchall():
    skill_map[r.name] = r.id
print(f"Skills loaded: {len(skill_map)}")

# Read Tracker data
tracker_df = pd.read_excel(EXCEL_FILE, sheet_name='Tracker')
print(f"Tracker rows: {len(tracker_df)}")

# Skill columns
skill_columns = [
    'Cartwheel', 'Handstand', 'Forward Roll', 'Backward Roll',
    'Locomotor Skills', 'Balance on Beam', 'Jumps on Beam', 'Turns on Beam',
    'High Beams', 'Beam Mounts', 'Beam Dismounts',
    'Bar Mounts', 'Hangs on Bar', 'Bar Skills', 'Bar Dismounts', 'Vaulting'
]

def parse_skill_level(value):
    if pd.isna(value) or not value:
        return None, None
    value = str(value).strip()
    if ' - ' in value:
        parts = value.split(' - ', 1)
        try:
            level = int(parts[0])
            description = parts[1]
            return level, description
        except:
            return None, value
    return None, value

def level_to_status(level):
    if level is None:
        return 'NOT_STARTED'
    if level <= 2:
        return 'IN_PROGRESS'
    elif level <= 3:
        return 'ACHIEVED'
    else:
        return 'MASTERED'

# Clear existing progress for this center (to avoid duplicates)
print("\nClearing existing skill progress...")
db.execute(text("DELETE FROM skill_progress WHERE center_id = :cid"), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

# Import all tracker data
created = 0
not_found = 0

for idx, row in tracker_df.iterrows():
    enquiry_id = str(row.get('Enquiry ID', '')).strip()
    if not enquiry_id or enquiry_id == 'nan':
        continue

    # Find child by enquiry_id
    child = db.execute(text("""
        SELECT id FROM children WHERE center_id = :cid AND enquiry_id = :eid
    """), {"cid": CHANDIGARH_CENTER_ID, "eid": enquiry_id}).fetchone()

    if not child:
        # Try by name
        child_name = str(row.get('Child Name', '')).strip()
        if child_name and child_name != 'nan':
            child = db.execute(text("""
                SELECT id FROM children WHERE center_id = :cid
                AND LOWER(REPLACE(first_name, ' ', '')) = LOWER(REPLACE(:name, ' ', ''))
                LIMIT 1
            """), {"cid": CHANDIGARH_CENTER_ID, "name": child_name}).fetchone()

    if not child:
        not_found += 1
        continue

    child_id = child.id

    # Import skills
    for skill_name in skill_columns:
        if skill_name not in skill_map:
            continue

        skill_id = skill_map[skill_name]
        value = row.get(skill_name)
        level, description = parse_skill_level(value)

        if level is None:
            continue

        status = level_to_status(level)
        notes = f"Level {level}: {description}" if description else f"Level {level}"

        db.execute(text("""
            INSERT INTO skill_progress (center_id, child_id, skill_id, level, notes,
                last_updated_at, updated_by_user_id, created_at, updated_at, is_archived)
            VALUES (:cid, :child, :skill, :level, :notes, NOW(), 6, NOW(), NOW(), false)
        """), {"cid": CHANDIGARH_CENTER_ID, "child": child_id, "skill": skill_id, "level": status, "notes": notes})
        created += 1

db.commit()

print(f"\nCreated {created} skill progress records")
print(f"Children not found: {not_found}")

# Final verification
result = db.execute(text("""
    SELECT COUNT(DISTINCT child_id) as children, COUNT(*) as records
    FROM skill_progress WHERE center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()
print(f"\nFinal: {result.children} children with {result.records} skill records")

db.close()
print("Done!")
