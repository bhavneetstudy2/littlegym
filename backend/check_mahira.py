"""
Check Mahira's enrollment data
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check Mahira's enrollments
result = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.start_date, e.end_date, e.visits_included, e.visits_used,
           e.plan_type, e.status, e.created_at
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.first_name ILIKE '%mahira%' AND c.center_id = 3 AND e.is_archived = false
    ORDER BY e.created_at
""")).fetchall()

print("Mahira's enrollments:")
for r in result:
    print(f"  ID:{r.id} | {r.enquiry_id} | {r.batch} | {r.start_date} to {r.end_date}")
    print(f"    {r.plan_type} | {r.visits_used}/{r.visits_included} | Created: {r.created_at}")

# Check Excel data for Mahira
print("\nChecking Excel data for TLGC0002...")
import pandas as pd
EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
mahira_rows = enrolled_df[enrolled_df['Enquiry ID'] == 'TLGC0002']
for idx, row in mahira_rows.iterrows():
    print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')}")
    print(f"    Booked: {row.get('Booked Classes')} | Date: {row.get('Date')} | Duration: {row.get('Duration')}")

print("\nChecking Excel data for TLGC0405...")
tlgc0405_rows = enrolled_df[enrolled_df['Enquiry ID'] == 'TLGC0405']
for idx, row in tlgc0405_rows.iterrows():
    print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')}")
    print(f"    Booked: {row.get('Booked Classes')} | Date: {row.get('Date')} | Duration: {row.get('Duration')}")

db.close()
