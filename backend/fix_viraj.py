"""
Fix Viraj's data:
1. Fix enquiry_id: TLGC0434 belongs to Viraj (child 324), not Aviraj (child 312)
2. Fix Aviraj's enquiry_id: should be TLGC0084
3. Update parent info for Viraj to Vaishali
4. Import missing 13 attendance records from CSV
5. Update visits_used
"""
import sys
sys.path.insert(0, ".")
import csv
from datetime import datetime
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

CHANDIGARH_CENTER_ID = 3
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'

# Step 1: Fix enquiry_id assignments
print("=" * 60)
print("Step 1: Fix enquiry_id assignments")
print("=" * 60)

# Remove TLGC0434 from Aviraj (child 312) - it's the wrong child
aviraj_312 = db.execute(text("SELECT id, first_name, enquiry_id FROM children WHERE id = 312")).fetchone()
print(f"  Aviraj (312): enquiry_id={aviraj_312.enquiry_id}")

# Set correct enquiry_id TLGC0084 on Aviraj 312 (Sakshi's daughter)
db.execute(text("UPDATE children SET enquiry_id = 'TLGC0084' WHERE id = 312"))
print(f"  -> Set Aviraj (312) enquiry_id = TLGC0084")

# Set TLGC0434 on Viraj (child 324)
db.execute(text("UPDATE children SET enquiry_id = 'TLGC0434' WHERE id = 324"))
print(f"  -> Set Viraj (324) enquiry_id = TLGC0434")

# Also set TLGC0096 on the other Viraj entry if there's no enquiry_id conflict
# Actually child 324 is the enquiry TLGC0096 Viraj, but since they enrolled as TLGC0434,
# we use the enrolled enquiry_id. The TLGC0096 was just the first discovery visit.

# Step 2: Update parent info
print("\n" + "=" * 60)
print("Step 2: Update parent info for Viraj")
print("=" * 60)

# Get current parent
parent_info = db.execute(text("""
    SELECT p.id, p.name, p.phone FROM parents p
    JOIN family_links fl ON fl.parent_id = p.id
    WHERE fl.child_id = 324
""")).fetchone()

print(f"  Current parent: {parent_info.name}, phone={parent_info.phone}")

# Update parent name and phone
db.execute(text("""
    UPDATE parents SET name = 'Vaishali', phone = '+91-8168410537'
    WHERE id = :pid
"""), {"pid": parent_info.id})
print(f"  -> Updated to: Vaishali, phone=+91-8168410537")

# Step 3: Import missing attendance records
print("\n" + "=" * 60)
print("Step 3: Import missing attendance records for Viraj")
print("=" * 60)

VIRAJ_CHILD_ID = 324

# Read attendance CSV to get Viraj's dates
viraj_dates = []
with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('Enquiry ID', '').strip() == 'TLGC0434':
            for i in range(1, 55):
                date_str = row.get(str(i), '').strip()
                if date_str:
                    try:
                        dt = datetime.strptime(f"{date_str}-2024", "%d-%b-%Y")
                        # Dates after August are likely 2025 based on enrollment start date 2025-08-24
                        if dt.month >= 8:
                            dt = dt.replace(year=2025)
                        else:
                            dt = dt.replace(year=2025)  # All dates are 2025 since enrollment started Aug 2025
                        viraj_dates.append(dt.date())
                    except:
                        print(f"  ! Could not parse date: {date_str}")
            break

print(f"  Found {len(viraj_dates)} attendance dates: {viraj_dates}")

# Get Viraj's enrollment
enrollment = db.execute(text("""
    SELECT id, batch_id FROM enrollments
    WHERE child_id = :cid AND is_archived = false
    ORDER BY id LIMIT 1
"""), {"cid": VIRAJ_CHILD_ID}).fetchone()

print(f"  Enrollment: #{enrollment.id}, batch_id={enrollment.batch_id}")

# Get batch info
batch = db.execute(text("SELECT id, start_time, end_time FROM batches WHERE id = :bid"), {"bid": enrollment.batch_id}).fetchone()

attendance_created = 0
sessions_created = 0

for att_date in viraj_dates:
    # Find or create class session
    session = db.execute(text("""
        SELECT id FROM class_sessions
        WHERE center_id = :cid AND batch_id = :bid AND session_date = :dt
    """), {"cid": CHANDIGARH_CENTER_ID, "bid": enrollment.batch_id, "dt": att_date}).fetchone()

    if not session:
        result = db.execute(text("""
            INSERT INTO class_sessions (center_id, batch_id, session_date, start_time, end_time,
                trainer_user_id, status, created_by_id, updated_by_id, created_at, updated_at, is_archived)
            VALUES (:cid, :bid, :dt, :st, :et, 6, 'COMPLETED', 6, 6, NOW(), NOW(), false)
            RETURNING id
        """), {
            "cid": CHANDIGARH_CENTER_ID,
            "bid": enrollment.batch_id,
            "dt": att_date,
            "st": batch.start_time,
            "et": batch.end_time
        })
        session_id = result.fetchone()[0]
        sessions_created += 1
    else:
        session_id = session.id

    # Check if attendance already exists
    existing = db.execute(text("""
        SELECT id FROM attendance
        WHERE child_id = :child AND class_session_id = :sid
    """), {"child": VIRAJ_CHILD_ID, "sid": session_id}).fetchone()

    if existing:
        print(f"  Already exists: {att_date}")
        continue

    # Create attendance record
    db.execute(text("""
        INSERT INTO attendance (center_id, class_session_id, child_id, enrollment_id, status,
            marked_by_user_id, marked_at, notes, created_by_id, updated_by_id, created_at, updated_at, is_archived)
        VALUES (:cid, :sid, :child, :eid, 'PRESENT', 6, NOW(), 'Imported from CSV', 6, 6, NOW(), NOW(), false)
    """), {
        "cid": CHANDIGARH_CENTER_ID,
        "sid": session_id,
        "child": VIRAJ_CHILD_ID,
        "eid": enrollment.id
    })
    attendance_created += 1
    print(f"  Created attendance: {att_date}")

# Step 4: Update visits_used
print("\n" + "=" * 60)
print("Step 4: Update visits_used")
print("=" * 60)

actual_count = db.execute(text("""
    SELECT COUNT(*) FROM attendance
    WHERE child_id = :cid AND status = 'PRESENT' AND is_archived = false
"""), {"cid": VIRAJ_CHILD_ID}).scalar()

db.execute(text("""
    UPDATE enrollments SET visits_used = :used WHERE id = :eid
"""), {"used": actual_count, "eid": enrollment.id})

print(f"  Enrollment #{enrollment.id}: visits_used set to {actual_count}")

db.commit()
print(f"\nDone! Created {sessions_created} sessions, {attendance_created} attendance records.")
db.close()
