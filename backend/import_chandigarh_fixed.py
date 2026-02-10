"""
Import Chandigarh data correctly using Enquiry ID mapping.
This script:
1. Reads the Enrolled sheet from Excel to get Enquiry ID + metadata
2. Updates children with enquiry_id
3. Updates enrollments with correct metadata
4. Reads the Attendance CSV
5. Creates attendance records for each date
6. Updates visits_used based on attendance
"""
import pandas as pd
import csv
import sys
from datetime import datetime, date
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.models import (
    Center, Child, Enrollment, Batch, Attendance, ClassSession
)
from app.utils.enums import AttendanceStatus, EnrollmentStatus, PlanType, SessionStatus
from app.core.database import SessionLocal

load_dotenv()

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'
CHANDIGARH_CENTER_ID = 3


def safe_print(msg):
    """Print with safe encoding."""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Replace problematic characters
        print(msg.encode('ascii', 'replace').decode('ascii'))


def parse_date_from_dd_mmm(date_str, year=2024):
    """Parse date from DD-MMM format."""
    if not date_str or pd.isna(date_str) or str(date_str).strip() == '':
        return None

    try:
        # Handle DD-MMM format (e.g., "18-Apr")
        date_str = str(date_str).strip()
        dt = datetime.strptime(f"{date_str}-{year}", "%d-%b-%Y")
        return dt.date()
    except:
        return None


def parse_date_general(date_val):
    """Parse date from various formats."""
    if pd.isna(date_val) or date_val == '' or date_val == '-':
        return None

    if isinstance(date_val, (datetime, date)):
        return date_val if isinstance(date_val, date) else date_val.date()

    try:
        if isinstance(date_val, str):
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_val, fmt).date()
                except:
                    continue
    except:
        pass

    return None


def import_enrollment_metadata(db: Session):
    """Import enrollment metadata from Excel using Enquiry ID."""
    safe_print("\n" + "="*70)
    safe_print("STEP 1: Importing Enrollment Metadata from Excel")
    safe_print("="*70)

    # Read Excel file
    df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
    safe_print(f"Found {len(df)} enrolled students in Excel")

    # Get all batches
    batches = {batch.name: batch for batch in db.query(Batch).filter(
        Batch.center_id == CHANDIGARH_CENTER_ID
    ).all()}

    updated_children = 0
    updated_enrollments = 0
    not_found = []

    for idx, row in df.iterrows():
        try:
            enquiry_id = str(row.get('Enquiry ID', '')).strip()
            child_name = str(row.get('Child Name', '')).strip()
            batch_name = str(row.get('Batch', '')).strip()
            booked_classes = int(row.get('Booked Classes', 0)) if not pd.isna(row.get('Booked Classes')) else 24
            total_amount = float(row.get('Total Amount', 0)) if not pd.isna(row.get('Total Amount')) else 0
            paid_amount = float(row.get('Paid Amount', 0)) if not pd.isna(row.get('Paid Amount')) else 0
            start_date_str = row.get('Date', '')
            duration = str(row.get('Duration', '')).strip() if not pd.isna(row.get('Duration')) else None

            if not enquiry_id or not child_name or enquiry_id == 'nan':
                continue

            # Find child by name (first time) or enquiry_id (subsequent)
            child = db.query(Child).filter(
                Child.center_id == CHANDIGARH_CENTER_ID
            ).filter(
                (Child.enquiry_id == enquiry_id) |
                (Child.first_name.ilike(f'%{child_name}%'))
            ).first()

            if not child:
                not_found.append(f"{enquiry_id} - {child_name}")
                continue

            # Update child with enquiry_id (skip if already set to avoid conflicts)
            if not child.enquiry_id:
                # Check if this enquiry_id is already used by another child
                existing_child = db.query(Child).filter(
                    Child.center_id == CHANDIGARH_CENTER_ID,
                    Child.enquiry_id == enquiry_id
                ).first()

                if not existing_child:
                    child.enquiry_id = enquiry_id
                    updated_children += 1
                elif existing_child.id != child.id:
                    safe_print(f"  ! Enquiry ID {enquiry_id} already used by {existing_child.first_name}")

            # Get batch
            batch = batches.get(batch_name)
            if not batch:
                safe_print(f"  ! Batch not found: {batch_name} for {child_name}")
                continue

            # Find or update enrollment
            enrollment = db.query(Enrollment).filter(
                Enrollment.center_id == CHANDIGARH_CENTER_ID,
                Enrollment.child_id == child.id
            ).first()

            if enrollment:
                # Update enrollment metadata
                enrollment.batch_id = batch.id
                enrollment.visits_included = booked_classes
                enrollment.visits_used = 0  # Will be updated from attendance
                enrollment.plan_type = PlanType.CUSTOM
                enrollment.status = EnrollmentStatus.ACTIVE

                # Parse start date
                start_date = parse_date_general(start_date_str)
                if start_date:
                    enrollment.start_date = start_date

                # Add duration and amount to notes
                notes_parts = []
                if duration:
                    notes_parts.append(f"Duration: {duration}")
                if total_amount > 0:
                    notes_parts.append(f"Total Amount: Rs.{total_amount}")
                if paid_amount > 0:
                    notes_parts.append(f"Paid Amount: Rs.{paid_amount}")
                if notes_parts:
                    enrollment.notes = "; ".join(notes_parts)

                updated_enrollments += 1
                safe_print(f"  OK {enquiry_id} - {child_name} ({batch_name}): {booked_classes} classes")

        except Exception as e:
            safe_print(f"  ! Error row {idx}: {str(e)}")
            db.rollback()  # Rollback this row and continue
            continue

    # Final commit for any pending changes
    try:
        db.commit()
    except Exception as e:
        safe_print(f"  ! Final commit error: {str(e)}")
        db.rollback()

    safe_print(f"\n[SUMMARY]")
    safe_print(f"  Children updated with Enquiry ID: {updated_children}")
    safe_print(f"  Enrollments updated: {updated_enrollments}")
    safe_print(f"  Not found: {len(not_found)}")


def import_attendance_data(db: Session):
    """Import attendance data from CSV using Enquiry ID."""
    safe_print("\n" + "="*70)
    safe_print("STEP 2: Importing Attendance Data from CSV")
    safe_print("="*70)

    # Read attendance CSV
    with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    safe_print(f"Found {len(rows)} attendance records in CSV")

    # Get all batches
    batches = {batch.name: batch for batch in db.query(Batch).filter(
        Batch.center_id == CHANDIGARH_CENTER_ID
    ).all()}

    attendance_created = 0
    sessions_created = 0
    children_not_found = []
    processed = 0

    for row in rows:
        try:
            enquiry_id = str(row.get('Enquiry ID', '')).strip()
            child_name = str(row.get('Child Name', '')).strip()
            batch_name = str(row.get('Batch', '')).strip()
            attended_classes = int(row.get('Attended Classes', 0)) if row.get('Attended Classes') else 0

            if not enquiry_id or not child_name:
                continue

            # Find child by enquiry_id
            child = db.query(Child).filter(
                Child.center_id == CHANDIGARH_CENTER_ID,
                Child.enquiry_id == enquiry_id
            ).first()

            if not child:
                children_not_found.append(f"{enquiry_id} - {child_name}")
                continue

            # Get enrollment
            enrollment = db.query(Enrollment).filter(
                Enrollment.center_id == CHANDIGARH_CENTER_ID,
                Enrollment.child_id == child.id
            ).first()

            if not enrollment:
                continue

            # Get batch
            batch = batches.get(batch_name)
            if not batch:
                continue

            # Parse attendance dates from columns 1-54
            attendance_dates = []
            for i in range(1, 55):
                date_str = row.get(str(i), '').strip()
                if date_str:
                    # Parse date (assuming 2024, can be adjusted)
                    parsed_date = parse_date_from_dd_mmm(date_str, year=2024)
                    if parsed_date:
                        attendance_dates.append(parsed_date)

            # Create attendance records
            for att_date in attendance_dates:
                # Find or create session for this date/batch
                session = db.query(ClassSession).filter(
                    ClassSession.center_id == CHANDIGARH_CENTER_ID,
                    ClassSession.batch_id == batch.id,
                    ClassSession.session_date == att_date
                ).first()

                if not session:
                    # Create session
                    session = ClassSession(
                        center_id=CHANDIGARH_CENTER_ID,
                        batch_id=batch.id,
                        session_date=att_date,
                        start_time=batch.start_time,
                        end_time=batch.end_time,
                        trainer_user_id=6,  # Super admin as default
                        status=SessionStatus.COMPLETED,
                        created_by_id=6,
                        updated_by_id=6
                    )
                    db.add(session)
                    db.flush()
                    sessions_created += 1

                # Check if attendance already exists for this session and child
                existing = db.query(Attendance).filter(
                    Attendance.center_id == CHANDIGARH_CENTER_ID,
                    Attendance.child_id == child.id,
                    Attendance.class_session_id == session.id
                ).first()

                if existing:
                    continue

                # Create attendance
                attendance = Attendance(
                    center_id=CHANDIGARH_CENTER_ID,
                    class_session_id=session.id,
                    child_id=child.id,
                    enrollment_id=enrollment.id,
                    status=AttendanceStatus.PRESENT,
                    marked_by_user_id=6,
                    marked_at=datetime.now(),
                    notes="Imported from CSV",
                    created_by_id=6,
                    updated_by_id=6
                )
                db.add(attendance)
                attendance_created += 1

            # Update enrollment visits_used
            if attendance_dates:
                enrollment.visits_used = len(attendance_dates)
                processed += 1
                if processed % 10 == 0:
                    safe_print(f"  Progress: {processed} students processed...")

        except Exception as e:
            safe_print(f"  ! Error processing {enquiry_id}: {str(e)}")
            db.rollback()  # Rollback to recover from error
            continue

    db.commit()

    safe_print(f"\n[SUMMARY]")
    safe_print(f"  Attendance records created: {attendance_created}")
    safe_print(f"  Sessions created: {sessions_created}")
    safe_print(f"  Students processed: {processed}")
    safe_print(f"  Children not found: {len(children_not_found)}")


def verify_data(db: Session):
    """Verify imported data."""
    safe_print("\n" + "="*70)
    safe_print("STEP 3: Verifying Data")
    safe_print("="*70)

    # Count children with enquiry_id
    children_with_enquiry = db.query(Child).filter(
        Child.center_id == CHANDIGARH_CENTER_ID,
        Child.enquiry_id.isnot(None)
    ).count()

    # Count total enrollments
    enrollments = db.query(Enrollment).filter(
        Enrollment.center_id == CHANDIGARH_CENTER_ID
    ).count()

    # Count attendance records
    attendance = db.query(Attendance).filter(
        Attendance.center_id == CHANDIGARH_CENTER_ID
    ).count()

    # Check specific student: Mahira
    mahira = db.query(Child).filter(
        Child.center_id == CHANDIGARH_CENTER_ID,
        Child.first_name.ilike('%mahira%')
    ).first()

    safe_print(f"\n[VERIFICATION RESULTS]")
    safe_print(f"  Children with Enquiry ID: {children_with_enquiry}")
    safe_print(f"  Total enrollments: {enrollments}")
    safe_print(f"  Total attendance records: {attendance}")

    if mahira:
        safe_print(f"\n  Found Mahira:")
        safe_print(f"    - ID: {mahira.id}")
        safe_print(f"    - Enquiry ID: {mahira.enquiry_id}")
        safe_print(f"    - Name: {mahira.first_name} {mahira.last_name or ''}")

        # Get enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.child_id == mahira.id
        ).first()

        if enrollment:
            batch = db.query(Batch).filter(Batch.id == enrollment.batch_id).first()
            safe_print(f"    - Batch: {batch.name if batch else 'N/A'}")
            safe_print(f"    - Booked: {enrollment.visits_included}")
            safe_print(f"    - Used: {enrollment.visits_used}")
            safe_print(f"    - Remaining: {enrollment.visits_included - enrollment.visits_used}")

        # Get attendance count
        att_count = db.query(Attendance).filter(
            Attendance.child_id == mahira.id
        ).count()
        safe_print(f"    - Attendance records: {att_count}")
    else:
        safe_print(f"\n  ! Mahira not found in database")


def main():
    """Main import function."""
    safe_print("\n" + "="*70)
    safe_print("IMPORTING CHANDIGARH DATA WITH ENQUIRY ID MAPPING")
    safe_print("="*70)

    db = SessionLocal()

    try:
        # Step 1: Import enrollment metadata
        import_enrollment_metadata(db)

        # Step 2: Import attendance data
        import_attendance_data(db)

        # Step 3: Verify data
        verify_data(db)

        safe_print("\n" + "="*70)
        safe_print("IMPORT COMPLETED SUCCESSFULLY!")
        safe_print("="*70)

    except Exception as e:
        safe_print(f"\n[ERROR] Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
