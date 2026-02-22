"""
Import Chandigarh data from Excel to Render PostgreSQL database.
Comprehensive import covering all sheets with proper deduplication.
"""
import pandas as pd
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import re

# Database connection
TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3  # Chandigarh center

engine = create_engine(TARGET_DB)
Session = sessionmaker(bind=engine)
db = Session()

# Tracking
stats = {
    'children': 0,
    'parents': 0,
    'family_links': 0,
    'leads': 0,
    'intro_visits': 0,
    'batches': 0,
    'enrollments': 0,
    'payments': 0,
    'attendance': 0,
    'skills': 0,
    'skill_progress': 0,
    'errors': []
}

def clean_phone(phone):
    """Clean and format phone number"""
    if pd.isna(phone):
        return None
    phone = str(phone).strip()
    # Remove all non-digits
    phone = re.sub(r'[^\d+]', '', phone)
    if not phone:
        return None
    # Ensure it starts with +91
    if not phone.startswith('+'):
        phone = '+91-' + phone.lstrip('91')
    return phone[:20] if phone else None

def parse_date(date_val):
    """Parse date from various formats"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, (datetime, date)):
        return date_val if isinstance(date_val, date) else date_val.date()
    try:
        return pd.to_datetime(date_val, dayfirst=True).date()
    except:
        return None

def parse_gender(gender_val):
    """Parse gender to Boy/Girl/Other"""
    if pd.isna(gender_val):
        return None
    gender = str(gender_val).strip().lower()
    if gender in ['m', 'male', 'boy']:
        return 'Boy'
    elif gender in ['f', 'female', 'girl']:
        return 'Girl'
    return 'Other'

def calculate_dob_from_age(age, reference_date=None):
    """Calculate approximate DOB from age"""
    if pd.isna(age):
        return None
    try:
        age = int(float(age))
        ref = reference_date or date.today()
        return date(ref.year - age, ref.month, ref.day)
    except:
        return None

print("=" * 80)
print("CHANDIGARH DATA IMPORT - Starting...")
print("=" * 80)

# Step 1: Build master children registry
print("\nStep 1: Building master children registry...")
print("-" * 80)

enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')
iv_df = pd.read_excel(EXCEL_FILE, sheet_name='IV')
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
tracker_df = pd.read_excel(EXCEL_FILE, sheet_name='Tracker')

master_children = {}

# Helper to add child to master registry
def add_to_master(enquiry_id, child_name, last_name, parent_name, contact, email, age, gender, school, dob, source_sheet, enquiry_date=None, remarks=None, expectations=None):
    """Add child to master registry, merging data from multiple sources"""

    if not enquiry_id:
        return

    if enquiry_id not in master_children:
        master_children[enquiry_id] = {
            'enquiry_id': enquiry_id,
            'child_first_name': None,
            'child_last_name': None,
            'parent_name': None,
            'contact': None,
            'email': None,
            'age': None,
            'gender': None,
            'school': None,
            'dob': None,
            'enquiry_date': None,
            'remarks': None,
            'expectations': None,
            'sources': []
        }

    child = master_children[enquiry_id]
    child['sources'].append(source_sheet)

    # Merge data - prefer non-null values
    if child_name and not child['child_first_name']:
        child['child_first_name'] = str(child_name).strip()
    if last_name and not child['child_last_name']:
        child['child_last_name'] = str(last_name).strip()
    if parent_name and not child['parent_name']:
        child['parent_name'] = str(parent_name).strip()
    if contact and not child['contact']:
        child['contact'] = clean_phone(contact)
    if email and not child['email']:
        child['email'] = str(email).strip() if pd.notna(email) else None
    if age and not child['age']:
        try:
            # Handle cases like "3+", "4-5", etc
            age_str = str(age).strip().replace('+', '').replace('-', '').split()[0]
            child['age'] = int(float(age_str)) if age_str else None
        except:
            child['age'] = None
    if gender and not child['gender']:
        child['gender'] = parse_gender(gender)
    if school and not child['school']:
        child['school'] = str(school).strip()
    if dob and not child['dob']:
        child['dob'] = parse_date(dob)
    if enquiry_date and not child['enquiry_date']:
        child['enquiry_date'] = parse_date(enquiry_date)
    if remarks:
        if child['remarks']:
            child['remarks'] += ' | ' + str(remarks)
        else:
            child['remarks'] = str(remarks)
    if expectations and not child['expectations']:
        child['expectations'] = str(expectations)

# Process Enquiry sheet
print("Processing Enquiry sheet...")
for idx, row in enquiry_df.iterrows():
    enquiry_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
        continue

    add_to_master(
        enquiry_id=enquiry_id,
        child_name=row.get('Child Name'),
        last_name=row.get('Last Name'),
        parent_name=row.get('Parent Name'),
        contact=row.get('Contact Number'),
        email=row.get('Email'),
        age=row.get('Age'),
        gender=row.get('Gender'),
        school=row.get('School'),
        dob=row.get('Birthday'),
        enquiry_date=row.get('Enquiry Date'),
        remarks=row.get('Remarks'),
        expectations=row.get('Expectations'),
        source_sheet='Enquiry'
    )

print(f"  Enquiry sheet: {len([k for k,v in master_children.items() if 'Enquiry' in v['sources']])} children")

# Process IV sheet
print("Processing IV sheet...")
for idx, row in iv_df.iterrows():
    enquiry_id = str(row['f']).strip() if pd.notna(row['f']) else None
    child_name = row.get('Child Name')

    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
        # No ID - assign new one
        if pd.notna(child_name):
            enquiry_id = f"TLGC-IV-{idx:03d}"

    if enquiry_id and pd.notna(child_name):
        add_to_master(
            enquiry_id=enquiry_id,
            child_name=child_name,
            last_name=None,
            parent_name=None,
            contact=row.get('Contact Number'),
            email=None,
            age=None,
            gender=None,
            school=None,
            dob=None,
            remarks=row.get('Remarks'),
            expectations=None,
            source_sheet='IV'
        )

print(f"  IV sheet: {len([k for k,v in master_children.items() if 'IV' in v['sources']])} children")

# Process Enrolled sheet
print("Processing Enrolled sheet...")
for idx, row in enrolled_df.iterrows():
    enquiry_id = str(row['Enquiry ID']).strip() if pd.notna(row['Enquiry ID']) else None
    child_name = row.get('Child Name')

    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan' or enquiry_id == ' ':
        if pd.notna(child_name):
            enquiry_id = f"TLGC-EN-{idx:03d}"

    if enquiry_id and pd.notna(child_name):
        add_to_master(
            enquiry_id=enquiry_id,
            child_name=child_name,
            last_name=None,
            parent_name=None,
            contact=None,
            email=None,
            age=None,
            gender=None,
            school=None,
            dob=None,
            source_sheet='Enrolled',
            remarks=None,
            expectations=None
        )

print(f"  Enrolled sheet: {len([k for k,v in master_children.items() if 'Enrolled' in v['sources']])} children")

# Process Expired sheet
print("Processing Expired sheet...")
for idx, row in expired_df.iterrows():
    enquiry_id = str(row['Enquiry ID']).strip() if pd.notna(row['Enquiry ID']) else None
    child_name = row.get('Child Name')

    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
        if pd.notna(child_name):
            enquiry_id = f"TLGC-EX-{idx:03d}"

    if enquiry_id and pd.notna(child_name):
        add_to_master(
            enquiry_id=enquiry_id,
            child_name=child_name,
            last_name=None,
            parent_name=None,
            contact=None,
            email=None,
            age=None,
            gender=None,
            school=None,
            dob=None,
            source_sheet='Expired',
            remarks=None,
            expectations=None
        )

print(f"  Expired sheet: {len([k for k,v in master_children.items() if 'Expired' in v['sources']])} children")

# Process Tracker sheet
print("Processing Tracker sheet...")
for idx, row in tracker_df.iterrows():
    enquiry_id = str(row['Enquiry ID']).strip() if pd.notna(row['Enquiry ID']) else None
    child_name = row.get('Child Name')

    if not enquiry_id or enquiry_id == '' or enquiry_id == 'nan':
        if pd.notna(child_name):
            enquiry_id = f"TLGC-TR-{idx:03d}"

    if enquiry_id and pd.notna(child_name):
        add_to_master(
            enquiry_id=enquiry_id,
            child_name=child_name,
            last_name=None,
            parent_name=None,
            contact=None,
            email=None,
            age=None,
            gender=None,
            school=None,
            dob=None,
            source_sheet='Tracker',
            remarks=None,
            expectations=row.get('Parent expectation')
        )

print(f"  Tracker sheet: {len([k for k,v in master_children.items() if 'Tracker' in v['sources']])} children")

print(f"\nOK Total unique children in master registry: {len(master_children)}")

# Note: Using age_years field directly instead of calculating DOB from age
# DOB will be calculated on-the-fly in the application when needed

print("\nMaster registry built successfully!")
print(f"Ready to import {len(master_children)} children to database")

db.close()
print("\nScript prepared. Run next phase to insert into database.")
