#!/usr/bin/env python3
"""
Import Intro Visit (IV) data from Excel IV sheet.
- Match by Enquiry ID to find child + lead
- Create intro_visits records with scheduled/attended dates
- Update lead status based on IV outcome
- For already-CONVERTED leads, just add the IV record (don't change status)
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

# IV Status -> lead status mapping
# Only applied if lead is NOT already CONVERTED
STATUS_MAP = {
    'IV Completed': 'IV_COMPLETED',
    'Enrolled': 'CONVERTED',
    'Not Interested': 'CLOSED_LOST',
    'Pending': 'IV_SCHEDULED',
    'IV Scheduled': 'IV_SCHEDULED',
    'Follow Up': 'FOLLOW_UP_PENDING',
}

# IV Status -> outcome mapping
OUTCOME_MAP = {
    'IV Completed': 'INTERESTED_ENROLL_LATER',
    'Enrolled': 'INTERESTED_ENROLL_NOW',
    'Not Interested': 'NOT_INTERESTED',
    'Pending': None,
    'IV Scheduled': None,
    'Follow Up': 'INTERESTED_ENROLL_LATER',
}


def import_iv():
    print("=" * 60)
    print("IMPORTING INTRO VISIT DATA")
    print("=" * 60)

    db = SessionLocal()

    try:
        iv_df = pd.read_excel(EXCEL_FILE, sheet_name='IV')
        # 'f' column is the Enquiry ID
        iv_df['IV Date'] = pd.to_datetime(iv_df['IV Date'], dayfirst=True, errors='coerce')

        # Also read Enquiry sheet for enquiry dates (fallback for missing IV Date)
        eq_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
        eq_df.rename(columns={' ': 'Enquiry ID'}, inplace=True)
        eq_df['Enquiry Date'] = pd.to_datetime(eq_df['Enquiry Date'], dayfirst=True, errors='coerce')
        enquiry_dates = {}
        for idx, row in eq_df.iterrows():
            eid = str(row.get('Enquiry ID', '')).strip()
            if eid and eid != 'nan' and pd.notna(row.get('Enquiry Date')):
                enquiry_dates[eid] = row['Enquiry Date']

        # Build batch name -> id map
        batches = db.execute(text(
            'SELECT id, name FROM batches WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        batch_map = {b[1]: b[0] for b in batches}
        print(f"Batch map: {batch_map}")

        # Build enquiry_id -> child_id map
        children = db.execute(text(
            'SELECT id, enquiry_id FROM children WHERE center_id = :cid'
        ), {'cid': CENTER_ID}).fetchall()
        child_map = {str(c[1]).strip(): c[0] for c in children if c[1]}

        # Build child_id -> lead_id map (+ lead status)
        leads = db.execute(text('''
            SELECT l.id, l.child_id, l.status, c.enquiry_id
            FROM leads l
            JOIN children c ON l.child_id = c.id
            WHERE l.center_id = :cid
        '''
        ), {'cid': CENTER_ID}).fetchall()
        lead_by_eid = {str(l[3]).strip(): {'lead_id': l[0], 'child_id': l[1], 'status': l[2]} for l in leads}

        # Check existing intro_visits to avoid duplicates
        existing_ivs = db.execute(text('''
            SELECT lead_id, scheduled_at FROM intro_visits WHERE center_id = :cid
        '''), {'cid': CENTER_ID}).fetchall()
        existing_iv_set = {(e[0], str(e[1])[:10]) for e in existing_ivs}
        print(f"Existing IVs: {len(existing_iv_set)}")

        created_ivs = 0
        updated_leads = 0
        created_leads = 0
        skipped_dup = 0
        no_child = 0
        skipped_empty = 0

        for idx, row in iv_df.iterrows():
            eid = str(row.get('f', '')).strip()
            if not eid or eid == 'nan':
                skipped_empty += 1
                continue

            child_name = str(row.get('Child Name', '')).strip()
            status = str(row.get('Status', '')).strip()
            iv_date = row.get('IV Date')
            batch_name = str(row.get('Batch', '')).strip() if pd.notna(row.get('Batch')) else ''
            remarks = str(row.get('Remarks', '')).strip() if pd.notna(row.get('Remarks')) else ''

            # Get child_id
            child_id = child_map.get(eid)
            if not child_id:
                no_child += 1
                continue

            batch_id = batch_map.get(batch_name) if batch_name else None

            # Get or create lead
            lead_info = lead_by_eid.get(eid)
            if not lead_info:
                # Create lead
                result = db.execute(text('''
                    INSERT INTO leads (
                        center_id, child_id, status, source,
                        created_by_id, updated_by_id, created_at, updated_at, is_archived
                    ) VALUES (
                        :cid, :child_id, 'ENQUIRY_RECEIVED', 'WALK_IN',
                        :admin_id, :admin_id, NOW(), NOW(), false
                    ) RETURNING id
                '''), {
                    'cid': CENTER_ID,
                    'child_id': child_id,
                    'admin_id': ADMIN_USER_ID,
                })
                lead_id = result.fetchone()[0]
                lead_info = {'lead_id': lead_id, 'child_id': child_id, 'status': 'ENQUIRY_RECEIVED'}
                lead_by_eid[eid] = lead_info
                created_leads += 1

            lead_id = lead_info['lead_id']
            current_lead_status = lead_info['status']

            # Determine scheduled_at
            if pd.notna(iv_date):
                scheduled_at = iv_date.to_pydatetime() if isinstance(iv_date, pd.Timestamp) else iv_date
            else:
                # Use enquiry date as fallback
                eq_date = enquiry_dates.get(eid)
                if eq_date and pd.notna(eq_date):
                    scheduled_at = eq_date.to_pydatetime() if isinstance(eq_date, pd.Timestamp) else eq_date
                else:
                    scheduled_at = datetime(2025, 4, 15)  # Default fallback

            # Check for duplicate
            date_str = str(scheduled_at)[:10]
            if (lead_id, date_str) in existing_iv_set:
                skipped_dup += 1
                continue

            # Determine attended_at
            attended_at = None
            if status in ('IV Completed', 'Enrolled', 'Follow Up'):
                attended_at = scheduled_at

            # Determine outcome
            outcome = OUTCOME_MAP.get(status)

            # Create intro_visit record
            db.execute(text('''
                INSERT INTO intro_visits (
                    center_id, lead_id, scheduled_at, attended_at,
                    batch_id, outcome, outcome_notes,
                    created_by_id, updated_by_id, created_at, updated_at, is_archived
                ) VALUES (
                    :cid, :lead_id, :scheduled_at, :attended_at,
                    :batch_id, :outcome, :notes,
                    :admin_id, :admin_id, NOW(), NOW(), false
                )
            '''), {
                'cid': CENTER_ID,
                'lead_id': lead_id,
                'scheduled_at': scheduled_at,
                'attended_at': attended_at,
                'batch_id': batch_id,
                'outcome': outcome,
                'notes': remarks if remarks else None,
                'admin_id': ADMIN_USER_ID,
            })
            created_ivs += 1
            existing_iv_set.add((lead_id, date_str))

            # Update lead status (only if not already CONVERTED)
            if current_lead_status != 'CONVERTED':
                new_status = STATUS_MAP.get(status)
                if new_status and new_status != current_lead_status:
                    update_fields = {'status': new_status, 'lid': lead_id}
                    sql = 'UPDATE leads SET status = :status WHERE id = :lid'
                    if new_status == 'CLOSED_LOST' and remarks:
                        sql = 'UPDATE leads SET status = :status, closed_reason = :reason WHERE id = :lid'
                        update_fields['reason'] = remarks
                    elif new_status == 'CONVERTED':
                        sql = 'UPDATE leads SET status = :status, converted_at = :conv_at WHERE id = :lid'
                        update_fields['conv_at'] = scheduled_at.date() if hasattr(scheduled_at, 'date') else scheduled_at
                    db.execute(text(sql), update_fields)
                    lead_info['status'] = new_status
                    updated_leads += 1

        db.commit()

        print()
        print(f"[DONE] Created {created_ivs} intro visit records")
        print(f"  Created {created_leads} new leads (had no lead)")
        print(f"  Updated {updated_leads} lead statuses")
        print(f"  Skipped duplicates: {skipped_dup}")
        print(f"  No child in DB: {no_child}")
        print(f"  Skipped empty: {skipped_empty}")

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

    iv_count = db.execute(text(
        'SELECT COUNT(*) FROM intro_visits WHERE center_id = :cid'
    ), {'cid': CENTER_ID}).scalar()
    print(f"Total intro visits: {iv_count}")

    # By outcome
    print()
    print("IVs by outcome:")
    rows = db.execute(text('''
        SELECT COALESCE(outcome, 'PENDING'), COUNT(*)
        FROM intro_visits WHERE center_id = :cid
        GROUP BY outcome ORDER BY COUNT(*) DESC
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    # Lead status distribution
    print()
    print("Lead status distribution after IV import:")
    rows = db.execute(text('''
        SELECT status, COUNT(*) FROM leads WHERE center_id = :cid
        GROUP BY status ORDER BY COUNT(*) DESC
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    # IV by batch
    print()
    print("IVs by batch:")
    rows = db.execute(text('''
        SELECT COALESCE(b.name, 'No batch'), COUNT(*)
        FROM intro_visits iv
        LEFT JOIN batches b ON iv.batch_id = b.id
        WHERE iv.center_id = :cid
        GROUP BY b.name ORDER BY COUNT(*) DESC
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    db.close()


if __name__ == '__main__':
    import_iv()
    verify()
