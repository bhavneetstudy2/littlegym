"""
Fix TLGC0259 assignment - should be Mehr (Anshu Goyal), not Mehraab
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FIXING TLGC0259 ASSIGNMENT")
print("="*70)

db = SessionLocal()

# Check current state
print("\nCurrent state:")
children = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name,
           p.name as parent_name, p.phone
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE (c.enquiry_id = 'TLGC0259' OR c.first_name IN ('Mehr', 'Mehraab'))
      AND c.center_id = :cid
    ORDER BY c.id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for child in children:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    enq_id = child.enquiry_id or "[NO ID]"
    print(f"  Child {child.id}: {enq_id:15} | {full_name:20} | Parent: {child.parent_name}")

# Check Excel
print("\nExcel data for TLGC0259:")
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
tlgc0259_rows = enquiry_df[enquiry_df['F'] == 'TLGC0259']

for idx, row in tlgc0259_rows.iterrows():
    print(f"  Row {idx}: {row.get('F')} | {row.get('Child Name')} | Parent: {row.get('Parent Name')} | Phone: {row.get('Contact Number')}")

# The fix: Based on Excel, TLGC0259 should be Mehr (Anshu Goyal)
print("\n" + "="*70)
print("APPLYING FIX:")
print("="*70)

# Remove TLGC0259 from Mehraab (child 403)
print("\n1. Removing TLGC0259 from child 403 (Mehraab)...")
db.execute(text("""
    UPDATE children
    SET enquiry_id = NULL
    WHERE id = 403 AND center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID})

# Assign TLGC0259 to Mehr (child 487)
print("2. Assigning TLGC0259 to child 487 (Mehr, parent: Anshu Goyal)...")
db.execute(text("""
    UPDATE children
    SET enquiry_id = 'TLGC0259'
    WHERE id = 487 AND center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID})

db.commit()

# Verify
print("\nVerification:")
children_after = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name,
           p.name as parent_name
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE (c.enquiry_id = 'TLGC0259' OR c.first_name IN ('Mehr', 'Mehraab'))
      AND c.center_id = :cid
    ORDER BY c.id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for child in children_after:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    enq_id = child.enquiry_id or "[NO ID]"
    status = "✓ CORRECT" if (child.id == 487 and child.enquiry_id == 'TLGC0259') else ""
    print(f"  Child {child.id}: {enq_id:15} | {full_name:20} | Parent: {child.parent_name} {status}")

db.close()
print("\n" + "="*70)
print("FIX COMPLETE!")
print("="*70)
