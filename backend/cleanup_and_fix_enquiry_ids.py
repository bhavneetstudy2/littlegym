"""
Step 1: Remove duplicates where same parent+child exists multiple times
Step 2: Fix enquiry IDs to match Excel using parent+child as unique key
"""
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

print("=" * 80)
print("CLEANUP DUPLICATES AND FIX ENQUIRY IDs")
print("=" * 80)

# Read Excel
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')

# Build mapping: (parent_name, child_first_name) -> enquiry_id
excel_mapping = {}
for idx, row in enquiry_df.iterrows():
    enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
    child_name = str(row.get('Child Name')).strip() if pd.notna(row.get('Child Name')) else None
    parent_name = str(row.get('Parent Name')).strip() if pd.notna(row.get('Parent Name')) else None

    if enquiry_id and child_name and enquiry_id != 'nan' and child_name != 'nan':
        if not parent_name or parent_name == 'nan':
            parent_name = 'Unknown'

        key = (parent_name.lower(), child_name.lower())

        if key not in excel_mapping:
            excel_mapping[key] = enquiry_id

print(f"Found {len(excel_mapping)} unique parent+child combinations in Excel")

engine = create_engine(TARGET_DB)

# Step 1: Find and remove duplicates
print("\nStep 1: Finding duplicates (same parent+child)...")
with engine.connect() as conn:
    # Find duplicates
    result = conn.execute(text("""
        SELECT
            LOWER(COALESCE(p.name, 'Unknown')) as parent_name,
            LOWER(c.first_name) as child_name,
            COUNT(*) as count,
            ARRAY_AGG(c.id ORDER BY c.id) as child_ids,
            ARRAY_AGG(c.enquiry_id ORDER BY c.id) as enquiry_ids
        FROM children c
        LEFT JOIN family_links fl ON c.id = fl.child_id AND c.center_id = fl.center_id AND fl.is_primary_contact = TRUE
        LEFT JOIN parents p ON fl.parent_id = p.id
        WHERE c.center_id = :center_id
        GROUP BY LOWER(COALESCE(p.name, 'Unknown')), LOWER(c.first_name)
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """), {"center_id": CENTER_ID})

    duplicates = result.fetchall()
    print(f"Found {len(duplicates)} parent+child combinations with duplicates")

duplicates_to_delete = []

for dup in duplicates:
    parent_name, child_name, count, child_ids, enquiry_ids = dup
    key = (parent_name, child_name)

    print(f"\n  {parent_name} + {child_name}: {count} records")
    print(f"    IDs: {child_ids}")
    print(f"    Enquiry IDs: {enquiry_ids}")

    # Find which one matches Excel
    if key in excel_mapping:
        correct_enquiry_id = excel_mapping[key]
        print(f"    Excel has: {correct_enquiry_id}")

        # Keep the child with matching enquiry_id, delete others
        for i, (cid, eid) in enumerate(zip(child_ids, enquiry_ids)):
            if eid != correct_enquiry_id:
                duplicates_to_delete.append(cid)
                print(f"    DELETE child #{cid} (enquiry_id: {eid})")
            else:
                print(f"    KEEP child #{cid} (enquiry_id: {eid})")

print(f"\n\nTotal children to delete: {len(duplicates_to_delete)}")

if duplicates_to_delete and input("Delete duplicates? (yes/no): ").lower() == 'yes':
    with engine.begin() as conn:
        # Delete leads
        result = conn.execute(
            text("DELETE FROM leads WHERE child_id = ANY(:ids) RETURNING id"),
            {"ids": duplicates_to_delete}
        )
        print(f"Deleted {result.rowcount} leads")

        # Delete family_links
        result = conn.execute(
            text("DELETE FROM family_links WHERE child_id = ANY(:ids) RETURNING id"),
            {"ids": duplicates_to_delete}
        )
        print(f"Deleted {result.rowcount} family_links")

        # Delete children
        result = conn.execute(
            text("DELETE FROM children WHERE id = ANY(:ids) RETURNING id"),
            {"ids": duplicates_to_delete}
        )
        print(f"Deleted {result.rowcount} children")

    print("\n" + "=" * 80)
    print("DUPLICATES REMOVED!")
    print("=" * 80)
else:
    print("\nSkipping deletion. No changes made.")

print("\nDone!")
