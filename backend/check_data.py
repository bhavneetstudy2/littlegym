"""Check current state of enrollment plans, attendance dates, and percentage logic."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# 1. Check enrollment plan_types and Duration info in notes
print("=" * 60)
print("1. ENROLLMENT PLAN TYPES")
print("=" * 60)
rows = db.execute(text("""
    SELECT plan_type, COUNT(*) as cnt
    FROM enrollments WHERE center_id = 3 AND is_archived = false
    GROUP BY plan_type ORDER BY cnt DESC
""")).fetchall()
for r in rows:
    print(f"  {r.plan_type}: {r.cnt}")

print("\n  Sample notes with Duration info:")
notes_rows = db.execute(text("""
    SELECT id, notes FROM enrollments
    WHERE center_id = 3 AND notes LIKE '%Duration%'
    LIMIT 10
""")).fetchall()
for r in notes_rows:
    print(f"  ID {r.id}: {r.notes}")

# Get unique durations
print("\n  Unique Duration values found:")
all_notes = db.execute(text("""
    SELECT DISTINCT notes FROM enrollments
    WHERE center_id = 3 AND notes LIKE '%Duration%'
""")).fetchall()
durations = set()
for r in all_notes:
    if r.notes:
        for part in r.notes.split(";"):
            if "Duration" in part:
                durations.add(part.strip())
for d in sorted(durations):
    print(f"    {d}")

# 2. Check attendance/session dates
print("\n" + "=" * 60)
print("2. ATTENDANCE SESSION DATES")
print("=" * 60)
date_range = db.execute(text("""
    SELECT MIN(cs.session_date) as earliest, MAX(cs.session_date) as latest, COUNT(*) as total
    FROM class_sessions cs WHERE cs.center_id = 3
""")).fetchone()
print(f"  Session date range: {date_range.earliest} to {date_range.latest}")
print(f"  Total sessions: {date_range.total}")

print("\n  Sample session dates (last 10):")
sample_dates = db.execute(text("""
    SELECT cs.session_date, b.name as batch_name, COUNT(a.id) as attendance_count
    FROM class_sessions cs
    JOIN batches b ON cs.batch_id = b.id
    LEFT JOIN attendance a ON a.class_session_id = cs.id
    WHERE cs.center_id = 3
    GROUP BY cs.session_date, b.name
    ORDER BY cs.session_date DESC
    LIMIT 15
""")).fetchall()
for r in sample_dates:
    print(f"  {r.session_date} | {r.batch_name} | {r.attendance_count} students")

# Check for today's dates specifically
from datetime import date
today = date.today()
today_count = db.execute(text("""
    SELECT COUNT(*) FROM class_sessions WHERE center_id = 3 AND session_date = :today
"""), {"today": today}).scalar()
print(f"\n  Sessions with today's date ({today}): {today_count}")

# 3. Check attendance percentage - how is visits_used vs visits_included
print("\n" + "=" * 60)
print("3. VISITS USED vs INCLUDED (Attendance %)")
print("=" * 60)
visit_data = db.execute(text("""
    SELECT e.id, c.first_name, e.visits_included, e.visits_used,
           (SELECT COUNT(*) FROM attendance a WHERE a.enrollment_id = e.id) as actual_attendance
    FROM enrollments e
    JOIN children c ON e.child_id = c.id
    WHERE e.center_id = 3 AND e.status = 'ACTIVE'
    ORDER BY e.visits_used DESC
    LIMIT 10
""")).fetchall()
for r in visit_data:
    pct = round(r.visits_used * 100 / r.visits_included, 1) if r.visits_included and r.visits_included > 0 else 0
    print(f"  {r.first_name}: used={r.visits_used}/{r.visits_included} ({pct}%), actual_attendance_rows={r.actual_attendance}")

db.close()
