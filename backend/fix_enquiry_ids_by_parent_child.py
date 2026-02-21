"""
Fix enquiry IDs using Parent Name + Child Name as unique identifier
Each parent+child combination is a unique child
"""
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

print("=" * 80)
print("FIX ENQUIRY IDs USING PARENT + CHILD NAME")
print("=" * 80)

# Read Excel
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
print(f"\nRead {len(enquiry_df)} rows from Enquiry sheet")

# Build mapping: (parent_name, child_first_name) -> enquiry_id
excel_mapping = {}
for idx, row in enquiry_df.iterrows():
    enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
    child_name = str(row.get('Child Name')).strip() if pd.notna(row.get('Child Name')) else None
    parent_name = str(row.get('Parent Name')).strip() if pd.notna(row.get('Parent Name')) else None

    if enquiry_id and child_name and enquiry_id != 'nan' and child_name != 'nan':
        # Normalize parent name (handle None/empty)
        if not parent_name or parent_name == 'nan':
            parent_name = 'Unknown'

        key = (parent_name.lower(), child_name.lower())

        # Store mapping
        if key not in excel_mapping:
            excel_mapping[key] = enquiry_id
        else:
            # If duplicate, keep the first one (could be same child appearing multiple times)
            print(f"  Duplicate parent+child: {parent_name} + {child_name} with IDs {excel_mapping[key]} and {enquiry_id}")

print(f"\nFound {len(excel_mapping)} unique parent+child combinations in Excel")

engine = create_engine(TARGET_DB)

# Get all children with their primary parent
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            c.id,
            c.first_name,
            c.enquiry_id as current_enquiry_id,
            p.name as parent_name
        FROM children c
        LEFT JOIN family_links fl ON c.id = fl.child_id AND c.center_id = fl.center_id AND fl.is_primary_contact = TRUE
        LEFT JOIN parents p ON fl.parent_id = p.id
        WHERE c.center_id = :center_id
        ORDER BY c.id
    """), {"center_id": CENTER_ID})

    db_children = result.fetchall()

print(f"Found {len(db_children)} children in database")

# Match and update
matched = 0
not_matched = 0
updated = 0
already_correct = 0

with engine.begin() as conn:
    for child in db_children:
        child_id, child_name, current_enquiry_id, parent_name = child

        # Normalize
        if not parent_name or parent_name == 'nan':
            parent_name = 'Unknown'

        key = (parent_name.lower(), child_name.lower())

        # Find in Excel mapping
        if key in excel_mapping:
            excel_enquiry_id = excel_mapping[key]
            matched += 1

            # Update if different
            if current_enquiry_id != excel_enquiry_id:
                try:
                    conn.execute(text("""
                        UPDATE children
                        SET enquiry_id = :enquiry_id
                        WHERE id = :child_id
                    """), {
                        "enquiry_id": excel_enquiry_id,
                        "child_id": child_id
                    })

                    updated += 1
                    if updated <= 20:  # Show first 20 updates
                        print(f"  Updated: {parent_name} + {child_name}: {current_enquiry_id} -> {excel_enquiry_id}")
                except Exception as e:
                    print(f"  ERROR updating {child_id} ({child_name}): {e}")
            else:
                already_correct += 1
        else:
            not_matched += 1
            if not_matched <= 10:  # Show first 10 not matched
                print(f"  NOT MATCHED in Excel: {parent_name} + {child_name} (current ID: {current_enquiry_id})")

print(f"\n" + "=" * 80)
print("UPDATE SUMMARY")
print("=" * 80)
print(f"Matched in Excel: {matched}")
print(f"Already correct: {already_correct}")
print(f"Updated: {updated}")
print(f"Not matched: {not_matched}")

# Show sample results
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            c.enquiry_id,
            c.first_name,
            p.name as parent_name
        FROM children c
        LEFT JOIN family_links fl ON c.id = fl.child_id AND c.center_id = fl.center_id AND fl.is_primary_contact = TRUE
        LEFT JOIN parents p ON fl.parent_id = p.id
        WHERE c.center_id = :center_id
        AND c.first_name IN ('Nihaal', 'Vihaan', 'Naina')
        ORDER BY c.first_name, p.name
    """), {"center_id": CENTER_ID})

    print("\nSample results (Nihaal, Vihaan, Naina):")
    for row in result:
        print(f"  {row[0]}: {row[1]} (parent: {row[2]})")

print("\n" + "=" * 80)
print("ENQUIRY ID FIX COMPLETE!")
print("=" * 80)
