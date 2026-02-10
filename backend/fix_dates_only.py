"""
Fix attendance dates: Jan/Feb = 2026, other months = 2025
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("FIXING ATTENDANCE DATES")
print("="*70)

# Check current date distribution
print("\nCurrent session date distribution:")
for r in db.execute(text("""
    SELECT EXTRACT(YEAR FROM session_date) as year,
           EXTRACT(MONTH FROM session_date) as month,
           COUNT(*) as count
    FROM class_sessions
    WHERE center_id = :cid
    GROUP BY EXTRACT(YEAR FROM session_date), EXTRACT(MONTH FROM session_date)
    ORDER BY year, month
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {int(r.year)}-{int(r.month):02d}: {r.count} sessions")

# Fix Jan/Feb 2025 -> 2026
result = db.execute(text("""
    UPDATE class_sessions
    SET session_date = session_date + INTERVAL '1 year'
    WHERE center_id = :cid
    AND EXTRACT(YEAR FROM session_date) = 2025
    AND EXTRACT(MONTH FROM session_date) IN (1, 2)
"""), {"cid": CHANDIGARH_CENTER_ID})
print(f"\nFixed {result.rowcount} sessions from Jan/Feb 2025 to 2026")

db.commit()

# Verify
print("\nAfter fix:")
for r in db.execute(text("""
    SELECT EXTRACT(YEAR FROM session_date) as year,
           EXTRACT(MONTH FROM session_date) as month,
           COUNT(*) as count
    FROM class_sessions
    WHERE center_id = :cid
    GROUP BY EXTRACT(YEAR FROM session_date), EXTRACT(MONTH FROM session_date)
    ORDER BY year, month
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchall():
    print(f"  {int(r.year)}-{int(r.month):02d}: {r.count} sessions")

db.close()
print("\nDone!")
