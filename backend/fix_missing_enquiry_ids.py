"""
Fix script to:
1. Assign TLGC IDs to 25 children with NULL enquiry_id
2. Fix child 245 with enquiry_id = 'nan' string
3. Fix child 443 with date string as first_name
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Step 1: Get current max TLGC number
    result = conn.execute(text(
        "SELECT MAX(enquiry_id) FROM children WHERE enquiry_id LIKE 'TLGC%'"
    )).scalar()

    if result:
        current_max = int(result.replace('TLGC', ''))
    else:
        current_max = 0

    print(f"Current max enquiry_id: TLGC{current_max:04d}")

    # Step 2: Fix child 245 - 'nan' string -> will get a TLGC ID
    nan_child = conn.execute(text(
        "SELECT id, first_name FROM children WHERE enquiry_id = 'nan'"
    )).fetchone()

    if nan_child:
        current_max += 1
        new_id = f"TLGC{current_max:04d}"
        conn.execute(text(
            "UPDATE children SET enquiry_id = :eid WHERE id = :cid"
        ), {"eid": new_id, "cid": nan_child[0]})
        print(f"Fixed child {nan_child[0]} ({nan_child[1]}): 'nan' -> {new_id}")

    # Step 3: Fix all children with NULL enquiry_id
    null_children = conn.execute(text(
        "SELECT id, first_name, last_name FROM children WHERE enquiry_id IS NULL ORDER BY id"
    )).fetchall()

    print(f"\nAssigning TLGC IDs to {len(null_children)} children with NULL enquiry_id:")

    for child in null_children:
        current_max += 1
        new_id = f"TLGC{current_max:04d}"
        conn.execute(text(
            "UPDATE children SET enquiry_id = :eid WHERE id = :cid"
        ), {"eid": new_id, "cid": child[0]})
        name = f"{child[1]} {child[2]}" if child[2] else child[1]
        print(f"  Child {child[0]:>4d} ({name:<30s}) -> {new_id}")

    # Step 4: Fix child 443 - date string as first_name
    # The DOB is 2021-03-01, which was also put in first_name
    # We don't know the real name, so mark it for review
    child_443 = conn.execute(text(
        "SELECT id, first_name, dob FROM children WHERE id = 443"
    )).fetchone()

    if child_443 and '2021-03-01' in str(child_443[1]):
        conn.execute(text(
            "UPDATE children SET first_name = :name WHERE id = 443"
        ), {"name": "UNKNOWN (needs review)"})
        print(f"\nFixed child 443: first_name '{child_443[1]}' -> 'UNKNOWN (needs review)'")

    conn.commit()

    # Step 5: Verify
    print("\n--- Verification ---")
    remaining_null = conn.execute(text(
        "SELECT COUNT(*) FROM children WHERE enquiry_id IS NULL"
    )).scalar()
    remaining_nan = conn.execute(text(
        "SELECT COUNT(*) FROM children WHERE enquiry_id = 'nan'"
    )).scalar()
    new_max = conn.execute(text(
        "SELECT MAX(enquiry_id) FROM children WHERE enquiry_id LIKE 'TLGC%'"
    )).scalar()
    child_443_check = conn.execute(text(
        "SELECT first_name FROM children WHERE id = 443"
    )).scalar()

    print(f"Children with NULL enquiry_id: {remaining_null}")
    print(f"Children with 'nan' enquiry_id: {remaining_nan}")
    print(f"New max enquiry_id: {new_max}")
    print(f"Child 443 first_name: {child_443_check}")
    print("\nAll fixes applied successfully!")
