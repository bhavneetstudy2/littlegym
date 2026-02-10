"""
Import TLG Chandigarh leads from CSV file.
Handles data cleaning, validation, and duplicate detection.
"""

import csv
import re
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Center, User, Parent, Child, FamilyLink, Lead
from app.utils.enums import LeadStatus, LeadSource


def parse_date(date_str):
    """Parse various date formats from CSV to Python date object."""
    if not date_str or date_str.strip() == "":
        return None

    date_str = date_str.strip()

    # Try different date formats
    formats = [
        "%d/%m/%Y",      # 05/11/20
        "%d-%b",         # 21-Apr (assume current year)
        "%d-%b-%y",      # 21-Apr-21
        "%d %B %y",      # 19 September 21
        "%d/%m/%y",      # 01/03/21
        "%d-%m-%Y",      # 21-04-2021
        "%d-%b-%Y",      # 21-Apr-2021
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # If only day-month (no year), assume recent birth year based on age
            if fmt == "%d-%b":
                # Default to 2020 for kids around 4-5 years old
                parsed_date = parsed_date.replace(year=2020)
            return parsed_date
        except ValueError:
            continue

    # If all formats fail, return None
    print(f"  [WARNING] Could not parse date: {date_str}")
    return None


def parse_age(age_str):
    """Parse age string to float."""
    if not age_str or age_str.strip() == "":
        return None

    try:
        age_str = age_str.strip()
        # Handle formats like "3.5", "4+", "12+"
        age_str = age_str.replace("+", "")
        return float(age_str)
    except ValueError:
        print(f"  [WARNING] Could not parse age: {age_str}")
        return None


def split_parent_names(parent_name_str):
    """Split parent names if multiple are provided."""
    if not parent_name_str or parent_name_str.strip() == "":
        return []

    parent_name_str = parent_name_str.strip()

    # Split by comma or slash
    if "," in parent_name_str:
        names = [n.strip() for n in parent_name_str.split(",")]
    elif "/" in parent_name_str:
        names = [n.strip() for n in parent_name_str.split("/")]
    else:
        names = [parent_name_str]

    # Filter out empty names
    return [n for n in names if n and n != ""]


def map_source_to_enum(source_str):
    """Map CSV source values to LeadSource enum."""
    if not source_str or source_str.strip() == "":
        return LeadSource.WALK_IN  # Default

    source_str = source_str.strip().lower()

    if "walk" in source_str or "walk-in" in source_str:
        return LeadSource.WALK_IN
    elif "referral" in source_str:
        return LeadSource.REFERRAL
    elif "instagram" in source_str or "social media" in source_str:
        return LeadSource.INSTAGRAM
    elif "facebook" in source_str:
        return LeadSource.FACEBOOK
    elif "google" in source_str or "website" in source_str:
        return LeadSource.GOOGLE
    else:
        return LeadSource.OTHER


def clean_phone(phone_str):
    """Clean and normalize phone number."""
    if not phone_str:
        return None

    # Remove all non-digit characters
    phone = re.sub(r'\D', '', str(phone_str))

    # If it's empty after cleaning, return None
    if not phone:
        return None

    # Ensure it's not too short
    if len(phone) < 10:
        return None

    # Take last 10 digits for Indian numbers
    return phone[-10:]


def is_valid_child_name(name):
    """Check if child name is valid (not 'Not Known', etc.)."""
    if not name or name.strip() == "":
        return False

    name = name.strip().lower()
    invalid_names = ["not known", "not", "unknown", ""]

    return name not in invalid_names


def calculate_dob_from_age(age_years):
    """Calculate approximate DOB from age."""
    if not age_years:
        return None

    try:
        current_year = date.today().year
        birth_year = current_year - int(age_years)
        # Use January 1st as default birth date
        return date(birth_year, 1, 1)
    except:
        return None


def import_chandigarh_leads(csv_file_path):
    """Import leads from CSV file."""
    db: Session = SessionLocal()

    # Counters
    stats = {
        "total_rows": 0,
        "skipped_invalid_child": 0,
        "skipped_no_phone": 0,
        "skipped_duplicate": 0,
        "created_children": 0,
        "created_parents": 0,
        "created_family_links": 0,
        "created_leads": 0,
        "errors": []
    }

    try:
        print("=" * 70)
        print("IMPORTING TLG CHANDIGARH LEADS FROM CSV")
        print("=" * 70)

        # Get the center (assume first center is TLG Chandigarh)
        center = db.query(Center).first()
        if not center:
            print("\n[ERROR] No center found! Please run seed_data.py first.")
            return

        print(f"\nImporting to center: {center.name}")

        # Get a default admin user for assignment
        admin_user = db.query(User).filter(User.center_id == center.id).first()

        # Read CSV file
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because header is row 1
                stats["total_rows"] += 1

                try:
                    # Extract data from row
                    lead_ref = row.get("F", "").strip()
                    enquiry_date_str = row.get("Enquiry Date", "").strip()
                    child_first_name = row.get("Child Name", "").strip()
                    child_last_name = row.get("Last Name", "").strip()
                    parent_name_str = row.get("Parent Name", "").strip()
                    phone_str = row.get("Contact Number", "").strip()
                    email = row.get("Email", "").strip() or None
                    age_str = row.get("Age", "").strip()
                    gender = row.get("Gender", "").strip()
                    source_str = row.get("Source", "").strip()
                    school = row.get("School", "").strip() or None
                    birthday_str = row.get("Birthday", "").strip()
                    expectations = row.get("Expectations", "").strip()
                    remarks = row.get("Remarks", "").strip()

                    # Validate child name
                    if not is_valid_child_name(child_first_name):
                        stats["skipped_invalid_child"] += 1
                        print(f"  [SKIP] Row {row_num}: Invalid child name '{child_first_name}'")
                        continue

                    # Clean and validate phone
                    phone = clean_phone(phone_str)
                    if not phone:
                        stats["skipped_no_phone"] += 1
                        print(f"  [SKIP] Row {row_num}: No valid phone number for {child_first_name}")
                        continue

                    # Parse dates
                    enquiry_date = parse_date(enquiry_date_str)
                    dob = parse_date(birthday_str)

                    # If no DOB but age is available, calculate approximate DOB
                    if not dob:
                        age = parse_age(age_str)
                        dob = calculate_dob_from_age(age)

                    # Check for duplicate (phone + child name)
                    existing_parent = db.query(Parent).filter(
                        Parent.center_id == center.id,
                        Parent.phone == phone
                    ).first()

                    if existing_parent:
                        # Check if child with same name exists for this parent
                        existing_child = db.query(Child).join(FamilyLink).filter(
                            Child.center_id == center.id,
                            Child.first_name == child_first_name,
                            FamilyLink.parent_id == existing_parent.id
                        ).first()

                        if existing_child:
                            stats["skipped_duplicate"] += 1
                            print(f"  [SKIP] Row {row_num}: Duplicate - {child_first_name} with phone {phone}")
                            continue

                    # Create or get parent(s)
                    parent_names = split_parent_names(parent_name_str)
                    if not parent_names:
                        parent_names = ["Parent"]  # Default name if missing

                    parents_list = []
                    for parent_name in parent_names:
                        # Check if parent already exists with this phone
                        parent = db.query(Parent).filter(
                            Parent.center_id == center.id,
                            Parent.phone == phone
                        ).first()

                        if not parent:
                            parent = Parent(
                                center_id=center.id,
                                name=parent_name,
                                phone=phone,
                                email=email,
                                notes=f"Lead ref: {lead_ref}"
                            )
                            db.add(parent)
                            db.flush()
                            stats["created_parents"] += 1

                        parents_list.append(parent)

                    # Create child
                    child_notes = []
                    if gender:
                        child_notes.append(f"Gender: {gender}")
                    if age_str:
                        child_notes.append(f"Age at enquiry: {age_str}")
                    if expectations:
                        child_notes.append(f"Expectations: {expectations}")

                    child = Child(
                        center_id=center.id,
                        first_name=child_first_name,
                        last_name=child_last_name if child_last_name else None,
                        dob=dob,
                        school=school,
                        interests=None,
                        notes=" | ".join(child_notes) if child_notes else None
                    )
                    db.add(child)
                    db.flush()
                    stats["created_children"] += 1

                    # Link child to parent(s)
                    for idx, parent in enumerate(parents_list):
                        family_link = FamilyLink(
                            center_id=center.id,
                            child_id=child.id,
                            parent_id=parent.id,
                            relationship_type="parent",
                            is_primary_contact=(idx == 0)  # First parent is primary
                        )
                        db.add(family_link)
                        stats["created_family_links"] += 1

                    # Create lead
                    discovery_notes = []
                    if lead_ref:
                        discovery_notes.append(f"Ref: {lead_ref}")
                    if enquiry_date:
                        discovery_notes.append(f"Enquiry date: {enquiry_date}")
                    if expectations:
                        discovery_notes.append(f"Expectations: {expectations}")
                    if remarks:
                        discovery_notes.append(f"Remarks: {remarks}")

                    # Map source to enum
                    lead_source = map_source_to_enum(source_str)

                    lead = Lead(
                        center_id=center.id,
                        child_id=child.id,
                        status=LeadStatus.DISCOVERY,
                        source=lead_source,
                        discovery_notes=" | ".join(discovery_notes) if discovery_notes else None,
                        assigned_to_user_id=admin_user.id if admin_user else None
                    )
                    db.add(lead)
                    db.flush()
                    stats["created_leads"] += 1

                    # Print progress every 50 rows
                    if stats["total_rows"] % 50 == 0:
                        print(f"  Processed {stats['total_rows']} rows... ({stats['created_leads']} leads created)")

                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    stats["errors"].append(error_msg)
                    print(f"  [ERROR] {error_msg}")
                    continue

        # Commit all changes
        db.commit()

        # Print summary
        print("\n" + "=" * 70)
        print("IMPORT SUMMARY")
        print("=" * 70)
        print(f"\nTotal rows processed: {stats['total_rows']}")
        print(f"\nSuccessfully created:")
        print(f"  - {stats['created_children']} children")
        print(f"  - {stats['created_parents']} parents")
        print(f"  - {stats['created_family_links']} family links")
        print(f"  - {stats['created_leads']} leads")

        print(f"\nSkipped:")
        print(f"  - {stats['skipped_invalid_child']} (invalid child name)")
        print(f"  - {stats['skipped_no_phone']} (no phone number)")
        print(f"  - {stats['skipped_duplicate']} (duplicates)")

        if stats["errors"]:
            print(f"\nErrors: {len(stats['errors'])}")
            for error in stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats["errors"]) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")

        print("\n" + "=" * 70)
        print("[SUCCESS] Import completed!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Import failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    csv_file = r"C:\Users\Administrator\Downloads\TLG Chandigarh - Enquiry.csv"
    import_chandigarh_leads(csv_file)
