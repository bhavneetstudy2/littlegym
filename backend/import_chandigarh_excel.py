"""Import Chandigarh data from Excel file."""
import pandas as pd
import os
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy import create_engine
from app.models import (
    Center, User, Parent, Child, FamilyLink, Lead, IntroVisit,
    Batch, Enrollment, Payment, Discount, Attendance, ClassSession
)
from app.utils.enums import (
    LeadStatus, LeadSource, PlanType, EnrollmentStatus,
    PaymentMethod, AttendanceStatus
)
from app.core.security import get_password_hash
from app.core.database import SessionLocal

load_dotenv()

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
CHANDIGARH_CENTER_ID = 3

def parse_date(date_val):
    """Parse date from various formats."""
    if pd.isna(date_val) or date_val == '' or date_val == '-':
        return None

    if isinstance(date_val, (datetime, date)):
        return date_val if isinstance(date_val, date) else date_val.date()

    try:
        # Try parsing common formats
        if isinstance(date_val, str):
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_val, fmt).date()
                except:
                    continue
    except:
        pass

    return None


def clean_phone(phone):
    """Clean and format phone number."""
    if pd.isna(phone) or str(phone).strip() == '':
        return '+91-0000000000'

    phone = str(phone).strip()
    # Remove any non-digit characters except +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')

    if not phone.startswith('+'):
        if phone.startswith('91'):
            phone = '+' + phone
        elif phone.startswith('0'):
            phone = '+91-' + phone
        else:
            phone = '+91-' + phone

    return phone if phone else '+91-0000000000'


def import_enquiries(db, xls):
    """Import enquiries as leads."""
    print("\n=== Importing Enquiries (Leads) ===")
    df = pd.read_excel(xls, sheet_name='Enquiry')

    leads_created = 0
    children_created = 0
    parents_created = 0

    for idx, row in df.iterrows():
        try:
            # Skip if no child name
            if pd.isna(row.get('Child Name')) or str(row.get('Child Name')).strip() == '':
                continue

            child_first_name = str(row['Child Name']).strip()
            child_last_name = str(row.get('Last Name', '')).strip() if not pd.isna(row.get('Last Name')) else None

            # Create child
            child = Child(
                center_id=CHANDIGARH_CENTER_ID,
                first_name=child_first_name,
                last_name=child_last_name if child_last_name else None,
                dob=parse_date(row.get('Birthday')),
                school=str(row.get('School', '')).strip() if not pd.isna(row.get('School')) else None,
                notes=str(row.get('Remarks', '')).strip() if not pd.isna(row.get('Remarks')) else None,
                created_by_id=6,  # Super Admin
                updated_by_id=6
            )
            db.add(child)
            db.flush()
            children_created += 1

            # Create parent
            parent_name = str(row.get('Parent Name', f'Parent of {child_first_name}')).strip()
            parent_phone = clean_phone(row.get('Contact Number'))
            parent_email = str(row.get('Email', '')).strip() if not pd.isna(row.get('Email')) else None

            parent = Parent(
                center_id=CHANDIGARH_CENTER_ID,
                name=parent_name,
                phone=parent_phone,
                email=parent_email if parent_email and '@' in parent_email else None,
                created_by_id=6,
                updated_by_id=6
            )
            db.add(parent)
            db.flush()
            parents_created += 1

            # Create family link
            family_link = FamilyLink(
                center_id=CHANDIGARH_CENTER_ID,
                child_id=child.id,
                parent_id=parent.id,
                relationship_type='guardian',
                is_primary_contact=True,
                created_by_id=6,
                updated_by_id=6
            )
            db.add(family_link)

            # Determine lead source
            source_str = str(row.get('Source', '')).upper().strip()
            source_mapping = {
                'WALK IN': LeadSource.WALK_IN,
                'WALKIN': LeadSource.WALK_IN,
                'WALK-IN': LeadSource.WALK_IN,
                'GOOGLE': LeadSource.GOOGLE,
                'INSTAGRAM': LeadSource.INSTAGRAM,
                'FACEBOOK': LeadSource.FACEBOOK,
                'REFERRAL': LeadSource.REFERRAL,
                'WHATSAPP': LeadSource.WHATSAPP,
            }
            source = source_mapping.get(source_str, LeadSource.WALK_IN)

            # Create lead
            lead = Lead(
                center_id=CHANDIGARH_CENTER_ID,
                child_id=child.id,
                status=LeadStatus.DISCOVERY,
                source=source,
                discovery_notes=str(row.get('Expectations', '')).strip() if not pd.isna(row.get('Expectations')) else None,
                created_by_id=6,
                updated_by_id=6
            )
            db.add(lead)
            leads_created += 1

        except Exception as e:
            print(f"Error importing enquiry row {idx}: {str(e)}")
            continue

    db.commit()
    print(f"[OK] Created {children_created} children")
    print(f"[OK] Created {parents_created} parents")
    print(f"[OK] Created {leads_created} leads")


def import_batches(db):
    """Create standard batches for Chandigarh."""
    print("\n=== Creating Batches ===")

    batches_data = [
        {"name": "Giggle Worms", "age_min": 1, "age_max": 2, "days": ["Tue", "Thu"], "start_time": "10:00", "end_time": "11:00", "capacity": 8},
        {"name": "Funny Bugs", "age_min": 2, "age_max": 3, "days": ["Mon", "Wed", "Fri"], "start_time": "10:00", "end_time": "11:00", "capacity": 10},
        {"name": "Good Friends", "age_min": 3, "age_max": 4, "days": ["Mon", "Wed", "Fri"], "start_time": "11:00", "end_time": "12:00", "capacity": 12},
        {"name": "Super Beasts", "age_min": 4, "age_max": 6, "days": ["Mon", "Wed", "Fri"], "start_time": "14:00", "end_time": "15:00", "capacity": 12},
        {"name": "Grade School", "age_min": 6, "age_max": 12, "days": ["Sat", "Sun"], "start_time": "09:00", "end_time": "10:00", "capacity": 15},
    ]

    for batch_data in batches_data:
        batch = Batch(
            center_id=CHANDIGARH_CENTER_ID,
            name=batch_data["name"],
            age_min=batch_data["age_min"],
            age_max=batch_data["age_max"],
            days_of_week=batch_data["days"],
            start_time=batch_data["start_time"],
            end_time=batch_data["end_time"],
            capacity=batch_data["capacity"],
            active=True,
            created_by_id=6,
            updated_by_id=6
        )
        db.add(batch)

    db.commit()
    print(f"[OK] Created {len(batches_data)} batches")


def import_enrollments(db, xls):
    """Import enrolled students."""
    print("\n=== Importing Enrollments ===")
    df = pd.read_excel(xls, sheet_name='Enrolled')

    # Get batches for mapping
    batches = {batch.name: batch.id for batch in db.query(Batch).filter(Batch.center_id == CHANDIGARH_CENTER_ID).all()}

    enrollments_created = 0
    payments_created = 0

    for idx, row in df.iterrows():
        try:
            # Skip if no child name
            if pd.isna(row.get('Child Name')) or str(row.get('Child Name')).strip() == '':
                continue

            child_name = str(row['Child Name']).strip()

            # Find child by name
            child = db.query(Child).filter(
                Child.center_id == CHANDIGARH_CENTER_ID,
                Child.first_name.ilike(f'%{child_name}%')
            ).first()

            if not child:
                print(f"  ! Child not found: {child_name}")
                continue

            # Get or default batch
            batch_name = str(row.get('Batch', '')).strip()
            batch_id = batches.get(batch_name)

            # Parse enrollment details
            booked_classes = int(row.get('Booked Classes', 0)) if not pd.isna(row.get('Booked Classes')) else 24
            total_amount = float(row.get('Total Amount', 0)) if not pd.isna(row.get('Total Amount')) else 0
            paid_amount = float(row.get('Paid Amount', 0)) if not pd.isna(row.get('Paid Amount')) else 0

            # Determine status
            status_str = str(row.get('Status', 'Active')).strip().upper()
            status = EnrollmentStatus.ACTIVE if 'ACTIVE' in status_str else EnrollmentStatus.EXPIRED

            # Create enrollment
            enrollment = Enrollment(
                center_id=CHANDIGARH_CENTER_ID,
                child_id=child.id,
                batch_id=batch_id,
                plan_type=PlanType.CUSTOM,
                start_date=parse_date(row.get('Date')) or date.today(),
                end_date=None,
                visits_included=booked_classes,
                visits_used=0,
                days_selected=[],
                status=status,
                notes=None,
                created_by_id=6,
                updated_by_id=6
            )
            db.add(enrollment)
            db.flush()
            enrollments_created += 1

            # Create payment if amount exists
            if paid_amount > 0:
                payment = Payment(
                    center_id=CHANDIGARH_CENTER_ID,
                    enrollment_id=enrollment.id,
                    amount=paid_amount,
                    currency='INR',
                    method=PaymentMethod.CASH,
                    reference=f'EXL-{enrollment.id}',
                    paid_at=parse_date(row.get('Date')) or datetime.now(),
                    discount_total=total_amount - paid_amount if total_amount > paid_amount else 0,
                    created_by_id=6,
                    updated_by_id=6
                )
                db.add(payment)
                payments_created += 1

        except Exception as e:
            print(f"  ! Error importing enrollment row {idx}: {str(e)}")
            continue

    db.commit()
    print(f"[OK] Created {enrollments_created} enrollments")
    print(f"[OK] Created {payments_created} payments")


def main():
    """Main import function."""
    print("=" * 70)
    print("IMPORTING CHANDIGARH DATA FROM EXCEL")
    print("=" * 70)

    # Load Excel file
    print(f"\nLoading Excel file: {EXCEL_FILE}")
    xls = pd.ExcelFile(EXCEL_FILE)
    print(f"[OK] Found {len(xls.sheet_names)} worksheets")

    # Get database session
    db = SessionLocal()

    try:
        # Import in order
        import_batches(db)
        import_enquiries(db, xls)
        import_enrollments(db, xls)

        print("\n" + "=" * 70)
        print("IMPORT COMPLETED SUCCESSFULLY!")
        print("=" * 70)

        # Print summary
        print("\nFinal counts:")
        print(f"  - Children: {db.query(Child).filter(Child.center_id == CHANDIGARH_CENTER_ID).count()}")
        print(f"  - Parents: {db.query(Parent).filter(Parent.center_id == CHANDIGARH_CENTER_ID).count()}")
        print(f"  - Leads: {db.query(Lead).filter(Lead.center_id == CHANDIGARH_CENTER_ID).count()}")
        print(f"  - Batches: {db.query(Batch).filter(Batch.center_id == CHANDIGARH_CENTER_ID).count()}")
        print(f"  - Enrollments: {db.query(Enrollment).filter(Enrollment.center_id == CHANDIGARH_CENTER_ID).count()}")
        print(f"  - Payments: {db.query(Payment).filter(Payment.center_id == CHANDIGARH_CENTER_ID).count()}")

    except Exception as e:
        print(f"\n[ERROR] Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
