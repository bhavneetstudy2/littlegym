"""
Create leads for all children that don't have them
Use Excel data to populate correct source
"""
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

SOURCE_MAP = {
    'Social Media': 'INSTAGRAM',
    'Referral': 'REFERRAL',
    'Walk-in': 'WALK_IN',
    'Website': 'ONLINE',
    'Other': 'OTHER'
}

print("=" * 80)
print("CREATE MISSING LEADS")
print("=" * 80)

# Read Excel
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
print(f"\nRead {len(enquiry_df)} rows from Enquiry sheet")

# Build mapping: enquiry_id -> source, remarks, enquiry_date
enquiry_data = {}
for idx, row in enquiry_df.iterrows():
    enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
        continue

    excel_source = row.get('Source')
    db_source = SOURCE_MAP.get(str(excel_source).strip(), 'WALK_IN') if pd.notna(excel_source) else 'WALK_IN'

    remarks = str(row.get('Remarks')).strip() if pd.notna(row.get('Remarks')) else None
    enquiry_date = row.get('Enquiry Date')
    if pd.notna(enquiry_date):
        try:
            enquiry_date = pd.to_datetime(enquiry_date).date()
        except:
            enquiry_date = None

    enquiry_data[enquiry_id] = {
        'source': db_source,
        'remarks': remarks,
        'enquiry_date': enquiry_date
    }

print(f"Loaded data for {len(enquiry_data)} enquiry IDs")

engine = create_engine(TARGET_DB)

# Get admin user
with engine.connect() as conn:
    admin_user = conn.execute(text("SELECT id FROM users WHERE center_id = :center_id LIMIT 1"), {"center_id": CENTER_ID}).scalar()
    if not admin_user:
        admin_user = conn.execute(text("SELECT id FROM users WHERE role = 'SUPER_ADMIN' LIMIT 1")).scalar()

print(f"Using user_id {admin_user} for created_by/updated_by")

created = 0
not_in_excel = 0

with engine.begin() as conn:
    # Get all children without leads
    result = conn.execute(text("""
        SELECT c.id, c.enquiry_id, c.notes
        FROM children c
        LEFT JOIN leads l ON c.id = l.child_id AND c.center_id = l.center_id
        WHERE c.center_id = :center_id AND l.id IS NULL
    """), {"center_id": CENTER_ID})

    children_without_leads = result.fetchall()
    print(f"\nFound {len(children_without_leads)} children without leads")

    for child in children_without_leads:
        child_id, enquiry_id, child_notes = child

        # Get data from Excel
        if enquiry_id in enquiry_data:
            source = enquiry_data[enquiry_id]['source']
            remarks = enquiry_data[enquiry_id]['remarks'] or child_notes
            enquiry_date = enquiry_data[enquiry_id]['enquiry_date']
        else:
            source = 'WALK_IN'
            remarks = child_notes
            enquiry_date = None
            not_in_excel += 1

        # Create lead
        conn.execute(text("""
            INSERT INTO leads (center_id, child_id, status, source, discovery_notes, external_id, is_archived, created_by_id, updated_by_id, created_at, updated_at)
            VALUES (:center_id, :child_id, 'ENQUIRY_RECEIVED', :source, :discovery_notes, :external_id, FALSE, :created_by_id, :updated_by_id, :created_at, NOW())
        """), {
            "center_id": CENTER_ID,
            "child_id": child_id,
            "source": source,
            "discovery_notes": remarks[:1000] if remarks else None,
            "external_id": enquiry_id,
            "created_by_id": admin_user,
            "updated_by_id": admin_user,
            "created_at": enquiry_date or datetime.now()
        })

        created += 1

        if created % 50 == 0:
            print(f"  Progress: {created}/{len(children_without_leads)} leads created...")

print("\n" + "=" * 80)
print("CREATE SUMMARY")
print("=" * 80)
print(f"Leads created: {created}")
print(f"Not found in Excel (used defaults): {not_in_excel}")

# Show final stats
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM leads WHERE center_id = :center_id"), {"center_id": CENTER_ID})
    print(f"\nTotal leads now: {result.scalar()}")

    result = conn.execute(text("""
        SELECT source, COUNT(*)
        FROM leads
        WHERE center_id = :center_id
        GROUP BY source
        ORDER BY COUNT(*) DESC
    """), {"center_id": CENTER_ID})

    print("\nLead source distribution:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

print("\n" + "=" * 80)
print("LEADS CREATION COMPLETE!")
print("=" * 80)
