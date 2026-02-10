"""
Import Expired sheet enrollments and attendance
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from datetime import datetime, date
from app.core.database import SessionLocal
from sqlalchemy import text

print("="*70, flush=True)
print("IMPORTING EXPIRED SHEET DATA", flush=True)
print("="*70, flush=True)

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3
EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

print("Database connected", flush=True)

# Load expired sheet
print("Reading Excel file...", flush=True)
expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
print(f"Loaded {len(expired_df)} expired records", flush=True)

# Get batches
print("Loading batches...", flush=True)
batches = {}
for r in db.execute(text("SELECT id, name FROM batches WHERE center_id = :cid"), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    batches[r.name] = r.id
print(f"Found {len(batches)} batches", flush=True)

def parse_date_correct_year(dt):
    """Parse date with correct year logic: Jan/Feb = 2026, rest = 2025"""
    if pd.isna(dt):
        return None
    if isinstance(dt, datetime):
        dt = dt.date()
    elif isinstance(dt, date):
        pass
    elif isinstance(dt, str):
        try:
            dt = datetime.strptime(dt.strip(), "%Y-%m-%d").date()
        except:
            return None
    else:
        return None

    # Apply year correction
    if dt.month in (1, 2):
        if dt.year != 2026:
            dt = dt.replace(year=2026)
    else:
        if dt.year != 2025:
            dt = dt.replace(year=2025)
    return dt

enrollments_created = 0
enrollments_found = 0
attendance_created = 0
children_not_found = 0
skipped = 0

print("Processing expired records...", flush=True)
for idx, row in expired_df.iterrows():
    if idx % 10 == 0:
        print(f"  Processing row {idx}...", flush=True)

    try:
        enquiry_id = str(row.get('Enquiry ID', '')).strip()
        if not enquiry_id or enquiry_id == 'nan':
            skipped += 1
            continue

        child_name = str(row.get('Child Name', '')).strip()
        batch_name = str(row.get('Batch', '')).strip()
        booked = int(row.get('Booked', 0)) if pd.notna(row.get('Booked')) else 0
        availed = int(row.get('Availed', 0)) if pd.notna(row.get('Availed')) else 0

        # Skip if no visits
        if booked == 0 and availed == 0:
            skipped += 1
            continue

        # Get batch
        batch_id = batches.get(batch_name)
        if not batch_id:
            skipped += 1
            continue

        # Find child
        child = db.execute(text("""
            SELECT id FROM children WHERE center_id = :cid AND enquiry_id = :eid
        """), {"cid": CHANDIGARH_CENTER_ID, "eid": enquiry_id}).fetchone()

        if not child:
            children_not_found += 1
            continue

        child_id = child.id

        # Check if enrollment exists for this child + batch
        enrollment = db.execute(text("""
            SELECT id, status, visits_included FROM enrollments
            WHERE child_id = :child AND batch_id = :bid AND is_archived = false
            ORDER BY created_at DESC LIMIT 1
        """), {"child": child_id, "bid": batch_id}).fetchone()

        if not enrollment:
            # Create expired enrollment
            result = db.execute(text("""
                INSERT INTO enrollments (center_id, child_id, batch_id, plan_type, status,
                    visits_included, visits_used, start_date,
                    created_by_id, updated_by_id, created_at, updated_at, is_archived)
                VALUES (:cid, :child, :bid, 'QUARTERLY', 'EXPIRED',
                    :booked, 0, '2025-04-01',
                    6, 6, NOW(), NOW(), false)
                RETURNING id
            """), {"cid": CHANDIGARH_CENTER_ID, "child": child_id, "bid": batch_id,
                   "booked": booked if booked > 0 else availed})
            enrollment_id = result.fetchone()[0]
            enrollments_created += 1
        else:
            enrollment_id = enrollment.id
            enrollments_found += 1

        # Import attendance from columns 1-54
        for i in range(1, 55):
            col_val = row.get(i) if i in row.index else row.get(str(i))
            if pd.isna(col_val):
                continue

            att_date = parse_date_correct_year(col_val)
            if not att_date:
                continue

            # Check if attendance already exists
            existing = db.execute(text("""
                SELECT a.id FROM attendance a
                JOIN class_sessions cs ON a.class_session_id = cs.id
                WHERE a.child_id = :child AND cs.batch_id = :bid AND cs.session_date = :dt
                AND a.is_archived = false
            """), {"child": child_id, "bid": batch_id, "dt": att_date}).fetchone()

            if existing:
                continue

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
                VALUES (:cid, :sid, :child, :eid, 'PRESENT', 6, NOW(), 'Expired enrollment', 6, 6, NOW(), NOW(), false)
            """), {"cid": CHANDIGARH_CENTER_ID, "sid": session_id, "child": child_id, "eid": enrollment_id})
            attendance_created += 1

            # Limit attendance records per enrollment to prevent hanging
            if attendance_created % 100 == 0:
                db.commit()
                print(f"    Committed {attendance_created} attendance records so far", flush=True)

    except Exception as e:
        print(f"  ERROR on row {idx} ({enquiry_id}): {str(e)}", flush=True)
        db.rollback()
        continue

    if idx % 20 == 0:
        db.commit()

db.commit()

print(f"\nResults:", flush=True)
print(f"  Enrollments created: {enrollments_created}", flush=True)
print(f"  Enrollments found: {enrollments_found}", flush=True)
print(f"  Attendance created: {attendance_created}", flush=True)
print(f"  Children not found: {children_not_found}", flush=True)
print(f"  Skipped: {skipped}", flush=True)

# Recalculate visits_used
print("\nRecalculating visits_used...", flush=True)
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT' AND a.is_archived = false
    ), 0)
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

# Verification
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

result = db.execute(text("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active,
        SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as expired
    FROM enrollments WHERE center_id = :cid AND is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()
print(f"\nEnrollments: {result.total} total ({result.active} active, {result.expired} expired)")

# Sample
print("\nSample - Abeer:")
for r in db.execute(text("""
    SELECT c.enquiry_id, b.name as batch, e.status, e.visits_used, e.visits_included,
           (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE enrollment_id = e.id) as paid
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = :cid AND c.first_name ILIKE '%abeer%'
    ORDER BY c.enquiry_id, e.status
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {r.enquiry_id} | {r.batch} | {r.status} | {r.visits_used}/{r.visits_included} | Paid: Rs.{r.paid}")

db.close()
print("\nDone!")
