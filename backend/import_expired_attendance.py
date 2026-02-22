#!/usr/bin/env python3
"""
Import attendance data from Excel Expired sheet into DB.
Also fix wrongly-EXPIRED enrollments that have remaining classes per Attendance sheet.
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


def import_expired_attendance():
    print("=" * 60)
    print("IMPORTING ATTENDANCE FROM EXPIRED SHEET")
    print("=" * 60)

    db = SessionLocal()

    try:
        exp_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
        exp_df.rename(columns={' ': 'Enquiry ID'}, inplace=True)

        # Build batch name -> id map
        batches = db.execute(text(
            'SELECT id, name FROM batches WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        batch_map = {b[1]: b[0] for b in batches}
        # Map old batch names
        batch_map['Beasts'] = batch_map.get('Super Beasts', 15)
        batch_map['One Time'] = batch_map.get('Funny Bugs', 10)  # Map to closest
        print(f"Batch map: {batch_map}")

        # Build enquiry_id -> child_id map
        children = db.execute(text(
            'SELECT id, enquiry_id FROM children WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        child_map = {str(c[1]).strip(): c[0] for c in children if c[1]}

        # Build child_id -> enrollment_id map (any enrollment, prefer by batch)
        enrollments = db.execute(text('''
            SELECT e.id, e.child_id, e.batch_id, e.status, e.start_date
            FROM enrollments e
            WHERE e.center_id = :cid
            ORDER BY e.start_date DESC
        '''), {'cid': CENTER_ID}).fetchall()
        # Map: (child_id, batch_id) -> enrollment_id, fallback child_id -> enrollment_id
        enrollment_by_batch = {}
        enrollment_by_child = {}
        for e in enrollments:
            key = (e[1], e[2])
            if key not in enrollment_by_batch:
                enrollment_by_batch[key] = e[0]
            if e[1] not in enrollment_by_child:
                enrollment_by_child[e[1]] = e[0]

        # Track existing sessions
        existing_sessions = db.execute(text('''
            SELECT id, batch_id, session_date FROM class_sessions WHERE center_id = :cid
        '''), {'cid': CENTER_ID}).fetchall()
        session_cache = {(s[1], str(s[2])): s[0] for s in existing_sessions}
        print(f"Existing sessions: {len(session_cache)}")

        # Track existing attendance to avoid duplicates
        existing_att = db.execute(text('''
            SELECT class_session_id, child_id FROM attendance WHERE center_id = :cid
        '''), {'cid': CENTER_ID}).fetchall()
        existing_att_set = {(a[0], a[1]) for a in existing_att}
        print(f"Existing attendance records: {len(existing_att_set)}")

        created_sessions = 0
        created_attendance = 0
        skipped_duplicate = 0
        no_child = 0
        no_batch = 0
        bad_date = 0

        for idx, row in exp_df.iterrows():
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

            enrollment_id = enrollment_by_batch.get((child_id, batch_id)) or enrollment_by_child.get(child_id)

            # Process each attendance date (columns 1-54)
            for col_num in range(1, 55):
                val = row.get(col_num)
                if pd.isna(val):
                    continue

                # Parse the date
                att_date = None
                if isinstance(val, pd.Timestamp):
                    att_date = val.date()
                elif isinstance(val, datetime):
                    att_date = val.date()
                elif isinstance(val, str):
                    val = val.strip()
                    if val == '`' or not val:
                        continue
                    try:
                        att_date = pd.to_datetime(val, dayfirst=True).date()
                    except:
                        bad_date += 1
                        continue
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

                # Skip if attendance already exists for this child+session
                if (session_id, child_id) in existing_att_set:
                    skipped_duplicate += 1
                    continue

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
                    'notes': 'Imported from Excel Expired sheet',
                    'admin_id': ADMIN_USER_ID,
                })
                created_attendance += 1
                existing_att_set.add((session_id, child_id))

        db.commit()

        print()
        print(f"[DONE] Created {created_sessions} new class sessions")
        print(f"[DONE] Created {created_attendance} attendance records")
        print(f"  Skipped duplicates: {skipped_duplicate}")
        print(f"  No child in DB: {no_child}")
        print(f"  No batch match: {no_batch}")
        print(f"  Bad dates: {bad_date}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def fix_wrong_expired():
    """Fix enrollments that are EXPIRED but have remaining classes in Attendance sheet"""
    print()
    print("=" * 60)
    print("FIXING WRONGLY-EXPIRED ENROLLMENTS")
    print("=" * 60)

    db = SessionLocal()

    try:
        att_df = pd.read_excel(EXCEL_FILE, sheet_name='Attendance')
        att_df.rename(columns={' ': 'Enquiry ID'}, inplace=True)

        fixed = 0
        for idx, row in att_df.iterrows():
            eid = str(row.get('Enquiry ID', '')).strip()
            if not eid or eid == 'nan':
                continue

            remaining = row.get('Remaining Classes', 0)
            if pd.isna(remaining):
                remaining = 0
            remaining = int(float(remaining))
            if remaining <= 0:
                continue

            attended = row.get('Attended Classes', 0)
            booked = row.get('Booked Classes', 0)
            if pd.isna(attended): attended = 0
            if pd.isna(booked): booked = 0
            attended = int(float(attended))
            booked = int(float(booked))

            batch_name = str(row.get('Batch', '')).strip()

            # Check if latest enrollment for this child is EXPIRED
            result = db.execute(text('''
                SELECT e.id, e.status, e.visits_used, e.visits_included, b.name
                FROM enrollments e
                JOIN children c ON e.child_id = c.id
                LEFT JOIN batches b ON e.batch_id = b.id
                WHERE c.enquiry_id = :eid AND e.center_id = :cid
                ORDER BY e.start_date DESC
                LIMIT 1
            '''), {'eid': eid, 'cid': CENTER_ID}).fetchone()

            if result and result[1] == 'EXPIRED':
                db.execute(text('''
                    UPDATE enrollments
                    SET status = 'ACTIVE',
                        visits_used = :used,
                        visits_included = :included
                    WHERE id = :eid
                '''), {
                    'eid': result[0],
                    'used': attended,
                    'included': booked,
                })
                print(f"  Fixed {eid}: {result[4]} | {result[2]}/{result[3]} -> {attended}/{booked} ACTIVE")
                fixed += 1

        db.commit()
        print(f"\n[DONE] Fixed {fixed} wrongly-EXPIRED enrollments")

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

    sessions = db.execute(text(
        'SELECT COUNT(*) FROM class_sessions WHERE center_id = :cid'
    ), {'cid': CENTER_ID}).scalar()
    attendance = db.execute(text(
        'SELECT COUNT(*) FROM attendance WHERE center_id = :cid'
    ), {'cid': CENTER_ID}).scalar()
    print(f"Total class sessions: {sessions}")
    print(f"Total attendance records: {attendance}")

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

    print()
    print("ACTIVE enrollments by batch:")
    rows = db.execute(text('''
        SELECT b.name, COUNT(*)
        FROM enrollments e
        JOIN batches b ON e.batch_id = b.id
        WHERE e.center_id = :cid AND e.status = 'ACTIVE'
        GROUP BY b.name ORDER BY b.name
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    db.close()


if __name__ == '__main__':
    import_expired_attendance()
    fix_wrong_expired()
    verify()
