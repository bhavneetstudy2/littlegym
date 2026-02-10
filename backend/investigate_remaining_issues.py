"""
Investigate remaining attendance count issues
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("INVESTIGATING REMAINING ISSUES")
print("="*70)

# Get the problematic enrollments
issues = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.start_date, e.end_date,
           e.plan_type, e.status, c.id as child_id, b.id as batch_id
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY (e.visits_used::float / NULLIF(e.visits_included, 0)) DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for r in issues:
    print(f"\n{'='*70}")
    print(f"Enrollment ID: {r.id}")
    print(f"Child: {r.enquiry_id} - {r.first_name}")
    print(f"Batch: {r.batch}")
    print(f"Attended: {r.visits_used}/{r.visits_included}")
    print(f"Plan: {r.plan_type} | Status: {r.status}")
    print(f"Period: {r.start_date} to {r.end_date}")

    # Check if there are multiple enrollments for this child+batch
    all_enrollments = db.execute(text("""
        SELECT id, start_date, end_date, visits_included, visits_used, status, is_archived
        FROM enrollments
        WHERE child_id = :child AND batch_id = :bid
        ORDER BY start_date
    """), {"child": r.child_id, "bid": r.batch_id}).fetchall()

    if len(all_enrollments) > 1:
        print(f"\n  MULTIPLE ENROLLMENTS for this child+batch:")
        for e in all_enrollments:
            archived = " (ARCHIVED)" if e.is_archived else ""
            print(f"    ID:{e.id} | {e.start_date} to {e.end_date} | {e.visits_used}/{e.visits_included} | {e.status}{archived}")

    # Check attendance distribution
    att = db.execute(text("""
        SELECT MIN(cs.session_date) as first_att,
               MAX(cs.session_date) as last_att,
               COUNT(*) as total_att
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.is_archived = false AND a.status = 'PRESENT'
    """), {"child": r.child_id, "bid": r.batch_id}).fetchone()

    print(f"\n  Attendance range: {att.first_att} to {att.last_att} ({att.total_att} total)")

    # Check attendance outside enrollment period
    outside = db.execute(text("""
        SELECT cs.session_date
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.is_archived = false AND a.status = 'PRESENT'
          AND (cs.session_date < :start OR (:end IS NOT NULL AND cs.session_date > :end))
        ORDER BY cs.session_date
    """), {"child": r.child_id, "bid": r.batch_id, "start": r.start_date, "end": r.end_date}).fetchall()

    if outside:
        print(f"\n  WARNING: {len(outside)} attendance records OUTSIDE enrollment period:")
        for o in outside[:5]:
            print(f"    {o.session_date}")
        if len(outside) > 5:
            print(f"    ... and {len(outside) - 5} more")

    # Check Excel data for this child
    print(f"\n  Checking Excel for {r.enquiry_id}...")
    try:
        import pandas as pd
        EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

        # Check Enrolled sheet
        enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
        child_rows = enrolled_df[enrolled_df['Enquiry ID'] == r.enquiry_id]
        batch_rows = child_rows[child_rows['Batch'] == r.batch]

        if not batch_rows.empty:
            print(f"  Found in Enrolled sheet:")
            for idx, row in batch_rows.iterrows():
                booked = row.get('Booked Classes')
                attended = row.get('Attended')
                print(f"    Booked: {booked} | Attended: {attended} | Date: {row.get('Date')} | Duration: {row.get('Duration')}")

        # Check Expired sheet
        try:
            expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
            exp_rows = expired_df[expired_df['Enquiry ID'] == r.enquiry_id]
            exp_batch_rows = exp_rows[exp_rows['Batch'] == r.batch]

            if not exp_batch_rows.empty:
                print(f"  Found in Expired sheet:")
                for idx, row in exp_batch_rows.iterrows():
                    booked = row.get('Booked')
                    availed = row.get('Availed')
                    print(f"    Booked: {booked} | Availed: {availed}")
        except:
            pass
    except Exception as e:
        print(f"  Could not check Excel: {e}")

db.close()
print("\n" + "="*70)
