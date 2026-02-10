"""
Search for Mehraab in Excel and database
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("SEARCHING FOR MEHRAAB")
print("="*70)

# Search in Excel - Enrolled sheet
print("\nSearching in Excel - Enrolled sheet:")
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
mehraab_enrolled = enrolled_df[enrolled_df['Child Name'].str.contains('mehraab', case=False, na=False)]

if len(mehraab_enrolled) > 0:
    print(f"Found {len(mehraab_enrolled)} records:")
    for idx, row in mehraab_enrolled.iterrows():
        print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')} | {row.get('Booked Classes')} classes")
else:
    print("  NOT FOUND in Enrolled sheet")

# Search in Excel - Expired sheet
print("\nSearching in Excel - Expired sheet:")
try:
    expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
    mehraab_expired = expired_df[expired_df['Child Name'].str.contains('mehraab', case=False, na=False)]

    if len(mehraab_expired) > 0:
        print(f"Found {len(mehraab_expired)} records:")
        for idx, row in mehraab_expired.iterrows():
            print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')} | {row.get('Booked')} booked")
    else:
        print("  NOT FOUND in Expired sheet")
except Exception as e:
    print(f"  Error reading Expired sheet: {e}")

# Search in database
print("\nSearching in database:")
db = SessionLocal()

mehraab_db = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name, c.last_name,
           (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enrollment_count
    FROM children c
    WHERE (c.first_name ILIKE '%mehraab%' OR c.last_name ILIKE '%mehraab%')
      AND c.center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

if len(mehraab_db) > 0:
    print(f"Found {len(mehraab_db)} records:")
    for r in mehraab_db:
        full_name = f"{r.first_name} {r.last_name}".strip()
        print(f"  {r.enquiry_id} | {full_name} | {r.enrollment_count} enrollments")

        # Show enrollments
        enrollments = db.execute(text("""
            SELECT b.name as batch, e.visits_used, e.visits_included, e.status
            FROM enrollments e
            JOIN batches b ON e.batch_id = b.id
            WHERE e.child_id = :cid AND e.is_archived = false
        """), {"cid": r.id}).fetchall()

        for e in enrollments:
            print(f"    - {e.batch}: {e.visits_used}/{e.visits_included} ({e.status})")
else:
    print("  NOT FOUND in database")

# Search for similar names
print("\n" + "="*70)
print("Searching for similar names (Meher, Mehar, etc.):")
print("="*70)

similar = db.execute(text("""
    SELECT c.enquiry_id, c.first_name, c.last_name
    FROM children c
    WHERE (c.first_name ILIKE 'meh%' OR c.first_name ILIKE 'mir%')
      AND c.center_id = :cid
    ORDER BY c.enquiry_id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

if len(similar) > 0:
    print(f"\nFound {len(similar)} children with similar names:")
    for r in similar:
        full_name = f"{r.first_name} {r.last_name}".strip()
        print(f"  {r.enquiry_id} | {full_name}")
else:
    print("  No similar names found")

# Check all sheets in Excel
print("\n" + "="*70)
print("Checking all sheets in Excel file:")
print("="*70)

xls = pd.ExcelFile(EXCEL_FILE)
print(f"\nAvailable sheets: {xls.sheet_names}")

for sheet_name in xls.sheet_names:
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)

        # Try to find Child Name or similar column
        name_col = None
        for col in df.columns:
            if 'name' in col.lower() or 'child' in col.lower():
                name_col = col
                break

        if name_col:
            mehraab_found = df[df[name_col].astype(str).str.contains('mehraab', case=False, na=False)]
            if len(mehraab_found) > 0:
                print(f"\n  Found in '{sheet_name}' sheet ({len(mehraab_found)} records):")
                for idx, row in mehraab_found.iterrows():
                    print(f"    Row {idx}: {row.get(name_col)}")
    except Exception as e:
        print(f"  Error reading sheet '{sheet_name}': {e}")

db.close()
print("\n" + "="*70)
