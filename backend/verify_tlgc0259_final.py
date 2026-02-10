"""
Final verification of TLGC0259 data
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FINAL VERIFICATION - TLGC0259 (Mehr)")
print("="*70)

db = SessionLocal()

# Database data
print("\nDATABASE:")
print("-" * 70)

child = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name,
           p.name as parent_name, p.phone
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE c.enquiry_id = 'TLGC0259' AND c.center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"Child: {child.first_name}")
print(f"Enquiry ID: {child.enquiry_id}")
print(f"Parent: {child.parent_name} ({child.phone})")

# Enrollment
enrollment = db.execute(text("""
    SELECT e.id, b.name as batch, e.visits_used, e.visits_included,
           e.start_date, e.end_date, e.status
    FROM enrollments e
    JOIN batches b ON e.batch_id = b.id
    WHERE e.child_id = :cid AND e.is_archived = false
"""), {"cid": child.id}).fetchone()

print(f"\nEnrollment:")
print(f"  Batch: {enrollment.batch}")
print(f"  Classes: {enrollment.visits_used}/{enrollment.visits_included}")
print(f"  Period: {enrollment.start_date} to {enrollment.end_date}")
print(f"  Status: {enrollment.status}")

# Attendance
attendance = db.execute(text("""
    SELECT cs.session_date, b.name as batch, a.status, a.id
    FROM attendance a
    JOIN class_sessions cs ON a.class_session_id = cs.id
    JOIN batches b ON cs.batch_id = b.id
    WHERE a.child_id = :cid AND a.is_archived = false
    ORDER BY cs.session_date
"""), {"cid": child.id}).fetchall()

print(f"\nAttendance ({len(attendance)} records):")
for att in attendance:
    print(f"  {att.session_date} | {att.batch} | {att.status} (ID: {att.id})")

# Excel data
print("\n" + "="*70)
print("EXCEL:")
print("-" * 70)

# Attendance sheet
attendance_df = pd.read_excel(EXCEL_FILE, sheet_name='Attendance')
tlgc0259_att = attendance_df[attendance_df.iloc[:, 0] == 'TLGC0259']

if len(tlgc0259_att) > 0:
    row = tlgc0259_att.iloc[0]
    print(f"Child: {row.iloc[1]}")
    print(f"Batch: {row.iloc[2]}")
    print(f"Booked: {row.iloc[3]}")
    print(f"Attended: {row.iloc[4]}")

    # Get attendance dates
    attendance_dates = []
    for col_idx in range(5, len(row)):
        if pd.notna(row.iloc[col_idx]):
            val = row.iloc[col_idx]
            # Skip if it's just a number (like the "16" at the start)
            if isinstance(val, (pd.Timestamp, str)) or (isinstance(val, int) and val > 100):
                attendance_dates.append(val)

    print(f"\nAttendance dates ({len(attendance_dates)}):")
    for date in attendance_dates:
        print(f"  {date}")

# Enrolled sheet
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
tlgc0259_enr = enrolled_df[enrolled_df['Enquiry ID'] == 'TLGC0259']

if len(tlgc0259_enr) > 0:
    print(f"\nEnrolled sheet data:")
    for idx, row in tlgc0259_enr.iterrows():
        print(f"  Date: {row.get('Date')}")
        print(f"  Batch: {row.get('Batch')}")
        print(f"  Booked: {row.get('Booked Classes')}")
        print(f"  Duration: {row.get('Duration')}")

db.close()

print("\n" + "="*70)
print("COMPARISON:")
print("="*70)
print(f"Excel shows: 8 classes attended")
print(f"Database shows: {len(attendance)} attendance records")
if len(attendance) == 8:
    print("✓ MATCH!")
elif len(attendance) == 9:
    print("⚠ One extra record - need to check which one is incorrect")
print("="*70)
