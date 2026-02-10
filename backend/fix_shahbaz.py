"""
Fix Shahbaz attendance count and verify visibility
"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
CHANDIGARH_CENTER_ID = 3

print("="*70)
print("Checking Shahbaz attendance records...")
print("="*70)

# Get Shahbaz's child ID
shahbaz = db.execute(text("""
    SELECT id FROM children WHERE center_id = :cid AND first_name ILIKE '%shahbaz%'
"""), {"cid": CHANDIGARH_CENTER_ID}).fetchone()

if shahbaz:
    child_id = shahbaz.id
    print(f"Shahbaz child_id: {child_id}")

    # Get Super Beasts batch id
    sb = db.execute(text("SELECT id FROM batches WHERE center_id = :cid AND name = 'Super Beasts'"),
                    {"cid": CHANDIGARH_CENTER_ID}).fetchone()
    sb_batch_id = sb.id if sb else None

    # Get Funny Bugs batch id
    fb = db.execute(text("SELECT id FROM batches WHERE center_id = :cid AND name = 'Funny Bugs'"),
                    {"cid": CHANDIGARH_CENTER_ID}).fetchone()
    fb_batch_id = fb.id if fb else None

    # Count attendance for Super Beasts
    print(f"\nSuper Beasts attendance (batch_id={sb_batch_id}):")
    sb_att = db.execute(text("""
        SELECT COUNT(*) as cnt FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.status = 'PRESENT' AND a.is_archived = false
    """), {"child": child_id, "bid": sb_batch_id}).fetchone()
    print(f"  Total: {sb_att.cnt}")

    # List actual attendance dates for Super Beasts
    dates = db.execute(text("""
        SELECT cs.session_date FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.status = 'PRESENT' AND a.is_archived = false
        ORDER BY cs.session_date
    """), {"child": child_id, "bid": sb_batch_id}).fetchall()
    print(f"  Dates: {[str(d.session_date) for d in dates]}")

    # Count attendance for Funny Bugs
    print(f"\nFunny Bugs attendance (batch_id={fb_batch_id}):")
    fb_att = db.execute(text("""
        SELECT COUNT(*) as cnt FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.status = 'PRESENT' AND a.is_archived = false
    """), {"child": child_id, "bid": fb_batch_id}).fetchone()
    print(f"  Total: {fb_att.cnt}")

    # List actual attendance dates for Funny Bugs
    dates = db.execute(text("""
        SELECT cs.session_date FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        WHERE a.child_id = :child AND cs.batch_id = :bid
          AND a.status = 'PRESENT' AND a.is_archived = false
        ORDER BY cs.session_date
    """), {"child": child_id, "bid": fb_batch_id}).fetchall()
    print(f"  Dates: {[str(d.session_date) for d in dates]}")

    # Check for attendance with wrong batch
    print("\nAll attendance for Shahbaz:")
    all_att = db.execute(text("""
        SELECT a.id, cs.session_date, cs.batch_id, b.name as batch_name
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN batches b ON cs.batch_id = b.id
        WHERE a.child_id = :child AND a.is_archived = false
        ORDER BY cs.session_date
    """), {"child": child_id}).fetchall()
    print(f"  Total records: {len(all_att)}")

db.close()
