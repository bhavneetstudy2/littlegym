"""
Full reimport - properly sync database with Excel Enrolled sheet and Attendance CSV.
This will:
1. Update/create children with correct enquiry_id
2. Update enrollments with correct batch, visits_included, payment data
3. Import attendance from CSV
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
import csv
from datetime import datetime, date
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

CHANDIGARH_CENTER_ID = 3
EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'

def parse_date_from_dd_mmm(date_str, year=2025):
    if not date_str or pd.isna(date_str) or str(date_str).strip() == '':
        return None
    try:
        date_str = str(date_str).strip()
        dt = datetime.strptime(f"{date_str}-{year}", "%d-%b-%Y")
        # Dates Apr-Dec are 2025, Jan onwards is 2026
        if dt.month >= 1 and dt.month <= 3:
            dt = dt.replace(year=2026)
        return dt.date()
    except:
        return None

def normalize_phone(phone):
    if not phone:
        return None
    phone = str(phone).strip()
    if '/' in phone:
        phone = phone.split('/')[0].strip()
    phone = phone.replace(' ', '').replace('-', '')
    if phone.startswith('91') and len(phone) > 10:
        phone = phone[2:]
    if len(phone) == 10:
        return f"+91-{phone}"
    return f"+91-{phone}"

# Load Excel enrolled data
print("="*70)
print("Loading Excel Enrolled data...")
print("="*70)
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
print(f"Loaded {len(enrolled_df)} enrolled records")

# Load attendance CSV
print("\nLoading Attendance CSV...")
attendance_data = {}
with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        enquiry_id = row.get('Enquiry ID', '').strip()
        if not enquiry_id:
            continue
        dates = []
        for i in range(1, 55):
            d = row.get(str(i), '').strip()
            if d:
                parsed = parse_date_from_dd_mmm(d, year=2025)
                if parsed:
                    dates.append(parsed)
        attendance_data[enquiry_id] = {
            'child_name': row.get('Child Name', '').strip(),
            'batch': row.get('Batch', '').strip(),
            'dates': dates
        }
print(f"Loaded {len(attendance_data)} attendance records")

# Get batches
batches = {}
for r in db.execute(text("SELECT id, name FROM batches WHERE center_id = :cid"), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    batches[r.name] = r.id
print(f"Batches: {list(batches.keys())}")

# Process each enrolled record
print("\n" + "="*70)
print("Processing enrolled records...")
print("="*70)

updated = 0
errors = 0

for _, row in enrolled_df.iterrows():
    enquiry_id = str(row.get('Enquiry ID', '')).strip()
    if not enquiry_id or enquiry_id == 'nan':
        continue

    child_name = str(row.get('Child Name', '')).strip()
    batch_name = str(row.get('Batch', '')).strip()
    booked = int(row.get('Booked Classes', 24)) if pd.notna(row.get('Booked Classes')) else 24
    total_amount = float(row.get('Total Amount', 0)) if pd.notna(row.get('Total Amount')) else 0
    paid_amount = float(row.get('Paid Amount', 0)) if pd.notna(row.get('Paid Amount')) else 0
    duration = str(row.get('Duration', '')).strip() if pd.notna(row.get('Duration')) else 'Quarterly'
    enroll_date = row.get('Date')
    if pd.notna(enroll_date):
        if isinstance(enroll_date, datetime):
            enroll_date = enroll_date.date()
        elif isinstance(enroll_date, date):
            pass  # Already a date
        elif isinstance(enroll_date, str):
            # Parse DD/MM/YYYY format
            try:
                enroll_date = datetime.strptime(enroll_date.strip(), "%d/%m/%Y").date()
            except:
                enroll_date = None
        else:
            enroll_date = None
    else:
        enroll_date = None

    batch_id = batches.get(batch_name)
    if not batch_id:
        # Try to find similar batch
        for bn, bid in batches.items():
            if batch_name.lower() in bn.lower() or bn.lower() in batch_name.lower():
                batch_id = bid
                break

    if not batch_id:
        print(f"  SKIP: {enquiry_id} {child_name} - unknown batch '{batch_name}'")
        errors += 1
        continue

    # Find child by enquiry_id
    child = db.execute(text("""
        SELECT id FROM children WHERE center_id = :cid AND enquiry_id = :eid
    """), {"cid": CHANDIGARH_CENTER_ID, "eid": enquiry_id}).fetchone()

    if not child:
        # Try fuzzy name match
        child = db.execute(text("""
            SELECT id FROM children WHERE center_id = :cid
            AND LOWER(REPLACE(first_name, ' ', '')) = LOWER(REPLACE(:name, ' ', ''))
            AND enquiry_id IS NULL
            LIMIT 1
        """), {"cid": CHANDIGARH_CENTER_ID, "name": child_name}).fetchone()

        if child:
            db.execute(text("UPDATE children SET enquiry_id = :eid WHERE id = :cid"),
                       {"eid": enquiry_id, "cid": child.id})

    if not child:
        print(f"  SKIP: {enquiry_id} {child_name} - child not found")
        errors += 1
        continue

    child_id = child.id

    # Find enrollment for this child + batch
    enrollment = db.execute(text("""
        SELECT id, visits_used FROM enrollments
        WHERE child_id = :child AND batch_id = :bid AND is_archived = false
    """), {"child": child_id, "bid": batch_id}).fetchone()

    if not enrollment:
        # Check attendance CSV to see if they have attendance in a different batch
        att_info = attendance_data.get(enquiry_id)
        if att_info and att_info['batch'] != batch_name:
            # The attendance is in a different batch than enrollment!
            att_batch_id = batches.get(att_info['batch'])
            if att_batch_id:
                # Check if there's an enrollment in the attendance batch
                enrollment = db.execute(text("""
                    SELECT id, visits_used FROM enrollments
                    WHERE child_id = :child AND batch_id = :bid AND is_archived = false
                """), {"child": child_id, "bid": att_batch_id}).fetchone()

    if not enrollment:
        print(f"  SKIP: {enquiry_id} {child_name} - no enrollment found for batch {batch_name}")
        errors += 1
        continue

    enrollment_id = enrollment.id

    # Map duration to plan_type
    plan_type = 'QUARTERLY'
    if 'yearly' in duration.lower() or 'year' in duration.lower():
        plan_type = 'YEARLY'
    elif 'monthly' in duration.lower() or 'month' in duration.lower():
        plan_type = 'MONTHLY'
    elif 'half' in duration.lower():
        plan_type = 'YEARLY'

    # Update enrollment
    db.execute(text("""
        UPDATE enrollments
        SET visits_included = :booked, plan_type = :plan, start_date = COALESCE(:sdate, start_date)
        WHERE id = :eid
    """), {"booked": booked, "plan": plan_type, "sdate": enroll_date, "eid": enrollment_id})

    # Check if payment exists
    existing_payment = db.execute(text("""
        SELECT id FROM payments WHERE enrollment_id = :eid LIMIT 1
    """), {"eid": enrollment_id}).fetchone()

    if not existing_payment and paid_amount > 0:
        # Create payment
        db.execute(text("""
            INSERT INTO payments (center_id, enrollment_id, amount, currency, method, paid_at,
                discount_total, net_amount, created_by_id, updated_by_id, created_at, updated_at, is_archived)
            VALUES (:cid, :eid, :amt, 'INR', 'CASH', :pdate, 0, :amt, 6, 6, NOW(), NOW(), false)
        """), {"cid": CHANDIGARH_CENTER_ID, "eid": enrollment_id, "amt": paid_amount, "pdate": enroll_date or date.today()})

    updated += 1

db.commit()
print(f"\nUpdated {updated} enrollments, {errors} errors")

# Now sync attendance
print("\n" + "="*70)
print("Syncing attendance data...")
print("="*70)

att_created = 0
sessions_created = 0

for enquiry_id, att_info in attendance_data.items():
    child = db.execute(text("""
        SELECT id FROM children WHERE center_id = :cid AND enquiry_id = :eid
    """), {"cid": CHANDIGARH_CENTER_ID, "eid": enquiry_id}).fetchone()

    if not child:
        continue

    child_id = child.id
    batch_name = att_info['batch']
    batch_id = batches.get(batch_name)

    if not batch_id:
        continue

    # Get enrollment
    enrollment = db.execute(text("""
        SELECT id FROM enrollments WHERE child_id = :child AND batch_id = :bid AND is_archived = false
    """), {"child": child_id, "bid": batch_id}).fetchone()

    if not enrollment:
        continue

    enrollment_id = enrollment.id

    # Get existing attendance dates for this child
    existing_dates = set()
    for r in db.execute(text("""
        SELECT cs.session_date FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
    """), {"child": child_id, "bid": batch_id}).fetchall():
        existing_dates.add(r.session_date)

    for att_date in att_info['dates']:
        if att_date in existing_dates:
            continue

        # Find or create session
        session = db.execute(text("""
            SELECT id FROM class_sessions WHERE center_id = :cid AND batch_id = :bid AND session_date = :dt
        """), {"cid": CHANDIGARH_CENTER_ID, "bid": batch_id, "dt": att_date}).fetchone()

        if not session:
            result = db.execute(text("""
                INSERT INTO class_sessions (center_id, batch_id, session_date, status,
                    created_by_id, updated_by_id, created_at, updated_at, is_archived)
                VALUES (:cid, :bid, :dt, 'COMPLETED', 6, 6, NOW(), NOW(), false)
                RETURNING id
            """), {"cid": CHANDIGARH_CENTER_ID, "bid": batch_id, "dt": att_date})
            session_id = result.fetchone()[0]
            sessions_created += 1
        else:
            session_id = session.id

        # Create attendance
        db.execute(text("""
            INSERT INTO attendance (center_id, class_session_id, child_id, enrollment_id, status,
                marked_by_user_id, marked_at, notes, created_by_id, updated_by_id, created_at, updated_at, is_archived)
            VALUES (:cid, :sid, :child, :eid, 'PRESENT', 6, NOW(), 'Imported', 6, 6, NOW(), NOW(), false)
        """), {"cid": CHANDIGARH_CENTER_ID, "sid": session_id, "child": child_id, "eid": enrollment_id})
        att_created += 1

db.commit()
print(f"Created {att_created} attendance records, {sessions_created} sessions")

# Recalculate visits_used
print("\n" + "="*70)
print("Recalculating visits_used...")
print("="*70)

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
print("Done!")

# Verify Abeer
print("\n" + "="*70)
print("Verification - ABEER records:")
print("="*70)

abeers = db.execute(text("""
    SELECT c.id, c.first_name, c.enquiry_id,
           e.id as enr_id, b.name as batch, e.visits_used, e.visits_included,
           (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE enrollment_id = e.id) as paid
    FROM children c
    JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE c.center_id = :cid AND c.first_name ILIKE '%abeer%'
    ORDER BY c.enquiry_id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for a in abeers:
    print(f"  {a.enquiry_id} | {a.first_name} | {a.batch} | {a.visits_used}/{a.visits_included} | Paid: Rs.{a.paid}")

db.close()
