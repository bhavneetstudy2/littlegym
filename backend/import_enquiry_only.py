"""
Import ONLY Enquiry sheet data - Step by step approach
"""
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import re

# Configuration
TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

engine = create_engine(TARGET_DB)
Session = sessionmaker(bind=engine)
db = Session()

# Get admin user
admin_user = db.execute(text("SELECT id FROM users WHERE center_id = :center_id LIMIT 1"), {"center_id": CENTER_ID}).scalar()
if not admin_user:
    admin_user = db.execute(text("SELECT id FROM users WHERE role = 'SUPER_ADMIN' LIMIT 1")).scalar()

print("=" * 80)
print("IMPORT ENQUIRY SHEET ONLY")
print("=" * 80)
print(f"Target Center ID: {CENTER_ID}")
print(f"Created by User ID: {admin_user}")

def clean_phone(phone):
    if pd.isna(phone):
        return None
    phone = str(phone).strip()
    phone = re.sub(r'[^\d+]', '', phone)
    if not phone:
        return None
    if not phone.startswith('+'):
        phone = '+91-' + phone.lstrip('91')
    return phone[:20] if phone else None

def parse_date(date_val):
    if pd.isna(date_val):
        return None
    if isinstance(date_val, (datetime, date)):
        return date_val if isinstance(date_val, date) else date_val.date()
    try:
        return pd.to_datetime(date_val, dayfirst=True).date()
    except:
        return None

def calculate_dob_from_age(age):
    if pd.isna(age):
        return None
    try:
        age_int = int(float(str(age).replace('+', '').replace('-', '').split()[0]))
        return date(date.today().year - age_int, 1, 1)
    except:
        return None

# Read Enquiry sheet
print("\nReading Enquiry sheet...")
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
print(f"Found {len(enquiry_df)} rows in Enquiry sheet")

# Stats
stats = {'children': 0, 'parents': 0, 'family_links': 0, 'leads': 0, 'errors': []}
next_id_num = 1

print("\nProcessing and importing...")
print("-" * 80)

for idx, row in enquiry_df.iterrows():
    try:
        # Get or generate Enquiry ID
        enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() else None

        if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
            # Generate new ID
            enquiry_id = f"TLGC-NEW-{next_id_num:04d}"
            next_id_num += 1

        # Get child data
        child_first_name = str(row['Child Name']).strip() if pd.notna(row['Child Name']) else None
        if not child_first_name:
            continue  # Skip if no child name

        child_last_name = str(row['Last Name']).strip() if pd.notna(row['Last Name']) else None
        parent_name = str(row['Parent Name']).strip() if pd.notna(row['Parent Name']) else 'Parent'
        contact_number = clean_phone(row['Contact Number'])
        email = str(row['Email']).strip() if pd.notna(row['Email']) and str(row['Email']).strip() != 'nan' else None

        # Parse age and DOB
        age = row.get('Age')
        dob = parse_date(row.get('Birthday'))
        if not dob and age:
            dob = calculate_dob_from_age(age)

        gender = str(row['Gender']).strip() if pd.notna(row['Gender']) else None
        if gender:
            gender = gender.lower()
            if gender in ['m', 'male', 'boy']:
                gender = 'Boy'
            elif gender in ['f', 'female', 'girl']:
                gender = 'Girl'
            else:
                gender = 'Other'

        school = str(row['School']).strip() if pd.notna(row['School']) and str(row['School']) != 'nan' else None
        remarks = str(row['Remarks']).strip() if pd.notna(row['Remarks']) and str(row['Remarks']) != 'nan' else None
        enquiry_date = parse_date(row.get('Enquiry Date'))

        # 1. Insert Child
        child_insert = text("""
            INSERT INTO children (center_id, first_name, last_name, dob, school, notes, external_id, is_archived, created_by_id, updated_by_id, created_at, updated_at)
            VALUES (:center_id, :first_name, :last_name, :dob, :school, :notes, :external_id, FALSE, :created_by_id, :updated_by_id, NOW(), NOW())
            RETURNING id
        """)

        child_id = db.execute(child_insert, {
            "center_id": CENTER_ID,
            "first_name": child_first_name[:100],
            "last_name": child_last_name[:100] if child_last_name else None,
            "dob": dob,
            "school": school[:255] if school else None,
            "notes": remarks[:1000] if remarks else None,
            "external_id": enquiry_id[:50],
            "created_by_id": admin_user,
            "updated_by_id": admin_user
        }).scalar()

        stats['children'] += 1

        # 2. Insert or get Parent
        parent_id = None
        if contact_number:
            # Check if parent exists
            existing_parent = db.execute(
                text("SELECT id FROM parents WHERE phone = :phone AND center_id = :center_id"),
                {"phone": contact_number, "center_id": CENTER_ID}
            ).scalar()

            if existing_parent:
                parent_id = existing_parent
            else:
                parent_insert = text("""
                    INSERT INTO parents (center_id, name, phone, email, is_archived, created_by_id, updated_by_id, created_at, updated_at)
                    VALUES (:center_id, :name, :phone, :email, FALSE, :created_by_id, :updated_by_id, NOW(), NOW())
                    RETURNING id
                """)

                parent_id = db.execute(parent_insert, {
                    "center_id": CENTER_ID,
                    "name": parent_name[:200],
                    "phone": contact_number,
                    "email": email[:255] if email else None,
                    "created_by_id": admin_user,
                    "updated_by_id": admin_user
                }).scalar()

                stats['parents'] += 1

        # 3. Create Family Link
        if parent_id:
            family_link_insert = text("""
                INSERT INTO family_links (center_id, child_id, parent_id, relationship_type, is_primary_contact, is_archived, created_by_id, updated_by_id, created_at, updated_at)
                VALUES (:center_id, :child_id, :parent_id, 'parent', TRUE, FALSE, :created_by_id, :updated_by_id, NOW(), NOW())
            """)

            db.execute(family_link_insert, {
                "center_id": CENTER_ID,
                "child_id": child_id,
                "parent_id": parent_id,
                "created_by_id": admin_user,
                "updated_by_id": admin_user
            })

            stats['family_links'] += 1

        # 4. Create Lead
        lead_insert = text("""
            INSERT INTO leads (center_id, child_id, status, source, discovery_notes, external_id, is_archived, created_by_id, updated_by_id, created_at, updated_at)
            VALUES (:center_id, :child_id, 'ENQUIRY_RECEIVED', 'WALK_IN', :discovery_notes, :external_id, FALSE, :created_by_id, :updated_by_id, :created_at, NOW())
        """)

        db.execute(lead_insert, {
            "center_id": CENTER_ID,
            "child_id": child_id,
            "discovery_notes": remarks[:1000] if remarks else None,
            "external_id": enquiry_id[:50],
            "created_by_id": admin_user,
            "updated_by_id": admin_user,
            "created_at": enquiry_date or datetime.now()
        })

        stats['leads'] += 1

        # Commit every 50 records
        if stats['children'] % 50 == 0:
            db.commit()
            print(f"  Progress: {stats['children']}/{len(enquiry_df)} children imported...")

    except Exception as e:
        error_msg = f"Row {idx}: {str(e)[:150]}"
        stats['errors'].append(error_msg)
        print(f"  ERROR: {error_msg}")
        db.rollback()
        continue

# Final commit
db.commit()
db.close()

# Summary
print("\n" + "=" * 80)
print("IMPORT SUMMARY")
print("=" * 80)
print(f"Children imported: {stats['children']}")
print(f"Parents created: {stats['parents']}")
print(f"Family links created: {stats['family_links']}")
print(f"Leads created: {stats['leads']}")
print(f"Errors: {len(stats['errors'])}")

if stats['errors']:
    print("\nFirst 10 errors:")
    for err in stats['errors'][:10]:
        print(f"  - {err}")

print("\n" + "=" * 80)
print("ENQUIRY SHEET IMPORT COMPLETE!")
print("=" * 80)
