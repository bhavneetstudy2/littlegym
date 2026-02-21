"""
Fix lead sources - update from Excel data instead of hardcoded WALK_IN
"""
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

# Source mapping: Excel → Database ENUM
SOURCE_MAP = {
    'Social Media': 'INSTAGRAM',
    'Referral': 'REFERRAL',
    'Walk-in': 'WALK_IN',
    'Website': 'ONLINE',
    'Other': 'OTHER'
}

print("=" * 80)
print("FIX LEAD SOURCES FROM EXCEL")
print("=" * 80)

# Read Excel
enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
print(f"\nRead {len(enquiry_df)} rows from Enquiry sheet")

engine = create_engine(TARGET_DB)

updated = 0
not_found = 0

with engine.begin() as conn:
    for idx, row in enquiry_df.iterrows():
        # Get enquiry_id from first column
        enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None

        if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
            continue

        # Get source from Excel
        excel_source = row.get('Source')
        if pd.isna(excel_source):
            db_source = 'WALK_IN'  # default
        else:
            excel_source = str(excel_source).strip()
            db_source = SOURCE_MAP.get(excel_source, 'WALK_IN')

        # Update lead in database
        result = conn.execute(text("""
            UPDATE leads
            SET source = :source
            WHERE center_id = :center_id
            AND external_id = :enquiry_id
        """), {
            "source": db_source,
            "center_id": CENTER_ID,
            "enquiry_id": enquiry_id
        })

        if result.rowcount > 0:
            updated += 1
            if updated <= 5:  # Show first 5 updates
                print(f"  Updated {enquiry_id}: {excel_source} -> {db_source}")
        else:
            not_found += 1

print(f"\n" + "=" * 80)
print("UPDATE SUMMARY")
print("=" * 80)
print(f"Leads updated: {updated}")
print(f"Not found: {not_found}")

# Show source distribution
with engine.connect() as conn:
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
print("SOURCE FIX COMPLETE!")
print("=" * 80)
