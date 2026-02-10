"""
Check children without Enquiry IDs
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("CHILDREN WITHOUT ENQUIRY IDs")
print("="*70)

db = SessionLocal()

# Find all children without enquiry_id
children_no_id = db.execute(text("""
    SELECT c.id, c.first_name, c.last_name, c.dob, c.created_at,
           (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enrollment_count,
           (SELECT COUNT(*) FROM attendance a
            JOIN class_sessions cs ON a.class_session_id = cs.id
            WHERE a.child_id = c.id AND a.is_archived = false) as attendance_count
    FROM children c
    WHERE (c.enquiry_id IS NULL OR c.enquiry_id = 'None' OR c.enquiry_id = '')
      AND c.center_id = :cid
    ORDER BY c.created_at DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(children_no_id)} children without Enquiry IDs:\n")

for child in children_no_id:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    print(f"Child ID: {child.id} | Name: {full_name}")
    print(f"  DOB: {child.dob}")
    print(f"  Created: {child.created_at}")
    print(f"  Enrollments: {child.enrollment_count}")
    print(f"  Attendance records: {child.attendance_count}")

    # Get parent info
    parent = db.execute(text("""
        SELECT p.name, p.phone, p.email
        FROM parents p
        JOIN family_links fl ON p.id = fl.parent_id
        WHERE fl.child_id = :cid AND fl.is_primary_contact = true
    """), {"cid": child.id}).fetchone()

    if parent:
        print(f"  Parent: {parent.name} | Phone: {parent.phone}")

    # Get enrollments
    if child.enrollment_count > 0:
        enrollments = db.execute(text("""
            SELECT b.name as batch, e.visits_used, e.visits_included, e.status, e.start_date
            FROM enrollments e
            JOIN batches b ON e.batch_id = b.id
            WHERE e.child_id = :cid AND e.is_archived = false
        """), {"cid": child.id}).fetchall()

        for e in enrollments:
            print(f"  -> {e.batch}: {e.visits_used}/{e.visits_included} ({e.status}) from {e.start_date}")

    print()

# Focus on "Mehr" specifically
print("="*70)
print("MEHR - DETAILED INVESTIGATION")
print("="*70)

mehr_children = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name, c.created_at
    FROM children c
    WHERE c.first_name ILIKE 'mehr%' AND c.center_id = :cid
    ORDER BY c.created_at
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(mehr_children)} children named Mehr/Mehar:\n")

for child in mehr_children:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    enq_id = child.enquiry_id if child.enquiry_id not in [None, 'None', ''] else "❌ NO ID"
    print(f"  {enq_id} | {full_name} | Created: {child.created_at}")

# Search in Excel
print("\n" + "="*70)
print("SEARCHING EXCEL FOR 'MEHR'")
print("="*70)

# Enrolled sheet
print("\n1. Enrolled sheet:")
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
mehr_enrolled = enrolled_df[enrolled_df['Child Name'].str.contains('mehr', case=False, na=False)]

if len(mehr_enrolled) > 0:
    for idx, row in mehr_enrolled.iterrows():
        print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')} | {row.get('Booked Classes')} classes")
else:
    print("  NOT FOUND")

# Enquiry sheet
print("\n2. Enquiry sheet:")
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
mehr_enquiry = enquiry_df[enquiry_df['Child Name'].str.contains('mehr', case=False, na=False)]

if len(mehr_enquiry) > 0:
    for idx, row in mehr_enquiry.iterrows():
        print(f"  Row {idx}: {row.get('Enquiry ID')} | {row.get('Child Name')} | Parent: {row.get('Parent Name')} | Age: {row.get('Age')}")
else:
    print("  NOT FOUND")

# Check how these children were created
print("\n" + "="*70)
print("HOW WERE THESE CHILDREN CREATED?")
print("="*70)

# Check created_by
for child in children_no_id[:5]:  # First 5
    creator = db.execute(text("""
        SELECT u.name, u.email, u.role
        FROM users u
        JOIN children c ON c.created_by_id = u.id
        WHERE c.id = :cid
    """), {"cid": child.id}).fetchone()

    full_name = f"{child.first_name} {child.last_name or ''}".strip()

    if creator:
        print(f"\n{full_name} (ID: {child.id})")
        print(f"  Created by: {creator.name} ({creator.email}) - {creator.role}")
        print(f"  Created at: {child.created_at}")
    else:
        print(f"\n{full_name} (ID: {child.id})")
        print(f"  Created by: UNKNOWN (user may be deleted)")
        print(f"  Created at: {child.created_at}")

db.close()
print("\n" + "="*70)
print("These children were likely created by a script/import without Enquiry IDs")
print("="*70)
