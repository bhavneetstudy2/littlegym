"""
Delete lead records without Enquiry IDs (only those with no enrollments/attendance)
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

CHANDIGARH_CENTER_ID = 3

print("="*70)
print("DELETING LEAD RECORDS WITHOUT ENQUIRY IDs")
print("="*70)

db = SessionLocal()

# First, find all children without IDs
no_id_children = db.execute(text("""
    SELECT c.id, c.first_name, c.last_name,
           (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enrollment_count,
           (SELECT COUNT(*) FROM attendance a
            JOIN class_sessions cs ON a.class_session_id = cs.id
            WHERE a.child_id = c.id AND a.is_archived = false) as attendance_count
    FROM children c
    WHERE (c.enquiry_id IS NULL OR c.enquiry_id = 'None' OR c.enquiry_id = '')
      AND c.center_id = :cid
    ORDER BY c.id
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

print(f"\nFound {len(no_id_children)} children without Enquiry IDs")

# Separate into can-delete and must-keep
can_delete = []
must_keep = []

for child in no_id_children:
    if child.enrollment_count == 0 and child.attendance_count == 0:
        can_delete.append(child)
    else:
        must_keep.append(child)

print(f"\n  Can safely delete: {len(can_delete)} (no enrollments, no attendance)")
print(f"  Must keep: {len(must_keep)} (have enrollments or attendance)")

# Show what will be kept
if must_keep:
    print("\n" + "="*70)
    print("WILL BE KEPT (have enrollments/attendance):")
    print("="*70)
    for child in must_keep:
        full_name = f"{child.first_name} {child.last_name or ''}".strip()
        print(f"  Child {child.id}: {full_name}")
        print(f"    Enrollments: {child.enrollment_count}, Attendance: {child.attendance_count}")

# Delete the ones we can safely delete
print("\n" + "="*70)
print("DELETING LEADS WITHOUT IDs (safe to delete):")
print("="*70)

if can_delete:
    print(f"\nDeleting {len(can_delete)} children...")

    # Delete in correct order due to foreign key constraints
    # 1. Delete intro_visits FIRST (references leads)
    iv_deleted = 0
    for child in can_delete:
        # Delete by child_id
        result = db.execute(text("""
            DELETE FROM intro_visits WHERE child_id = :cid
        """), {"cid": child.id})
        iv_deleted += result.rowcount

        # Also delete by lead_id
        result2 = db.execute(text("""
            DELETE FROM intro_visits WHERE lead_id IN (
                SELECT id FROM leads WHERE child_id = :cid
            )
        """), {"cid": child.id})
        iv_deleted += result2.rowcount

    print(f"  Deleted {iv_deleted} intro visits")

    # 2. Delete leads (now safe to delete)
    leads_deleted = 0
    for child in can_delete:
        result = db.execute(text("""
            DELETE FROM leads WHERE child_id = :cid
        """), {"cid": child.id})
        leads_deleted += result.rowcount

    print(f"  Deleted {leads_deleted} leads")

    # 3. Delete family_links
    for child in can_delete:
        db.execute(text("""
            DELETE FROM family_links WHERE child_id = :cid
        """), {"cid": child.id})

    print(f"  Deleted family links")

    # 4. Finally delete children
    for child in can_delete:
        db.execute(text("""
            DELETE FROM children WHERE id = :cid
        """), {"cid": child.id})

    db.commit()
    print(f"  Deleted {len(can_delete)} children")
else:
    print("  No children to delete")

# Also need to handle parents that are now orphaned
print("\n" + "="*70)
print("CLEANING UP ORPHANED PARENTS:")
print("="*70)

orphaned_parents = db.execute(text("""
    SELECT p.id, p.name, p.phone
    FROM parents p
    WHERE p.center_id = :cid
      AND NOT EXISTS (
        SELECT 1 FROM family_links fl WHERE fl.parent_id = p.id
      )
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

if orphaned_parents:
    print(f"\nFound {len(orphaned_parents)} orphaned parents (no children linked)")

    for parent in orphaned_parents:
        print(f"  Deleting parent: {parent.name} ({parent.phone})")
        db.execute(text("""
            DELETE FROM parents WHERE id = :pid
        """), {"pid": parent.id})

    db.commit()
    print(f"\n  Deleted {len(orphaned_parents)} orphaned parents")
else:
    print("\n  No orphaned parents to delete")

# Verification
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

remaining_no_id = db.execute(text("""
    SELECT COUNT(*) as cnt
    FROM children
    WHERE (enquiry_id IS NULL OR enquiry_id = 'None' OR enquiry_id = '')
      AND center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nChildren without Enquiry IDs remaining: {remaining_no_id.cnt}")

if remaining_no_id.cnt > 0:
    print("\nRemaining children (all have enrollments/attendance):")
    remaining = db.execute(text("""
        SELECT c.id, c.first_name, c.last_name,
               (SELECT COUNT(*) FROM enrollments WHERE child_id = c.id AND is_archived = false) as enrollments,
               (SELECT COUNT(*) FROM attendance a WHERE a.child_id = c.id AND a.is_archived = false) as attendance
        FROM children c
        WHERE (c.enquiry_id IS NULL OR c.enquiry_id = 'None' OR c.enquiry_id = '')
          AND c.center_id = :cid
        ORDER BY c.first_name
    """), {"cid": CHANDIGARH_CENTER_ID}).fetchall()

    for r in remaining:
        full_name = f"{r.first_name} {r.last_name or ''}".strip()
        print(f"  {full_name}: {r.enrollments} enrollments, {r.attendance} attendance")

total_children = db.execute(text("""
    SELECT COUNT(*) as cnt FROM children WHERE center_id = :cid
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

print(f"\nTotal children in database: {total_children.cnt}")

db.close()
print("\n" + "="*70)
print("CLEANUP COMPLETE!")
print("="*70)
