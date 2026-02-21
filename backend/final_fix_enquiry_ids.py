"""
Final fix for all enquiry IDs - clear all wrong ones first, then update correct ones
"""
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

print("=" * 80)
print("FINAL FIX: MATCH ALL ENQUIRY IDs TO EXCEL")
print("=" * 80)

# Build Excel mapping: enquiry_id -> (parent, child)
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')

# First, build the correct mapping from Excel
excel_id_to_key = {}  # enquiry_id -> (parent_name, child_name)
key_to_excel_id = {}  # (parent_name, child_name) -> enquiry_id

for idx, row in enquiry_df.iterrows():
    enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
    child_name = str(row.get('Child Name')).strip() if pd.notna(row.get('Child Name')) else None
    parent_name = str(row.get('Parent Name')).strip() if pd.notna(row.get('Parent Name')) else None

    if enquiry_id and child_name and enquiry_id != 'nan' and child_name != 'nan':
        if not parent_name or parent_name == 'nan':
            parent_name = 'Unknown'

        key = (parent_name.lower(), child_name.lower())

        if key not in key_to_excel_id:
            key_to_excel_id[key] = enquiry_id
            excel_id_to_key[enquiry_id] = key

print(f"Loaded {len(key_to_excel_id)} parent+child combinations from Excel")

engine = create_engine(TARGET_DB)

# Get all children with their enquiry_ids
children_to_clear = []
children_to_update = []

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            c.id,
            c.enquiry_id,
            c.first_name,
            COALESCE(p.name, 'Unknown') as parent_name
        FROM children c
        LEFT JOIN family_links fl ON c.id = fl.child_id AND c.center_id = fl.center_id AND fl.is_primary_contact = TRUE
        LEFT JOIN parents p ON fl.parent_id = p.id
        WHERE c.center_id = :center_id
    """), {"center_id": CENTER_ID})

    for row in result:
        child_id, db_enquiry_id, child_name, parent_name = row
        key = (parent_name.lower(), child_name.lower())

        # Check if this child's enquiry_id is correct
        if db_enquiry_id:
            # Does this enquiry_id belong to this parent+child according to Excel?
            if db_enquiry_id in excel_id_to_key:
                expected_key = excel_id_to_key[db_enquiry_id]
                if expected_key != key:
                    # Wrong ID! This child has an enquiry_id that belongs to someone else
                    children_to_clear.append((child_id, child_name, parent_name, db_enquiry_id))

        # Does this child need the correct enquiry_id?
        if key in key_to_excel_id:
            correct_id = key_to_excel_id[key]
            if db_enquiry_id != correct_id:
                children_to_update.append((child_id, child_name, parent_name, correct_id))

print(f"\nFound {len(children_to_clear)} children with WRONG enquiry IDs (will clear)")
print(f"Found {len(children_to_update)} children that need CORRECT enquiry IDs (will update)")

# Step 1: Clear all wrong IDs
if children_to_clear:
    print("\nClearing wrong enquiry IDs...")
    with engine.begin() as conn:
        for child_id, child_name, parent_name, old_id in children_to_clear:
            conn.execute(text("UPDATE children SET enquiry_id = NULL WHERE id = :id"), {"id": child_id})
            print(f"  Cleared: {parent_name} + {child_name} (had {old_id})")

# Step 2: Update all children with correct IDs
if children_to_update:
    print("\nUpdating with correct enquiry IDs...")
    with engine.begin() as conn:
        for child_id, child_name, parent_name, correct_id in children_to_update:
            conn.execute(text("UPDATE children SET enquiry_id = :id WHERE id = :child_id"),
                        {"id": correct_id, "child_id": child_id})
            print(f"  Updated: {parent_name} + {child_name} -> {correct_id}")

print("\n" + "=" * 80)
print("ALL ENQUIRY IDs FIXED!")
print("=" * 80)
