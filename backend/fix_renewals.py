"""
Fix children who have attendance in batches they're not enrolled in.
This happens because the import script only created/updated one enrollment per child,
so renewals in different batches lost their enrollment record.

Fix:
1. Create missing enrollment records for each child-batch pair
2. Link attendance records to the correct enrollment
3. Recalculate visits_used for all affected enrollments
"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from sqlalchemy import text
from datetime import date

db = SessionLocal()

CHANDIGARH_CENTER_ID = 3

# Find children with attendance in batches they have no enrollment for
missing = db.execute(text("""
    WITH child_enrolled_batches AS (
        SELECT child_id, batch_id, id as enrollment_id FROM enrollments WHERE is_archived = false
    ),
    child_attendance_batches AS (
        SELECT DISTINCT a.child_id, cs.batch_id,
               COUNT(*) as att_count,
               MIN(cs.session_date) as first_date,
               MAX(cs.session_date) as last_date
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        GROUP BY a.child_id, cs.batch_id
    )
    SELECT cab.child_id, c.first_name, c.enquiry_id,
           cab.batch_id, b.name as batch_name,
           cab.att_count, cab.first_date, cab.last_date
    FROM child_attendance_batches cab
    JOIN children c ON cab.child_id = c.id
    JOIN batches b ON cab.batch_id = b.id
    LEFT JOIN child_enrolled_batches ceb
        ON cab.child_id = ceb.child_id AND cab.batch_id = ceb.batch_id
    WHERE ceb.child_id IS NULL
    ORDER BY c.first_name
""")).fetchall()

print("=" * 60)
print(f"FIX: Creating {len(missing)} missing enrollment records")
print("=" * 60)

created_enrollments = []

for row in missing:
    child_id, child_name, enquiry_id, batch_id, batch_name, att_count, first_date, last_date = row

    # Calculate a reasonable end_date (3 months after first session)
    from datetime import timedelta
    est_end = first_date + timedelta(days=90)
    if est_end < last_date:
        est_end = last_date + timedelta(days=7)

    print(f"\n  {child_name} ({enquiry_id}): Creating enrollment for {batch_name}")
    print(f"    {att_count} sessions from {first_date} to {last_date}")

    # Create the missing enrollment
    result = db.execute(text("""
        INSERT INTO enrollments (
            center_id, child_id, batch_id, plan_type, status,
            start_date, end_date, visits_included, visits_used,
            days_selected, notes, is_archived,
            created_by_id, updated_by_id, created_at, updated_at
        ) VALUES (
            :center_id, :child_id, :batch_id, 'QUARTERLY', 'EXPIRED',
            :start_date, :end_date, :visits_included, :visits_used,
            NULL, :notes, false,
            1, 1, NOW(), NOW()
        ) RETURNING id
    """), {
        "center_id": CHANDIGARH_CENTER_ID,
        "child_id": child_id,
        "batch_id": batch_id,
        "start_date": first_date,
        "end_date": est_end,
        "visits_included": att_count,
        "visits_used": att_count,
        "notes": f"Past enrollment (reconstructed from attendance data). {att_count} sessions in {batch_name}."
    })
    new_enr_id = result.fetchone()[0]
    created_enrollments.append((new_enr_id, child_id, batch_id, batch_name))
    print(f"    Created enrollment id={new_enr_id}")

    # Link attendance records to this enrollment
    updated = db.execute(text("""
        UPDATE attendance SET enrollment_id = :enr_id
        FROM class_sessions cs
        WHERE attendance.class_session_id = cs.id
          AND attendance.child_id = :child_id
          AND cs.batch_id = :batch_id
          AND (attendance.enrollment_id IS NULL OR attendance.enrollment_id NOT IN (
              SELECT id FROM enrollments WHERE child_id = :child_id AND batch_id = :batch_id
          ))
    """), {
        "enr_id": new_enr_id,
        "child_id": child_id,
        "batch_id": batch_id
    })
    print(f"    Linked {updated.rowcount} attendance records")

# Now fix visits_used for ALL enrollments of these affected children
print("\n" + "=" * 60)
print("FIX: Recalculating visits_used for affected children")
print("=" * 60)

affected_child_ids = list(set(row[0] for row in missing))

for child_id in affected_child_ids:
    # Get all enrollments for this child
    enrollments = db.execute(text("""
        SELECT e.id, e.batch_id, b.name, e.visits_used
        FROM enrollments e
        LEFT JOIN batches b ON e.batch_id = b.id
        WHERE e.child_id = :cid
    """), {"cid": child_id}).fetchall()

    child_name = db.execute(text("SELECT first_name FROM children WHERE id = :cid"), {"cid": child_id}).fetchone()[0]
    print(f"\n  {child_name} (child_id={child_id}):")

    for enr in enrollments:
        enr_id, batch_id, batch_name, old_used = enr

        # Count actual attendance in this enrollment's batch
        actual = db.execute(text("""
            SELECT COUNT(*)
            FROM attendance a
            JOIN class_sessions cs ON a.class_session_id = cs.id
            WHERE a.child_id = :cid AND cs.batch_id = :bid
              AND a.status = 'PRESENT'
        """), {"cid": child_id, "bid": batch_id}).scalar() or 0

        if old_used != actual:
            db.execute(text("""
                UPDATE enrollments SET visits_used = :used WHERE id = :eid
            """), {"used": actual, "eid": enr_id})
            print(f"    Enrollment {enr_id} ({batch_name}): {old_used} -> {actual}")
        else:
            print(f"    Enrollment {enr_id} ({batch_name}): {actual} (ok)")

db.commit()
print("\nDone! Changes committed.")
db.close()
