"""
Clean up duplicate children from double import.
Keep old records (with enquiry_id), delete new duplicates (with external_id).
Preserve new children that don't exist in old import.
"""
from sqlalchemy import create_engine, text

TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
engine = create_engine(TARGET_DB)

print("=" * 80)
print("CLEANUP DUPLICATE CHILDREN")
print("=" * 80)

with engine.begin() as conn:
    # Step 1: Find duplicate children IDs to delete
    print("\nStep 1: Identifying duplicate children...")
    result = conn.execute(text("""
        SELECT c2.id, c2.first_name, c2.external_id
        FROM children c1
        JOIN children c2 ON c1.enquiry_id = c2.external_id AND c1.id != c2.id
        WHERE c1.center_id = 3 AND c2.center_id = 3
        AND c1.enquiry_id IS NOT NULL
        AND c2.external_id IS NOT NULL
        ORDER BY c2.id
    """))

    duplicate_child_ids = [row[0] for row in result.fetchall()]
    print(f"Found {len(duplicate_child_ids)} duplicate children to delete")

    if duplicate_child_ids:
        # Step 2: Delete leads for duplicate children
        print("\nStep 2: Deleting leads for duplicate children...")
        result = conn.execute(
            text("DELETE FROM leads WHERE child_id = ANY(:ids) RETURNING id"),
            {"ids": duplicate_child_ids}
        )
        deleted_leads = result.rowcount
        print(f"Deleted {deleted_leads} leads")

        # Step 3: Delete family_links for duplicate children
        print("\nStep 3: Deleting family_links for duplicate children...")
        result = conn.execute(
            text("DELETE FROM family_links WHERE child_id = ANY(:ids) RETURNING id"),
            {"ids": duplicate_child_ids}
        )
        deleted_links = result.rowcount
        print(f"Deleted {deleted_links} family_links")

        # Step 4: Delete the duplicate children
        print("\nStep 4: Deleting duplicate children...")
        result = conn.execute(
            text("DELETE FROM children WHERE id = ANY(:ids) RETURNING id"),
            {"ids": duplicate_child_ids}
        )
        deleted_children = result.rowcount
        print(f"Deleted {deleted_children} children")

    # Step 5: Find NEW children that need enquiry_id updated
    print("\nStep 5: Finding new children to preserve...")
    result = conn.execute(text("""
        SELECT id, first_name, external_id
        FROM children
        WHERE center_id = 3
        AND external_id IS NOT NULL
        AND enquiry_id IS NULL
        AND external_id NOT IN (
            SELECT enquiry_id FROM children WHERE center_id = 3 AND enquiry_id IS NOT NULL
        )
        ORDER BY id
    """))

    new_children = result.fetchall()
    print(f"Found {len(new_children)} new children to preserve")

    # Step 6: Update enquiry_id for new children
    if new_children:
        print("\nStep 6: Updating enquiry_id for new children...")
        for child in new_children:
            conn.execute(
                text("UPDATE children SET enquiry_id = :external_id WHERE id = :id"),
                {"external_id": child[2], "id": child[0]}
            )
        print(f"Updated {len(new_children)} children")
        print("Sample new children:")
        for child in new_children[:5]:
            print(f"  ID: {child[0]}, Name: {child[1]}, Enquiry ID: {child[2]}")

    # Step 7: Clean up orphaned parents (no family_links)
    print("\nStep 7: Cleaning up orphaned parents...")
    result = conn.execute(text("""
        DELETE FROM parents
        WHERE center_id = 3
        AND id NOT IN (SELECT DISTINCT parent_id FROM family_links WHERE center_id = 3)
        AND created_at > '2026-02-21 17:00:00'
        RETURNING id
    """))
    deleted_parents = result.rowcount
    print(f"Deleted {deleted_parents} orphaned parents")

print("\n" + "=" * 80)
print("CLEANUP SUMMARY")
print("=" * 80)
print(f"Duplicate children deleted: {deleted_children if duplicate_child_ids else 0}")
print(f"Leads deleted: {deleted_leads if duplicate_child_ids else 0}")
print(f"Family links deleted: {deleted_links if duplicate_child_ids else 0}")
print(f"New children preserved: {len(new_children)}")
print(f"Orphaned parents deleted: {deleted_parents}")

# Final verification
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM children WHERE center_id = 3"))
    print(f"\nTotal children in center 3: {result.scalar()}")

    result = conn.execute(text("SELECT COUNT(*) FROM children WHERE center_id = 3 AND enquiry_id IS NOT NULL"))
    print(f"Children with enquiry_id: {result.scalar()}")

    result = conn.execute(text("SELECT COUNT(*) FROM children WHERE center_id = 3 AND external_id IS NOT NULL AND enquiry_id IS NULL"))
    print(f"Children with only external_id (should be 0): {result.scalar()}")

    result = conn.execute(text("SELECT COUNT(*) FROM leads WHERE center_id = 3"))
    print(f"Total leads in center 3: {result.scalar()}")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE!")
print("=" * 80)
