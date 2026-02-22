#!/usr/bin/env python3
"""
Import attendance data from Excel Attendance sheet into DB.
- Creates class_sessions for each unique (batch, date) combination
- Creates attendance records (PRESENT) for each child+date
- Links to active enrollment where possible
- Does NOT modify visits_used (already set during enrollment import)
"""
import os, sys, pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

CENTER_ID = 3
ADMIN_USER_ID = 1
EXCEL_FILE = 'C:/Users/Administrator/Downloads/TLG Chandigarh (1).xlsx'


def import_attendance():
    print("=" * 60)
    print("IMPORTING ATTENDANCE DATA")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Read Excel
        att_df = pd.read_excel(EXCEL_FILE, sheet_name='Attendance')
        att_df.rename(columns={' ': 'Enquiry ID'}, inplace=True)

        # Build batch name -> id map
        batches = db.execute(text(
            'SELECT id, name FROM batches WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        batch_map = {b[1]: b[0] for b in batches}
        print(f"Batches in DB: {batch_map}")

        # Build enquiry_id -> child_id map
        children = db.execute(text(
            'SELECT id, enquiry_id FROM children WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        child_map = {str(c[1]).strip(): c[0] for c in children if c[1]}
        print(f"Children in DB: {len(child_map)}")

        # Build child_id -> latest active enrollment_id map
        enrollments = db.execute(text('''
            SELECT e.id, e.child_id, e.batch_id, e.status
            FROM enrollments e
            WHERE e.center_id = :cid AND e.status = 'ACTIVE'
            ORDER BY e.start_date DESC
        '''), {'cid': CENTER_ID}).fetchall()
        # Map: child_id -> enrollment_id (latest active)
        enrollment_map = {}
        for e in enrollments:
            if e[1] not in enrollment_map:
                enrollment_map[e[1]] = e[0]
        print(f"Active enrollments: {len(enrollment_map)}")

        # Track created sessions: (batch_id, date_str) -> session_id
        session_cache = {}

        # Check existing sessions
        existing_sessions = db.execute(text('''
            SELECT id, batch_id, session_date FROM class_sessions WHERE center_id = :cid
        '''), {'cid': CENTER_ID}).fetchall()
        for s in existing_sessions:
            session_cache[(s[1], str(s[2]))] = s[0]
        print(f"Existing sessions: {len(session_cache)}")

        created_sessions = 0
        created_attendance = 0
        no_child = 0
        no_batch = 0
        skipped_nat = 0

        for idx, row in att_df.iterrows():
            eid = str(row.get('Enquiry ID', '')).strip()
            if not eid or eid == 'nan':
                continue

            batch_name = str(row.get('Batch', '')).strip()
            batch_id = batch_map.get(batch_name)
            if not batch_id:
                no_batch += 1
                continue

            child_id = child_map.get(eid)
            if not child_id:
                no_child += 1
                continue

            enrollment_id = enrollment_map.get(child_id)

            # Process each attendance date (columns 1-54)
            for col_num in range(1, 55):
                col_name = str(col_num)
                if col_name not in att_df.columns:
                    break

                val = row.get(col_name)
                if pd.isna(val):
                    continue

                # Parse the date
                if isinstance(val, pd.Timestamp):
                    att_date = val.date()
                elif isinstance(val, datetime):
                    att_date = val.date()
                else:
                    continue

                date_str = str(att_date)

                # Get or create class session
                session_key = (batch_id, date_str)
                if session_key not in session_cache:
                    result = db.execute(text('''
                        INSERT INTO class_sessions (
                            center_id, batch_id, session_date, status,
                            created_by_id, updated_by_id, created_at, updated_at, is_archived
                        ) VALUES (
                            :cid, :batch_id, :session_date, 'COMPLETED',
                            :admin_id, :admin_id, NOW(), NOW(), false
                        ) RETURNING id
                    '''), {
                        'cid': CENTER_ID,
                        'batch_id': batch_id,
                        'session_date': att_date,
                        'admin_id': ADMIN_USER_ID,
                    })
                    session_id = result.fetchone()[0]
                    session_cache[session_key] = session_id
                    created_sessions += 1
                else:
                    session_id = session_cache[session_key]

                # Create attendance record
                db.execute(text('''
                    INSERT INTO attendance (
                        center_id, class_session_id, child_id, enrollment_id,
                        status, marked_by_user_id, marked_at, notes,
                        created_by_id, updated_by_id, created_at, updated_at, is_archived
                    ) VALUES (
                        :cid, :session_id, :child_id, :enrollment_id,
                        'PRESENT', :admin_id, :marked_at, :notes,
                        :admin_id, :admin_id, NOW(), NOW(), false
                    )
                '''), {
                    'cid': CENTER_ID,
                    'session_id': session_id,
                    'child_id': child_id,
                    'enrollment_id': enrollment_id,
                    'marked_at': att_date,
                    'notes': 'Imported from Excel Attendance sheet',
                    'admin_id': ADMIN_USER_ID,
                })
                created_attendance += 1

        db.commit()

        print()
        print(f"[DONE] Created {created_sessions} class sessions")
        print(f"[DONE] Created {created_attendance} attendance records")
        print(f"  No child in DB: {no_child}")
        print(f"  No batch match: {no_batch}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def verify():
    print()
    print("=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    db = SessionLocal()

    # Total counts
    sessions = db.execute(text(
        'SELECT COUNT(*) FROM class_sessions WHERE center_id = :cid'
    ), {'cid': CENTER_ID}).scalar()
    attendance = db.execute(text(
        'SELECT COUNT(*) FROM attendance WHERE center_id = :cid'
    ), {'cid': CENTER_ID}).scalar()
    print(f"Total class sessions: {sessions}")
    print(f"Total attendance records: {attendance}")

    # Per batch
    print()
    print("Attendance by batch:")
    rows = db.execute(text('''
        SELECT b.name, COUNT(DISTINCT cs.id) as sessions, COUNT(a.id) as records
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN batches b ON cs.batch_id = b.id
        WHERE a.center_id = :cid
        GROUP BY b.name
        ORDER BY b.name
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} sessions, {r[2]} attendance records")

    # Sample: TLGC0002 (Mahira)
    print()
    print("=== Sample: TLGC0002 (Mahira) ===")
    rows = db.execute(text('''
        SELECT cs.session_date, b.name, a.status
        FROM attendance a
        JOIN class_sessions cs ON a.class_session_id = cs.id
        JOIN batches b ON cs.batch_id = b.id
        JOIN children c ON a.child_id = c.id
        WHERE c.enquiry_id = 'TLGC0002' AND a.center_id = :cid
        ORDER BY cs.session_date
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]}")
    print(f"  Total: {len(rows)}")

    db.close()


if __name__ == '__main__':
    import_attendance()
    verify()
