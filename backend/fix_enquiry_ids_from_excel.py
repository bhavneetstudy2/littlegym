"""
Fix children by updating their Enquiry IDs from Excel Enquiry sheet
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FIXING ENQUIRY IDs FROM EXCEL")
print("="*70)

# Load Enquiry sheet
print("\nLoading Enquiry sheet from Excel...")
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
print(f"Loaded {len(enquiry_df)} records from Enquiry sheet")

# Filter to only records with Enquiry IDs (column is named 'F')
enquiry_with_ids = enquiry_df[pd.notna(enquiry_df['F'])]
print(f"Found {len(enquiry_with_ids)} records with Enquiry IDs")

db = SessionLocal()

# Get all children without Enquiry IDs
no_id_children = db.execute(text("""
    SELECT c.id, c.first_name, c.last_name,
           p.name as parent_name, p.phone as parent_phone
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE (c.enquiry_id IS NULL OR c.enquiry_id = 'None' OR c.enquiry_id = '')
      AND c.center_id = :cid
    ORDER BY c.id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(no_id_children)} children in database without Enquiry IDs")

# Try to match and update
matched = 0
not_matched = 0

print("\nMatching children with Excel data...")

for child in no_id_children:
    # Try to match by child name + parent name
    child_full_name = f"{child.first_name} {child.last_name or ''}".strip()

    # Try exact match on child name
    matches = enquiry_with_ids[
        (enquiry_with_ids['Child Name'].str.strip().str.lower() == child.first_name.lower())
    ]

    # If multiple matches, narrow down by parent name
    if len(matches) > 1 and child.parent_name:
        matches = matches[
            matches['Parent Name'].str.contains(child.parent_name, case=False, na=False) |
            matches['Parent Name'].str.contains(child.parent_name.split()[0], case=False, na=False)
        ]

    # If multiple matches, try phone number
    if len(matches) > 1 and child.parent_phone:
        phone_clean = child.parent_phone.replace('+91-', '').replace('-', '').replace(' ', '')
        matches = matches[
            matches['Contact Number'].astype(str).str.replace('-', '').str.replace(' ', '').str.contains(phone_clean[-10:], na=False)
        ]

    if len(matches) == 1:
        enquiry_id = str(matches.iloc[0]['F'])

        # Check if this Enquiry ID is already in use
        existing = db.execute(text("""
            SELECT id, first_name FROM children
            WHERE enquiry_id = :eid AND center_id = :cid
        """), {"eid": enquiry_id, "cid": CHANDIGARH_CENTER_ID}).fetchone()

        if existing:
            print(f"  SKIP: {child_full_name:20} | {enquiry_id} already used by child {existing.id} ({existing.first_name})")
            not_matched += 1
        else:
            print(f"  MATCH: {child_full_name:20} | Parent: {child.parent_name:20} -> {enquiry_id}")

            # Update the child
            db.execute(text("""
                UPDATE children SET enquiry_id = :eid WHERE id = :cid
            """), {"eid": enquiry_id, "cid": child.id})

            matched += 1
    else:
        not_matched += 1
        if len(matches) == 0:
            print(f"  NO MATCH: {child_full_name:20} | Parent: {child.parent_name:20} (not found in Excel)")
        else:
            print(f"  MULTIPLE: {child_full_name:20} | Parent: {child.parent_name:20} ({len(matches)} matches - need manual review)")

db.commit()

print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"\nMatched and updated: {matched}")
print(f"Not matched: {not_matched}")

# Check remaining children without IDs
remaining = db.execute(text("""
    SELECT COUNT(*) as cnt
    FROM children
    WHERE (enquiry_id IS NULL OR enquiry_id = 'None' OR enquiry_id = '')
      AND center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nChildren still without Enquiry IDs: {remaining.cnt}")

if remaining.cnt > 0:
    print("\nThese are likely leads from Enquiry sheet that don't have IDs in Excel")

# Verify some specific cases
print("\n" + "="*70)
print("VERIFICATION - Mehr cases:")
print("="*70)

mehr_children = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name,
           p.name as parent_name, p.phone as parent_phone
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE c.first_name ILIKE 'mehr%' AND c.center_id = :cid
    ORDER BY c.enquiry_id NULLS LAST
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for child in mehr_children:
    full_name = f"{child.first_name} {child.last_name or ''}".strip()
    enq_id = child.enquiry_id if child.enquiry_id not in [None, 'None', ''] else "[STILL NO ID]"
    print(f"  {enq_id:15} | {full_name:20} | Parent: {child.parent_name}")

db.close()
print("\n" + "="*70)
print("UPDATE COMPLETE!")
print("="*70)
