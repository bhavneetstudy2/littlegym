"""
Clean up Shahbaz's attendance to match CSV exactly
"""
import sys
sys.path.insert(0, '.')
import csv
from datetime import datetime, date
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'

def parse_date_from_dd_mmm(date_str, year=2025):
    if not date_str or str(date_str).strip() == '':
        return None
    try:
        date_str = str(date_str).strip()
        dt = datetime.strptime(f"{date_str}-{year}", "%d-%b-%Y")
        # Dates Apr-Dec are 2025, Jan-Mar is 2026
        if dt.month >= 1 and dt.month <= 3:
            dt = dt.replace(year=2026)
        return dt.date()
    except:
        return None

# Get Shahbaz's CSV data
shahbaz_csv = {}
with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('Child Name', '').strip().lower()
        if 'shahbaz' in name:
            batch = row.get('Batch', '').strip()
            dates = []
            for i in range(1, 55):
                d = row.get(str(i), '').strip()
                if d:
                    parsed = parse_date_from_dd_mmm(d)
                    if parsed:
                        dates.append(parsed)
            shahbaz_csv[batch] = set(dates)
            print(f"CSV {batch}: {len(dates)} dates")
            print(f"  Dates: {sorted(dates)}")

# Get batch IDs
batches = {}
for r in db.execute(text("SELECT id, name FROM batches WHERE center_id = :cid"), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    batches[r.name] = r.id

# Get Shahbaz's child ID
shahbaz = db.execute(text("""
    SELECT id FROM children WHERE center_id = :cid AND first_name ILIKE '%shahbaz%'
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()
child_id = shahbaz.id
print(f"\nShahbaz child_id: {child_id}")

# Delete all existing Shahbaz attendance and recreate from CSV
print("\nArchiving all existing Shahbaz attendance...")
db.execute(text("""
    UPDATE attendance SET is_archived = true
    WHERE child_id = :child AND is_archived = false
"""), {"child": child_id})
db.commit()

# Get enrollments for Shahbaz
enrollments = {}
for r in db.execute(text("""
    SELECT e.id, b.name as batch_name, b.id as batch_id
    FROM enrollments e
    JOIN batches b ON e.batch_id = b.id
    WHERE e.child_id = :child AND e.is_archived = false
"""), {"child": child_id}).fetchall():
    enrollments[r.batch_name] = {"enrollment_id": r.id, "batch_id": r.batch_id}

print(f"Enrollments: {list(enrollments.keys())}")

# Create attendance from CSV
created = 0
for batch_name, dates in shahbaz_csv.items():
    if batch_name not in enrollments:
        print(f"Warning: No enrollment for batch {batch_name}")
        continue

    enr = enrollments[batch_name]
    batch_id = enr["batch_id"]
    enrollment_id = enr["enrollment_id"]

    for att_date in dates:
        # Find or create session
        session = db.execute(text("""
            SELECT id FROM class_sessions
            WHERE center_id = :cid AND batch_id = :bid AND session_date = :dt
        """), {"cid": CHANDIGARH_CENTER_ID, "bid": batch_id, "dt": att_date}).fetchone()

        if not session:
            result = db.execute(text("""
                INSERT INTO class_sessions (center_id, batch_id, session_date, status,
                    created_by_id, updated_by_id, created_at, updated_at, is_archived)
                VALUES (:cid, :bid, :dt, 'COMPLETED', 6, 6, NOW(), NOW(), false)
                RETURNING id
            """), {"cid": CHANDIGARH_CENTER_ID, "bid": batch_id, "dt": att_date})
            session_id = result.fetchone()[0]
        else:
            session_id = session.id

        # Create attendance
        db.execute(text("""
            INSERT INTO attendance (center_id, class_session_id, child_id, enrollment_id, status,
                marked_by_user_id, marked_at, notes, created_by_id, updated_by_id, created_at, updated_at, is_archived)
            VALUES (:cid, :sid, :child, :eid, 'PRESENT', 6, NOW(), 'Imported', 6, 6, NOW(), NOW(), false)
        """), {"cid": CHANDIGARH_CENTER_ID, "sid": session_id, "child": child_id, "eid": enrollment_id})
        created += 1

db.commit()
print(f"\nCreated {created} attendance records")

# Recalculate visits_used for Shahbaz
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT' AND a.is_archived = false
    ), 0)
    WHERE e.child_id = :child AND e.is_archived = false
"""), {"child": child_id})
db.commit()

# Verify
print("\nVerification:")
for r in db.execute(text("""
    SELECT c.id, c.first_name, c.enquiry_id,
           e.id as enr_id, b.name as batch, e.visits_used, e.visits_included, e.status
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.id = :child
"""), {"child": child_id}).fetchall():
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} | {r.status}")

db.close()
print("\nDone!")
