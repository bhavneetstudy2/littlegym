"""
Fix duplicate enrollments created by the import script running multiple times.

For each child, if they have multiple enrollments in the SAME batch with the SAME status,
keep the one with the lowest ID (oldest) and archive the duplicates.
Re-link attendance records to the surviving enrollment.
"""
import sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Find duplicate groups: same child_id + batch_id + status with more than 1 enrollment
dupes = db.execute(text("""
    SELECT child_id, batch_id, status,
           ARRAY_AGG(id ORDER BY id) as enrollment_ids,
           COUNT(*) as cnt
    FROM enrollments
    WHERE is_archived = false AND batch_id IS NOT NULL
    GROUP BY child_id, batch_id, status
    HAVING COUNT(*) > 1
    ORDER BY child_id
""")).fetchall()

print(f"Found {len(dupes)} duplicate groups to fix")
print("=" * 70)

total_archived = 0
total_relinked = 0

for row in dupes:
    child_id, batch_id, status, enrollment_ids, cnt = row
    keep_id = enrollment_ids[0]  # Keep the oldest (lowest ID)
    archive_ids = enrollment_ids[1:]  # Archive the rest

    # Get child name and batch name for logging
    info = db.execute(text("""
        SELECT c.first_name, b.name as batch_name
        FROM children c, batches b
        WHERE c.id = :cid AND b.id = :bid
    """), {"cid": child_id, "bid": batch_id}).fetchone()

    child_name = info.first_name if info else f"child_{child_id}"
    batch_name = info.batch_name if info else f"batch_{batch_id}"

    print(f"\n  {child_name} | {batch_name} ({status}): {cnt} enrollments -> keeping #{keep_id}, archiving {archive_ids}")

    # Re-link attendance records from duplicate enrollments to the keeper
    for dup_id in archive_ids:
        updated = db.execute(text("""
            UPDATE attendance SET enrollment_id = :keep_id
            WHERE enrollment_id = :dup_id
        """), {"keep_id": keep_id, "dup_id": dup_id})
        if updated.rowcount > 0:
            print(f"    Relinked {updated.rowcount} attendance records from enrollment #{dup_id}")
            total_relinked += updated.rowcount

    # Archive the duplicates
    archived = db.execute(text("""
        UPDATE enrollments SET is_archived = true
        WHERE id = ANY(:ids)
    """), {"ids": archive_ids})
    total_archived += archived.rowcount
    print(f"    Archived {archived.rowcount} duplicate enrollments")

# Now recalculate visits_used for all surviving enrollments that were affected
print("\n" + "=" * 70)
print("Recalculating visits_used for affected enrollments...")

affected_ids = [row[3][0] for row in dupes]  # keep_ids
for keep_id in affected_ids:
    actual = db.execute(text("""
        SELECT COUNT(*) FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN enrollments e ON e.id = :eid
        WHERE a.enrollment_id = :eid AND a.status = 'PRESENT'
    """), {"eid": keep_id}).scalar() or 0

    current = db.execute(text("SELECT visits_used FROM enrollments WHERE id = :eid"), {"eid": keep_id}).scalar()
    if current != actual:
        db.execute(text("UPDATE enrollments SET visits_used = :used WHERE id = :eid"), {"used": actual, "eid": keep_id})
        print(f"  Enrollment #{keep_id}: visits_used {current} -> {actual}")

db.commit()
print(f"\nDone! Archived {total_archived} duplicate enrollments, relinked {total_relinked} attendance records.")

# Verify: check remaining duplicates
remaining = db.execute(text("""
    SELECT COUNT(*) FROM (
        SELECT child_id, batch_id, status
        FROM enrollments
        WHERE is_archived = false AND batch_id IS NOT NULL
        GROUP BY child_id, batch_id, status
        HAVING COUNT(*) > 1
    ) sub
""")).scalar()
print(f"Remaining duplicate groups: {remaining}")

db.close()
