"""
Import Tracker data (skill progress) from Excel to database
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
print("IMPORTING TRACKER DATA")
print("="*70)

# Step 1: Create/get curriculum
print("\n1. Setting up curriculum...")
curriculum = db.execute(text("""
    SELECT id FROM curricula WHERE name = 'TLG Gymnastics Curriculum' LIMIT 1
""")).fetchone()

if not curriculum:
    # Try to use any existing curriculum
    curriculum = db.execute(text("SELECT id FROM curricula LIMIT 1")).fetchone()

if not curriculum:
    result = db.execute(text("""
        INSERT INTO curricula (name, is_global, active, created_at, updated_at, created_by_id, updated_by_id)
        VALUES ('TLG Gymnastics Curriculum', true, true, NOW(), NOW(), 6, 6)
        RETURNING id
    """))
    curriculum_id = result.fetchone()[0]
    print(f"  Created curriculum with id: {curriculum_id}")
else:
    curriculum_id = curriculum.id
    print(f"  Using existing curriculum with id: {curriculum_id}")

db.commit()

# Step 2: Define skill categories and skills
skill_definitions = {
    'Floor Skills': [
        ('Cartwheel', ['Monkey Jump', '1,2,3 Cartwheel', 'Lunge Cartwheel', 'Half Cartwheel', 'Cartwheel', 'One Hand Cartwheel', 'Aerial']),
        ('Handstand', ['Donkey Kick', 'Wall Handstand', 'Half Handstand', 'Handstand', 'Handstand Walk', 'Press Handstand']),
        ('Forward Roll', ['Egg Roll', 'Forward Roll', 'Straddle Forward Roll', 'Dive Roll', 'Forward Roll to Stand']),
        ('Backward Roll', ['Back Safety Roll', 'Backward Roll', 'Straddle Backward Roll', 'Back Extension Roll', 'Back Roll to Handstand']),
        ('Locomotor Skills', ['Bunny Hop', 'Kick Walk', 'Skip', 'Gallop', 'Sideways Walk', 'Chassé']),
    ],
    'Beam Skills': [
        ('Balance on Beam', ['V Sit', 'Leg Swings', 'Relevé Walk', 'Arabesque', 'Scale']),
        ('Jumps on Beam', ['Straight Jump', 'Tuck Jump', 'Straddle Jump', 'Split Jump', 'Leap']),
        ('Turns on Beam', ['Pivot Turn', 'Half Turn', 'Full Turn', 'Jump Turn']),
        ('High Beams', ['Walking', 'Dip Walk', 'Relevé Walk', 'Chassé', 'Leap']),
        ('Beam Mounts', ['Step On', 'Jump to Front Support', 'Squat On', 'Straddle Mount', 'Wolf Mount']),
        ('Beam Dismounts', ['Jump Off', 'Tuck Jump', 'Straddle Jump', 'Cartwheel', 'Round Off']),
    ],
    'Bar Skills': [
        ('Bar Mounts', ['Reach and Swings', 'Front Support', 'Pullover', 'Cast', 'Glide Swing']),
        ('Hangs on Bar', ['Dead Hang', 'Tuck Hang', 'Pike Hang', 'Straddle Hang', 'Inverted Hang']),
        ('Bar Skills', ['Swing', 'Cast', 'Back Hip Circle', 'Front Hip Circle', 'Kip']),
        ('Bar Dismounts', ['Front Support to Tummy Roll', 'Underswing', 'Flyaway', 'Back Hip Circle Dismount']),
    ],
    'Vault Skills': [
        ('Vaulting', ['Squat On with Spring Board', 'Straddle On with Spring Board', 'Squat Over', 'Straddle Over', 'Handspring']),
    ],
}

# Step 3: Create skills in database
print("\n2. Creating skills...")
skill_id_map = {}  # Map skill_name -> skill_id

for category, skills in skill_definitions.items():
    for skill_name, levels in skills:
        # Check if skill exists
        existing = db.execute(text("""
            SELECT id FROM skills WHERE curriculum_id = :cid AND name = :name
        """), {"cid": curriculum_id, "name": skill_name}).fetchone()

        if existing:
            skill_id_map[skill_name] = existing.id
        else:
            result = db.execute(text("""
                INSERT INTO skills (curriculum_id, name, category, display_order, created_at, updated_at)
                VALUES (:cid, :name, :cat, :order, NOW(), NOW())
                RETURNING id
            """), {"cid": curriculum_id, "name": skill_name, "cat": category, "order": len(skill_id_map)})
            skill_id_map[skill_name] = result.fetchone()[0]

db.commit()
print(f"  Created/found {len(skill_id_map)} skills")

# Step 4: Read Tracker data
print("\n3. Reading Tracker data...")
tracker_df = pd.read_excel(EXCEL_FILE, sheet_name='Tracker')
print(f"  Loaded {len(tracker_df)} records")

# Skill columns in the Excel
skill_columns = [
    'Cartwheel', 'Handstand', 'Forward Roll', 'Backward Roll',
    'Locomotor Skills', 'Balance on Beam', 'Jumps on Beam', 'Turns on Beam',
    'High Beams', 'Beam Mounts', 'Beam Dismounts',
    'Bar Mounts', 'Hangs on Bar', 'Bar Skills', 'Bar Dismounts', 'Vaulting'
]

def parse_skill_level(value):
    """Parse skill level from format 'N - Description' to level number"""
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

def level_to_status(level, max_levels=5):
    """Convert numeric level to status"""
    if level is None:
        return 'NOT_STARTED'
    if level <= 1:
        return 'IN_PROGRESS'
    elif level <= 2:
        return 'IN_PROGRESS'
    elif level <= 3:
        return 'ACHIEVED'
    else:
        return 'MASTERED'

# Step 5: Import skill progress
print("\n4. Importing skill progress...")
progress_created = 0
progress_updated = 0
children_processed = 0
children_not_found = 0

for _, row in tracker_df.iterrows():
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
        child = db.execute(text("""
            SELECT id FROM children WHERE center_id = :cid
            AND LOWER(REPLACE(first_name, ' ', '')) = LOWER(REPLACE(:name, ' ', ''))
            LIMIT 1
        """), {"cid": CHANDIGARH_CENTER_ID, "name": child_name}).fetchone()

    if not child:
        children_not_found += 1
        continue

    child_id = child.id
    children_processed += 1

    # Get parent expectation and progress check as notes
    parent_expectation = str(row.get('Parent expectation', '')) if pd.notna(row.get('Parent expectation')) else None
    progress_check = str(row.get('Progress Check', '')) if pd.notna(row.get('Progress Check')) else None

    # Import each skill
    for skill_name in skill_columns:
        if skill_name not in skill_id_map:
            continue

        skill_id = skill_id_map[skill_name]
        value = row.get(skill_name)
        level, description = parse_skill_level(value)

        if level is None:
            continue

        status = level_to_status(level)
        notes = f"Level {level}: {description}" if description else f"Level {level}"

        # Check if progress exists
        existing = db.execute(text("""
            SELECT id FROM skill_progress
            WHERE center_id = :cid AND child_id = :child AND skill_id = :skill
        """), {"cid": CHANDIGARH_CENTER_ID, "child": child_id, "skill": skill_id}).fetchone()

        if existing:
            db.execute(text("""
                UPDATE skill_progress
                SET level = :level, notes = :notes, last_updated_at = NOW(), updated_at = NOW()
                WHERE id = :pid
            """), {"level": status, "notes": notes, "pid": existing.id})
            progress_updated += 1
        else:
            db.execute(text("""
                INSERT INTO skill_progress (center_id, child_id, skill_id, level, notes,
                    last_updated_at, updated_by_user_id, created_at, updated_at, is_archived)
                VALUES (:cid, :child, :skill, :level, :notes, NOW(), 6, NOW(), NOW(), false)
            """), {"cid": CHANDIGARH_CENTER_ID, "child": child_id, "skill": skill_id, "level": status, "notes": notes})
            progress_created += 1

db.commit()

print(f"\n  Children processed: {children_processed}")
print(f"  Children not found: {children_not_found}")
print(f"  Progress records created: {progress_created}")
print(f"  Progress records updated: {progress_updated}")

# Step 6: Verify sample data
print("\n" + "="*70)
print("VERIFICATION - Sample Progress Data")
print("="*70)

# Check a few children's progress
sample_children = ['Mehar', 'Shahbaz', 'Viraj']
for name in sample_children:
    print(f"\n{name}:")
    result = db.execute(text("""
        SELECT c.first_name, s.name as skill_name, s.category, sp.level, sp.notes
        FROM skill_progress sp
        JOIN children c ON sp.child_id = c.id
        JOIN skills s ON sp.skill_id = s.id
        WHERE c.center_id = :cid AND c.first_name ILIKE :name
        ORDER BY s.category, s.name
        LIMIT 10
    """), {"cid": CHANDIGARH_CENTER_ID, "name": f"%{name}%"}).fetchall()

    if result:
        for r in result:
            print(f"  {r.category} > {r.skill_name}: {r.level} - {r.notes}")
    else:
        print("  No progress data found")

db.close()
print("\n" + "="*70)
print("Import complete!")
print("="*70)
