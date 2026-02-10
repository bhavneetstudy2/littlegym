"""
Fix enrollment data issues based on Excel comparison
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
print("FIXING ENROLLMENT DATA ISSUES")
print("="*70)

# Load Excel data
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')

# Fix specific enrollment issues
fixes = [
    # Evaan: should have 24 classes, not 1
    {"enquiry_id": "TLGC0347", "batch": "Super Beasts", "correct_visits": 24},

    # Vihaan: should have 12 classes (Quarterly), not 2
    {"enquiry_id": "TLGC0024", "batch": "Grade School", "correct_visits": 12},
]

print("\nApplying manual fixes:")
for fix in fixes:
    result = db.execute(text("""
        UPDATE enrollments e
        SET visits_included = :visits
        FROM children c, batches b
        WHERE e.child_id = c.id AND e.batch_id = b.id
          AND c.enquiry_id = :eid AND b.name = :batch
          AND e.is_archived = false AND e.center_id = :cid
        RETURNING e.id, e.visits_included
    """), {"eid": fix["enquiry_id"], "batch": fix["batch"],
           "visits": fix["correct_visits"], "cid": CHANDIGARH_CENTER_ID})

    updated = result.fetchone()
    if updated:
        print(f"  {fix['enquiry_id']} | {fix['batch']}: Updated visits_included to {updated.visits_included}")
    else:
        print(f"  {fix['enquiry_id']} | {fix['batch']}: Not found")

db.commit()

# For enrollments where attendance exists before start_date, adjust start_date
print("\nAdjusting enrollment start dates where attendance exists before them:")
result = db.execute(text("""
    UPDATE enrollments e
    SET start_date = (
        SELECT MIN(cs.session_date)
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id
          AND cs.batch_id = e.batch_id
          AND a.is_archived = false
          AND cs.session_date < e.start_date
    )
    WHERE e.center_id = :cid AND e.is_archived = false
      AND EXISTS (
        SELECT 1 FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = e.child_id
          AND cs.batch_id = e.batch_id
          AND a.is_archived = false
          AND cs.session_date < e.start_date
      )
    RETURNING id
"""), {"cid": CHANDIGARH_CENTER_ID})

adjusted = result.fetchall()
print(f"  Adjusted {len(adjusted)} enrollment start dates")
db.commit()

# Archive duplicate active enrollments for same child+batch (keep latest)
print("\nArchiving duplicate active enrollments (keeping latest):")
duplicates = db.execute(text("""
    SELECT child_id, batch_id, COUNT(*) as cnt
    FROM enrollments
    WHERE center_id = :cid AND is_archived = false
    GROUP BY child_id, batch_id
    HAVING COUNT(*) > 1
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

for dup in duplicates:
    print(f"  Child {dup.child_id} + Batch {dup.batch_id}: {dup.cnt} active enrollments")

    # Get all enrollments for this child+batch
    enrollments = db.execute(text("""
        SELECT id, start_date, created_at
        FROM enrollments
        WHERE child_id = :child AND batch_id = :bid
          AND center_id = :cid AND is_archived = false
        ORDER BY start_date DESC, created_at DESC
    """), {"child": dup.child_id, "bid": dup.batch_id, "cid": CHANDIGARH_CENTER_ID}).fetchall()

    # Keep the first (latest), archive the rest
    keep_id = enrollments[0].id
    for e in enrollments[1:]:
        db.execute(text("""
            UPDATE enrollments SET is_archived = true WHERE id = :eid
        """), {"eid": e.id})
        print(f"    Archived enrollment ID {e.id}, keeping ID {keep_id}")

db.commit()

# Recalculate visits_used with correct date ranges
print("\nRecalculating visits_used with date range filtering...")
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

# Verification
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

remaining = db.execute(text("""
    SELECT e.id, c.enquiry_id, c.first_name, b.name as batch,
           e.visits_included, e.visits_used, e.start_date, e.end_date
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    LEFT JOIN batches b ON e.batch_id = b.id
    WHERE e.visits_used > e.visits_included
      AND e.center_id = :cid AND e.is_archived = false
    ORDER BY (e.visits_used::float / NULLIF(e.visits_included, 0)) DESC
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nRemaining issues: {len(remaining)} enrollments with attended > booked")

for r in remaining:
    over = r.visits_used - r.visits_included
    print(f"  {r.enquiry_id} | {r.first_name} | {r.batch} | {r.visits_used}/{r.visits_included} (+{over})")

# Summary stats
stats = db.execute(text("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN visits_used <= visits_included THEN 1 ELSE 0 END) as ok,
        SUM(CASE WHEN visits_used > visits_included THEN 1 ELSE 0 END) as over
    FROM enrollments
    WHERE center_id = :cid AND is_archived = false
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nSummary:")
print(f"  Total enrollments: {stats.total}")
print(f"  Within limits: {stats.ok}")
print(f"  Over booked: {stats.over}")

db.close()
print("\nDone!")
