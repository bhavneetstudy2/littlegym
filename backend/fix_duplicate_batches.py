"""Fix duplicate batch records in the database.

Each batch name exists twice. This script:
1. Identifies originals (lower ID) vs duplicates (higher ID)
2. Remaps all references (enrollments, class_sessions, intro_visits, batch_mappings) to the original
3. Deletes the duplicate batch records
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Step 1: Find duplicate batches (same name + center_id)
    dupes = db.execute(text("""
        SELECT name, center_id,
               MIN(id) as keep_id,
               MAX(id) as delete_id,
               COUNT(*) as cnt
        FROM batches
        WHERE center_id = 3
        GROUP BY name, center_id
        HAVING COUNT(*) > 1
        ORDER BY name
    """)).fetchall()

    if not dupes:
        print("No duplicate batches found!")
        sys.exit(0)

    print("=== Duplicate Batches Found ===")
    for d in dupes:
        print(f"  {d.name}: KEEP id={d.keep_id}, DELETE id={d.delete_id}")

    # Step 2: Check references for each duplicate
    print("\n=== Checking References ===")
    tables_to_check = [
        ("enrollments", "batch_id"),
        ("class_sessions", "batch_id"),
        ("intro_visits", "batch_id"),
        ("batch_mappings", "batch_id"),
    ]

    for d in dupes:
        delete_id = d.delete_id
        keep_id = d.keep_id
        print(f"\n  Batch '{d.name}' (delete id={delete_id} -> keep id={keep_id}):")

        for table, col in tables_to_check:
            count = db.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE {col} = :bid"),
                {"bid": delete_id}
            ).scalar()
            if count > 0:
                print(f"    {table}: {count} rows to remap")

    # Step 3: Remap all references
    print("\n=== Remapping References ===")
    total_remapped = 0
    for d in dupes:
        delete_id = d.delete_id
        keep_id = d.keep_id

        for table, col in tables_to_check:
            result = db.execute(
                text(f"UPDATE {table} SET {col} = :keep_id WHERE {col} = :delete_id"),
                {"keep_id": keep_id, "delete_id": delete_id}
            )
            if result.rowcount > 0:
                print(f"  Remapped {result.rowcount} rows in {table}: {delete_id} -> {keep_id}")
                total_remapped += result.rowcount

    print(f"\n  Total rows remapped: {total_remapped}")

    # Step 4: Delete duplicate batches
    print("\n=== Deleting Duplicate Batches ===")
    delete_ids = [d.delete_id for d in dupes]
    for did in delete_ids:
        db.execute(text("DELETE FROM batches WHERE id = :id"), {"id": did})
        print(f"  Deleted batch id={did}")

    # Step 5: Verify
    remaining = db.execute(text("""
        SELECT id, name FROM batches WHERE center_id = 3 AND active = true ORDER BY name
    """)).fetchall()

    print(f"\n=== Remaining Batches ({len(remaining)}) ===")
    for b in remaining:
        print(f"  ID: {b.id} | {b.name}")

    db.commit()
    print("\nDone! Changes committed successfully.")

except Exception as e:
    db.rollback()
    print(f"\nERROR: {e}")
    raise
finally:
    db.close()
