"""
Investigate TLGC0259 (Mehr) attendance discrepancy
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from sqlalchemy import text

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("INVESTIGATING TLGC0259 (Mehr) ATTENDANCE")
print("="*70)

db = SessionLocal()

# 1. Check current database state for child 487 (Mehr with TLGC0259)
print("\n1. DATABASE - Child 487 (Mehr, TLGC0259):")
print("-" * 70)

child_info = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name,
           p.name as parent_name, p.phone
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE c.id = 487 AND c.center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

if child_info:
    print(f"Child ID: {child_info.id}")
    print(f"Enquiry ID: {child_info.enquiry_id}")
    print(f"Name: {child_info.first_name}")
    print(f"Parent: {child_info.parent_name} ({child_info.phone})")

    # Check enrollments
    enrollments = db.execute(text("""
        SELECT e.id, b.name as batch, e.visits_used, e.visits_included,
               e.start_date, e.end_date, e.status
        FROM enrollments e
        JOIN batches b ON e.batch_id = b.id
        WHERE e.child_id = :cid AND e.is_archived = false
    """), {"cid": 487}).fetchall()

    print(f"\nEnrollments ({len(enrollments)}):")
    for e in enrollments:
        print(f"  ID {e.id}: {e.batch} | {e.visits_used}/{e.visits_included} | {e.status}")
        print(f"    Period: {e.start_date} to {e.end_date}")

    # Check attendance
    attendance = db.execute(text("""
        SELECT cs.session_date, b.name as batch, a.status, a.id as att_id
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN batches b ON cs.batch_id = b.id
        WHERE a.child_id = :cid AND a.is_archived = false
        ORDER BY cs.session_date
    """), {"cid": 487}).fetchall()

    print(f"\nAttendance records ({len(attendance)}):")
    for att in attendance:
        print(f"  {att.session_date} | {att.batch} | {att.status} (ID: {att.att_id})")

# 2. Check if attendance exists for child 403 (old Mehraab who had TLGC0259)
print("\n2. DATABASE - Child 403 (Mehraab, previously had TLGC0259):")
print("-" * 70)

child_403 = db.execute(text("""
    SELECT c.id, c.enquiry_id, c.first_name,
           p.name as parent_name
    FROM children c
    LEFT JOIN family_links fl ON c.id = fl.child_id AND fl.is_primary_contact = true
    LEFT JOIN parents p ON fl.parent_id = p.id
    WHERE c.id = 403 AND c.center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

if child_403:
    print(f"Child ID: {child_403.id}")
    print(f"Enquiry ID: {child_403.enquiry_id or '[NO ID]'}")
    print(f"Name: {child_403.first_name}")
    print(f"Parent: {child_403.parent_name}")

    # Check attendance for child 403
    attendance_403 = db.execute(text("""
        SELECT cs.session_date, b.name as batch, a.status
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN batches b ON cs.batch_id = b.id
        WHERE a.child_id = :cid AND a.is_archived = false
        ORDER BY cs.session_date
    """), {"cid": 403}).fetchall()

    print(f"\nAttendance records ({len(attendance_403)}):")
    for att in attendance_403:
        print(f"  {att.session_date} | {att.batch} | {att.status}")

# 3. Check Excel Attendance sheet for TLGC0259
print("\n3. EXCEL ATTENDANCE SHEET - TLGC0259:")
print("-" * 70)

attendance_df = pd.read_excel(EXCEL_FILE, sheet_name='Attendance')

# Find TLGC0259 in attendance
tlgc0259_rows = attendance_df[attendance_df.iloc[:, 0] == 'TLGC0259']

if len(tlgc0259_rows) > 0:
    print(f"Found {len(tlgc0259_rows)} row(s) for TLGC0259 in Attendance sheet")

    for idx, row in tlgc0259_rows.iterrows():
        print(f"\nRow {idx}:")
        print(f"  Enquiry ID: {row.iloc[0]}")
        print(f"  Child Name: {row.iloc[1]}")
        print(f"  Batch: {row.iloc[2]}")
        print(f"  Booked: {row.iloc[3]}")
        print(f"  Attended: {row.iloc[4]}")

        # Count attendance dates (columns after the first few metadata columns)
        attendance_dates = []
        for col_idx in range(5, len(row)):
            if pd.notna(row.iloc[col_idx]):
                attendance_dates.append(row.iloc[col_idx])

        print(f"  Attendance dates ({len(attendance_dates)}):")
        for date in attendance_dates[:10]:  # Show first 10
            print(f"    {date}")
        if len(attendance_dates) > 10:
            print(f"    ... and {len(attendance_dates) - 10} more")
else:
    print("NOT FOUND in Attendance sheet!")

# 4. Check if there are attendance records without proper child linking
print("\n4. ORPHANED ATTENDANCE (not linked to child 487):")
print("-" * 70)

# Check if there's attendance for TLGC0259 as a text search
orphaned = db.execute(text("""
    SELECT a.id, cs.session_date, b.name as batch, c.id as child_id,
           c.enquiry_id, c.first_name
    FROM attendance a
    JOIN class_sessions cs ON a.class_session_id = cs.id
    JOIN batches b ON cs.batch_id = b.id
    LEFT JOIN children c ON a.child_id = c.id
    WHERE a.center_id = :cid AND a.is_archived = false
      AND cs.session_date >= '2025-06-01'
      AND cs.session_date <= '2025-08-31'
      AND b.name = 'Good Friends'
    ORDER BY cs.session_date
    LIMIT 50
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nGood Friends attendance Jun-Aug 2025 ({len(orphaned)} records):")
for att in orphaned[:15]:
    print(f"  {att.session_date} | Child {att.child_id}: {att.enquiry_id or '[NO ID]'} | {att.first_name}")

db.close()
print("\n" + "="*70)
print("ANALYSIS NEEDED: Where did the 8 attendance records go?")
print("="*70)
