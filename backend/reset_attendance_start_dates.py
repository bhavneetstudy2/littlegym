"""
Reset enrollment start dates back to original and note extra attendance
"""
import sys
sys.path.insert(0, '.')
import pandas as pd
from datetime import datetime
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3
EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

print("="*70)
print("RESETTING ENROLLMENT DATES TO EXCEL VALUES")
print("="*70)

# Load Excel
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')

# Convert Date column to datetime for proper sorting
def parse_date_flexible(d):
    if pd.isna(d):
        return None
    if isinstance(d, datetime):
        return d
    if isinstance(d, str):
        try:
            return datetime.strptime(d, "%d/%m/%Y")
        except:
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except:
                return None
    return None

enrolled_df['Date'] = enrolled_df['Date'].apply(parse_date_flexible)

# For each child, get their LATEST enrollment from Excel
print("\nResetting enrollment dates to match Excel (latest enrollment only):")

# Get all active enrollments
enrollments = db.execute(text("""
    SELECT e.id, c.enquiry_id, b.name as batch, e.start_date
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    JOIN batches b ON e.batch_id = b.id
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

reset_count = 0

for enr in enrollments:
    # Find this enrollment in Excel
    excel_rows = enrolled_df[
        (enrolled_df['Enquiry ID'] == enr.enquiry_id) &
        (enrolled_df['Batch'] == enr.batch)
    ].sort_values('Date', ascending=False)  # Get latest

    if not excel_rows.empty:
        # Use the LATEST enrollment date from Excel
        latest_row = excel_rows.iloc[0]
        excel_date = latest_row.get('Date')

        if pd.notna(excel_date):
            if isinstance(excel_date, str):
                try:
                    excel_date = datetime.strptime(excel_date, "%d/%m/%Y").date()
                except:
                    continue
            elif isinstance(excel_date, datetime):
                excel_date = excel_date.date()

            # Update enrollment start date to Excel date
            db.execute(text("""
                UPDATE enrollments
                SET start_date = :new_date
                WHERE id = :eid
            """), {"eid": enr.id, "new_date": excel_date})
            reset_count += 1

print(f"  Reset {reset_count} enrollment dates")
db.commit()

# Recalculate visits_used with corrected date ranges
print("\nRecalculating visits_used with correct date ranges...")
db.execute(text("""
    UPDATE enrollments e
    SET visits_used = COALESCE((
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id
          AND cs.batch_id = e.batch_id
          AND a.status = 'PRESENT'
          AND a.is_archived = false
          AND cs.session_date >= e.start_date
          AND (e.end_date IS NULL OR cs.session_date <= e.end_date)
    ), 0)
    WHERE e.center_id = :cid AND e.is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID})
db.commit()

# Check results
print("\n" + "="*70)
print("RESULTS")
print("="*70)

remaining = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.start_date
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY (e.visits_used::float / NULLIF(e.visits_included, 0)) DESC
    LIMIT 20
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

count_result = db.execute(text("""
    SELECT COUNT(*) as cnt FROM enrollments
    WHERE visits_used > visits_included AND center_id = :cid AND is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nEnrollments with attended > booked: {count_result.cnt}")

if remaining:
    print("\nTop cases:")
    for r in remaining:
        over = r.visits_used - r.visits_included
        pct = (over / r.visits_included * 100) if r.visits_included > 0 else 0
        print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} (+{over}, +{pct:.0f}%)")

# These are legitimate cases where kids attended more than booked
# (likely renewals where Excel doesn't clearly separate periods)
# Let's add notes to explain this

print("\nAdding notes to enrollments with extra attendance...")
for r in remaining[:10]:  # Top 10 cases
    extra = r.visits_used - r.visits_included
    note = f"Note: {extra} additional classes attended (likely includes renewal/extension period)"

    current_notes = db.execute(text("""
        SELECT notes FROM enrollments WHERE id = :eid
    """), {"eid": r.id}).fetchone().notes or ""

    if "additional classes attended" not in current_notes:
        new_notes = (current_notes + "; " + note) if current_notes else note
        db.execute(text("""
            UPDATE enrollments SET notes = :notes WHERE id = :eid
        """), {"eid": r.id, "notes": new_notes})

db.commit()

db.close()
print("\nDone!")
