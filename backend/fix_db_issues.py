"""
Comprehensive DB fix script for The Little Gym CRM.
Fixes:
1. 5 enrollments with swapped start/end dates
2. 10 'Not Known' + 3 'Dead Lead' placeholder children (archive them)
3. 9 enrollments where visits_used > visits_included (mark EXPIRED, store carry-forward)
4. 27 duplicate active enrollments for same child+batch (keep latest, expire older)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)


def fix_swapped_dates(conn):
    """Fix enrollments where end_date < start_date by swapping them."""
    print("=" * 60)
    print("FIX 1: Enrollments with swapped start/end dates")
    print("=" * 60)

    rows = conn.execute(text(
        "SELECT id, start_date, end_date, status FROM enrollments WHERE end_date < start_date"
    )).fetchall()

    print(f"Found {len(rows)} enrollments with end_date < start_date")
    for row in rows:
        conn.execute(text(
            "UPDATE enrollments SET start_date = :end_date, end_date = :start_date WHERE id = :id"
        ), {"id": row[0], "start_date": row[1], "end_date": row[2]})
        print(f"  Enrollment {row[0]}: swapped {row[1]} <-> {row[2]}")

    return len(rows)


def archive_placeholder_children(conn):
    """Archive 'Not Known' and 'Dead Lead' placeholder children."""
    print("\n" + "=" * 60)
    print("FIX 2: Archive placeholder children")
    print("=" * 60)

    rows = conn.execute(text("""
        SELECT c.id, c.first_name, c.enquiry_id,
               (SELECT COUNT(*) FROM enrollments e WHERE e.child_id = c.id AND e.status = 'ACTIVE') as active_enrollments,
               (SELECT COUNT(*) FROM attendance a WHERE a.child_id = c.id) as attendance_count
        FROM children c
        WHERE c.first_name IN ('Not Known', 'Dead Lead')
          AND c.is_archived = false
        ORDER BY c.first_name, c.id
    """)).fetchall()

    print(f"Found {len(rows)} placeholder children:")
    archived = 0
    skipped = 0

    for row in rows:
        child_id, name, enquiry_id, active_enrollments, attendance_count = row
        if active_enrollments > 0 or attendance_count > 0:
            print(f"  SKIP Child {child_id} ({name}, {enquiry_id}): has {active_enrollments} active enrollments, {attendance_count} attendance")
            skipped += 1
        else:
            conn.execute(text("UPDATE children SET is_archived = true WHERE id = :id"), {"id": child_id})
            conn.execute(text("UPDATE leads SET is_archived = true WHERE child_id = :id"), {"id": child_id})
            print(f"  ARCHIVED Child {child_id} ({name}, {enquiry_id})")
            archived += 1

    print(f"Archived {archived}, skipped {skipped}")
    return archived


def fix_overused_enrollments(conn):
    """Mark overused enrollments as EXPIRED and store carry-forward in notes."""
    print("\n" + "=" * 60)
    print("FIX 3: Enrollments exceeding visit limits -> EXPIRED + carry-forward")
    print("=" * 60)

    rows = conn.execute(text("""
        SELECT e.id, c.first_name, c.enquiry_id, e.visits_used, e.visits_included, e.notes
        FROM enrollments e
        JOIN children c ON c.id = e.child_id
        WHERE e.visits_used > e.visits_included
          AND e.visits_included IS NOT NULL AND e.visits_included > 0
          AND e.status = 'ACTIVE'
        ORDER BY e.id
    """)).fetchall()

    print(f"Found {len(rows)} ACTIVE enrollments exceeding visit limits:")
    for row in rows:
        eid, name, enquiry_id, used, included, existing_notes = row
        excess = used - included
        carry_note = f"[Carry-forward: {excess} visits to next enrollment]"
        new_notes = f"{existing_notes} {carry_note}" if existing_notes else carry_note

        conn.execute(text(
            "UPDATE enrollments SET status = 'EXPIRED', notes = :notes WHERE id = :id"
        ), {"id": eid, "notes": new_notes})
        print(f"  Enrollment {eid} ({name}, {enquiry_id}): {used}/{included} visits, excess={excess} -> EXPIRED")

    return len(rows)


def fix_duplicate_active_enrollments(conn):
    """Keep latest active enrollment per child+batch, expire older ones."""
    print("\n" + "=" * 60)
    print("FIX 4: Duplicate active enrollments (same child + batch)")
    print("=" * 60)

    dupes = conn.execute(text("""
        SELECT child_id, batch_id, COUNT(*) as cnt
        FROM enrollments
        WHERE status = 'ACTIVE' AND batch_id IS NOT NULL
        GROUP BY child_id, batch_id
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """)).fetchall()

    print(f"Found {len(dupes)} child+batch combos with multiple ACTIVE enrollments:")
    total_expired = 0

    for dupe in dupes:
        child_id, batch_id, count = dupe
        enrollments = conn.execute(text("""
            SELECT e.id, e.start_date, e.end_date, e.visits_used, c.first_name, c.enquiry_id
            FROM enrollments e
            JOIN children c ON c.id = e.child_id
            WHERE e.child_id = :cid AND e.batch_id = :bid AND e.status = 'ACTIVE'
            ORDER BY e.start_date DESC NULLS LAST, e.id DESC
        """), {"cid": child_id, "bid": batch_id}).fetchall()

        latest = enrollments[0]
        print(f"\n  Child {child_id} ({latest[4]}, {latest[5]}), Batch {batch_id}: {count} active")
        print(f"    KEEP   Enrollment {latest[0]} (start: {latest[1]}, visits: {latest[3]})")

        for old in enrollments[1:]:
            conn.execute(text(
                "UPDATE enrollments SET status = 'EXPIRED' WHERE id = :id"
            ), {"id": old[0]})
            print(f"    EXPIRE Enrollment {old[0]} (start: {old[1]}, visits: {old[3]})")
            total_expired += 1

    print(f"\nExpired {total_expired} duplicate enrollments")
    return total_expired


def verify(conn):
    """Post-fix verification."""
    print("\n" + "=" * 60)
    print("POST-FIX VERIFICATION")
    print("=" * 60)

    checks = [
        ("Enrollments with swapped dates", "SELECT COUNT(*) FROM enrollments WHERE end_date < start_date"),
        ("Unarchived placeholder children", "SELECT COUNT(*) FROM children WHERE first_name IN ('Not Known', 'Dead Lead') AND is_archived = false"),
        ("ACTIVE enrollments exceeding visits", "SELECT COUNT(*) FROM enrollments WHERE visits_used > visits_included AND visits_included > 0 AND status = 'ACTIVE'"),
        ("Duplicate active enrollments", "SELECT COUNT(*) FROM (SELECT child_id, batch_id FROM enrollments WHERE status = 'ACTIVE' AND batch_id IS NOT NULL GROUP BY child_id, batch_id HAVING COUNT(*) > 1) sub"),
        ("Children with NULL enquiry_id", "SELECT COUNT(*) FROM children WHERE enquiry_id IS NULL"),
        ("Total ACTIVE enrollments", "SELECT COUNT(*) FROM enrollments WHERE status = 'ACTIVE'"),
        ("Total EXPIRED enrollments", "SELECT COUNT(*) FROM enrollments WHERE status = 'EXPIRED'"),
    ]

    for label, query in checks:
        result = conn.execute(text(query)).scalar()
        status = "OK" if result == 0 or "Total" in label else "REMAINING"
        print(f"  [{status}] {label}: {result}")


if __name__ == "__main__":
    with engine.connect() as conn:
        fix_swapped_dates(conn)
        archive_placeholder_children(conn)
        fix_overused_enrollments(conn)
        fix_duplicate_active_enrollments(conn)
        conn.commit()
        print("\nAll fixes committed.\n")
        verify(conn)
        print("\nDone!")
