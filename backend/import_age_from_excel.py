"""
Import age values from Excel Age column
"""
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3

print("=" * 80)
print("IMPORT AGE FROM EXCEL")
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

        # Get age from Excel
        age = row.get('Age')
        if pd.isna(age):
            continue

        try:
            # Parse age - handle cases like "3+", "4-5", etc
            age_str = str(age).strip().replace('+', '').replace('-', '').split()[0]
            age_int = int(float(age_str))
        except:
            continue

        # Update child in database
        result = conn.execute(text("""
            UPDATE children
            SET age_years = :age
            WHERE center_id = :center_id
            AND enquiry_id = :enquiry_id
        """), {
            "age": age_int,
            "center_id": CENTER_ID,
            "enquiry_id": enquiry_id
        })

        if result.rowcount > 0:
            updated += 1
            if updated <= 10:  # Show first 10 updates
                print(f"  Updated {enquiry_id}: age = {age_int}")
        else:
            not_found += 1

print(f"\n" + "=" * 80)
print("UPDATE SUMMARY")
print("=" * 80)
print(f"Ages updated: {updated}")
print(f"Not found: {not_found}")

# Show sample
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT enquiry_id, first_name, age_years, dob
        FROM children
        WHERE center_id = :center_id
        AND age_years IS NOT NULL
        ORDER BY id
        LIMIT 10
    """), {"center_id": CENTER_ID})

    print("\nSample children with age:")
    for row in result:
        print(f"  {row[0]}: {row[1]}, age={row[2]}, dob={row[3]}")

print("\n" + "=" * 80)
print("AGE IMPORT COMPLETE!")
print("=" * 80)
