"""
Check admin users and their details
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("="*70)
print("ADMIN USERS")
print("="*70)

users = db.execute(text("""
    SELECT id, name, email, role, center_id, status
    FROM users
    WHERE role IN ('SUPER_ADMIN', 'CENTER_ADMIN')
    ORDER BY role, id
""")).fetchall()

print(f"\nFound {len(users)} admin users:\n")

for u in users:
    center = " (All centers)" if u.center_id is None else f" (Center {u.center_id})"
    status = " [ACTIVE]" if u.status == "active" else f" [{u.status.upper()}]"
    print(f"ID: {u.id} | {u.name} | {u.email}")
    print(f"  Role: {u.role}{center}{status}")
    print()

# Show Chandigarh center admin
print("="*70)
print("Chandigarh Center Details:")
print("="*70)

chandigarh = db.execute(text("""
    SELECT id, name, city
    FROM centers
    WHERE name ILIKE '%chandigarh%'
""")).fetchone()

if chandigarh:
    print(f"\nCenter ID: {chandigarh.id}")
    print(f"Name: {chandigarh.name}")
    print(f"City: {chandigarh.city}")

    # Find admin for this center
    center_admin = db.execute(text("""
        SELECT id, name, email, role
        FROM users
        WHERE center_id = :cid AND role = 'CENTER_ADMIN'
    """), {"cid": chandigarh.id}).fetchone()

    if center_admin:
        print(f"\nCenter Admin:")
        print(f"  {center_admin.name} ({center_admin.email})")
    else:
        print("\n[WARNING] No center admin found for Chandigarh!")

db.close()
print("\n" + "="*70)
print("Default credentials: email=admin@littlegym.com, password=admin123")
print("="*70)
