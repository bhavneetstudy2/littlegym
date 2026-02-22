#!/usr/bin/env python3
"""Fix plan_type on enrollments using Duration column from Enrolled sheet."""
import os, sys, pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

CENTER_ID = 3
EXCEL_FILE = 'C:/Users/Administrator/Downloads/TLG Chandigarh (1).xlsx'

DURATION_MAP = {
    'quarterly': 'QUARTERLY',
    'quaterly': 'QUARTERLY',  # typo in Excel
    'monthly': 'MONTHLY',
    'one time': 'PAY_PER_VISIT',
    'semi-annually': 'CUSTOM',
    'annually': 'YEARLY',
}


def fix_plan_types():
    print("=" * 60)
    print("FIXING PLAN TYPES")
    print("=" * 60)

    db = SessionLocal()

    enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
    enrolled_df.rename(columns={' ': 'Enquiry ID'}, inplace=True)
    enrolled_df['Date'] = pd.to_datetime(enrolled_df['Date'], dayfirst=True, errors='coerce')

    # Build (eid, date_str) -> plan_type from Excel
    excel_plan = {}
    for idx, row in enrolled_df.iterrows():
        eid = str(row.get('Enquiry ID', '')).strip()
        date_val = row.get('Date')
        duration = str(row.get('Duration', '')).strip().lower() if pd.notna(row.get('Duration')) else ''
        if eid and eid != 'nan' and pd.notna(date_val) and duration:
            date_str = str(date_val.date())
            plan_type = DURATION_MAP.get(duration, 'CUSTOM')
            excel_plan[(eid, date_str)] = plan_type

    print(f"Excel enrollment->plan mappings: {len(excel_plan)}")

    enrollments = db.execute(text('''
        SELECT e.id, c.enquiry_id, e.start_date, e.plan_type
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        WHERE e.center_id = :cid
    '''), {'cid': CENTER_ID}).fetchall()

    fixed = 0
    already_correct = 0
    no_match = 0

    for e in enrollments:
        eid = str(e[1]).strip()
        date_str = str(e[2])
        current_type = e[3]
        excel_type = excel_plan.get((eid, date_str))
        if excel_type:
            if current_type != excel_type:
                db.execute(text('UPDATE enrollments SET plan_type = :pt WHERE id = :eid'),
                           {'pt': excel_type, 'eid': e[0]})
                fixed += 1
            else:
                already_correct += 1
        else:
            no_match += 1

    db.commit()

    print(f"Fixed plan_type: {fixed}")
    print(f"Already correct: {already_correct}")
    print(f"No Excel match: {no_match}")

    print()
    print("Plan type distribution after fix:")
    rows = db.execute(text('''
        SELECT plan_type, COUNT(*) FROM enrollments WHERE center_id = :cid
        GROUP BY plan_type ORDER BY COUNT(*) DESC
    '''), {'cid': CENTER_ID}).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

    # Verify TLGC0078
    print()
    result = db.execute(text('''
        SELECT e.plan_type, e.start_date, e.visits_included, e.status
        FROM enrollments e JOIN children c ON e.child_id = c.id
        WHERE c.enquiry_id = 'TLGC0078' AND e.center_id = :cid
    '''), {'cid': CENTER_ID}).fetchall()
    print("TLGC0078 after fix:")
    for r in result:
        print(f"  {r[1]} | {r[0]} | {r[2]} classes | {r[3]}")

    db.close()


if __name__ == '__main__':
    fix_plan_types()
