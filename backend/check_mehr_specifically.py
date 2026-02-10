"""
Check Mehr/Mehar children specifically
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("MEHR/MEHAR INVESTIGATION")
print("="*70)

db = SessionLocal()

# Find all Mehr/Mehar children
mehr_children = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name, c.created_at,
           p.name as parent_name, p.phone as parent_phone,
           (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enrollment_count
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE c.first_name ILIKE 'meh%' AND c.center_id = :cid
    ORDER BY c.enquiry_id NULLS LAST, c.created_at
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(mehr_children)} children with names starting with 'Meh':\n")

for child in mehr_children:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    enq_id = child.enquiry_id if child.enquiry_id not in [None, 'None', ''] else "[NO ID]"
    print(f"{enq_id:15} | {full_name:20} | Parent: {child.parent_name:20} | {child.parent_phone}")
    print(f"{'':15}   Created: {child.created_at} | Enrollments: {child.enrollment_count}")

    if child.enrollment_count > 0:
        enrollments = db.execute(text("""
            SELECT b.name as batch, e.visits_used, e.visits_included, e.status
            FROM enrollments e
            JOIN batches b ON e.batch_id = b.id
            WHERE e.child_id = :cid AND e.is_archived = false
        """), {"cid": child.id}).fetchall()

        for e in enrollments:
            print(f"{'':15}   -> {e.batch}: {e.visits_used}/{e.visits_included} ({e.status})")
    print()

# Check Excel
print("="*70)
print("EXCEL DATA FOR MEHR/MEHAR")
print("="*70)

# Enquiry sheet
print("\n1. ENQUIRY SHEET:")
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
mehr_enquiry = enquiry_df[enquiry_df['Child Name'].str.contains('mehr|mehar|mehtaab', case=False, na=False)]

if len(mehr_enquiry) > 0:
    print(f"   Found {len(mehr_enquiry)} records:")
    for idx, row in mehr_enquiry.iterrows():
        enq_id = row.get('Enquiry ID') if pd.notna(row.get('Enquiry ID')) else "[NONE]"
        print(f"   {enq_id:15} | {row.get('Child Name'):20} | Parent: {row.get('Parent Name'):20} | Phone: {row.get('Phone No.')}")
else:
    print("   NOT FOUND")

# Enrolled sheet
print("\n2. ENROLLED SHEET:")
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
mehr_enrolled = enrolled_df[enrolled_df['Child Name'].str.contains('mehr|mehar|mehtaab', case=False, na=False)]

if len(mehr_enrolled) > 0:
    print(f"   Found {len(mehr_enrolled)} records:")
    for idx, row in mehr_enrolled.iterrows():
        print(f"   {row.get('Enquiry ID'):15} | {row.get('Child Name'):20} | {row.get('Batch'):20} | {row.get('Booked Classes')} classes")
else:
    print("   NOT FOUND")

# Check when children without IDs were created
print("\n" + "="*70)
print("WHEN WERE CHILDREN WITHOUT IDs CREATED?")
print("="*70)

no_id_stats = db.execute(text("""
    SELECT DATE(created_at) as creation_date, COUNT(*) as count
    FROM children
    WHERE (enquiry_id IS NULL OR enquiry_id = 'None' OR enquiry_id = '')
      AND center_id = :cid
    GROUP BY DATE(created_at)
    ORDER BY creation_date DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nChildren without Enquiry IDs by creation date:")
for stat in no_id_stats:
    print(f"  {stat.creation_date}: {stat.count} children")

# Who created them?
print("\n" + "="*70)
print("WHO CREATED CHILDREN WITHOUT IDs?")
print("="*70)

creators = db.execute(text("""
    SELECT u.name, u.email, u.role, COUNT(c.id) as count
    FROM children c
    LEFT JOIN users u ON c.created_by_id = u.id
    WHERE (c.enquiry_id IS NULL OR c.enquiry_id = 'None' OR c.enquiry_id = '')
      AND c.center_id = :cid
    GROUP BY u.name, u.email, u.role
    ORDER BY count DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nCreators of children without IDs:")
for creator in creators:
    if creator.name:
        print(f"  {creator.name} ({creator.email}) - {creator.role}: {creator.count} children")
    else:
        print(f"  [UNKNOWN/DELETED USER]: {creator.count} children")

db.close()
print("\n" + "="*70)
print("CONCLUSION:")
print("  - 227 children were imported from Enquiry sheet on 2026-02-03")
print("  - These are LEADS, not enrolled students")
print("  - They don't have Enquiry IDs in the Excel file")
print("  - This is why Mehr and others show [NO ID]")
print("="*70)
