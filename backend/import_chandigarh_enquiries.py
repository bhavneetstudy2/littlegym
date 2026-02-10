"""Import Chandigarh enquiries from CSV file."""
import csv
import requests
from datetime import datetime, date
import re

BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh - Enquiry.csv"

# Source mapping
SOURCE_MAP = {
    "walk-in": "WALK_IN",
    "referral": "REFERRAL",
    "social media": "INSTAGRAM",
    "website": "WEBSITE",
    "other": "OTHER",
    "": "WALK_IN"
}


def parse_date(date_str):
    """Parse date from DD/MM/YYYY format."""
    if not date_str:
        return None
    try:
        # Try DD/MM/YYYY format
        dt = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return dt.date().isoformat()
    except ValueError:
        try:
            # Try other formats
            dt = datetime.strptime(date_str.strip(), "%d-%b")
            return None  # Just month-day, can't determine year
        except ValueError:
            return None


def parse_age_to_dob(age_str):
    """Convert age to approximate DOB."""
    if not age_str:
        return None
    try:
        age = float(age_str.replace("+", "").strip())
        if age > 0:
            # Calculate approximate birth year
            birth_year = date.today().year - int(age)
            # Assume birth month based on decimal
            birth_month = 6  # Default to June
            if age != int(age):
                decimal = age - int(age)
                birth_month = int(12 - (decimal * 12)) + 1
                if birth_month > 12:
                    birth_month = 12
                if birth_month < 1:
                    birth_month = 1
            return f"{birth_year}-{birth_month:02d}-15"
    except (ValueError, TypeError):
        pass
    return None


def clean_phone(phone):
    """Clean phone number."""
    if not phone:
        return None
    # Remove spaces, keep digits and + and -
    phone = re.sub(r'[^\d+\-]', '', str(phone).strip())
    if not phone:
        return None
    # Ensure it starts with +91 if it's a 10-digit number
    if len(phone) == 10 and phone.isdigit():
        phone = f"+91-{phone}"
    return phone


def clean_name(name):
    """Clean name field."""
    if not name:
        return None
    name = name.strip()
    if name.lower() in ["not known", "n/a", "-", ""]:
        return None
    return name


def login():
    """Login and get token."""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@thelittlegym.in",
        "password": "admin123"
    })
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        exit(1)
    data = response.json()
    print(f"Logged in as: {data['user']['name']}")
    return data["access_token"]


def get_chandigarh_center_id(headers):
    """Get Chandigarh center ID."""
    response = requests.get(f"{BASE_URL}/centers", headers=headers)
    centers = response.json()
    for c in centers:
        if "Chandigarh" in c["name"]:
            print(f"Found center: {c['id']} - {c['name']}")
            return c["id"]
    print("Chandigarh center not found!")
    return None


def create_lead(headers, center_id, row):
    """Create a lead from CSV row."""
    # Extract data from row
    lead_id = row.get("F", "").strip()
    enquiry_date = row.get("Enquiry Date", "")
    child_first_name = clean_name(row.get("Child Name", ""))
    child_last_name = clean_name(row.get("Last Name", ""))
    parent_name = clean_name(row.get("Parent Name", ""))
    contact = clean_phone(row.get("Contact Number", ""))
    email = row.get("Email", "").strip() or None
    age = row.get("Age", "").strip()
    gender = row.get("Gender", "").strip()
    source = row.get("Source", "").strip().lower()
    school = row.get("School", "").strip() or None
    birthday = row.get("Birthday", "").strip()
    expectations = row.get("Expectations", "").strip() or None
    remarks = row.get("Remarks", "").strip() or None

    # Skip if no child name
    if not child_first_name:
        print(f"  Skipping {lead_id}: No child name")
        return None

    # Skip if no parent contact
    if not contact and not parent_name:
        print(f"  Skipping {lead_id}: No parent info")
        return None

    # Calculate DOB from age or birthday
    dob = None
    if birthday:
        dob = parse_date(birthday)
    if not dob and age:
        dob = parse_age_to_dob(age)

    # Map source
    source_enum = SOURCE_MAP.get(source, "WALK_IN")

    # Build notes
    notes_parts = []
    if lead_id:
        notes_parts.append(f"Original ID: {lead_id}")
    if enquiry_date:
        notes_parts.append(f"Enquiry: {enquiry_date}")
    if gender:
        notes_parts.append(f"Gender: {gender}")
    if expectations:
        notes_parts.append(f"Expectations: {expectations}")
    if remarks:
        notes_parts.append(f"Remarks: {remarks}")
    if school and school.lower() == "enrolled":
        notes_parts.append("Status: Previously marked as Enrolled")

    # Create lead payload
    payload = {
        "child_first_name": child_first_name,
        "child_last_name": child_last_name,
        "child_dob": dob,
        "child_school": school if school and school.lower() != "enrolled" else None,
        "child_interests": None,
        "child_notes": "; ".join(notes_parts) if notes_parts else None,
        "parents": [{
            "name": parent_name or "Parent",
            "phone": contact or "+91-0000000000",
            "email": email,
            "notes": None
        }],
        "source": source_enum,
        "discovery_notes": None,
        "center_id": center_id
    }

    # Create lead via API
    response = requests.post(f"{BASE_URL}/leads", headers=headers, json=payload)
    if response.status_code == 200:
        lead = response.json()
        return lead
    else:
        print(f"  Failed to create lead {lead_id}: {response.text[:100]}")
        return None


def main():
    print("=" * 60)
    print("Importing Chandigarh Enquiries from CSV")
    print("=" * 60)

    # Login
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    # Get Chandigarh center
    center_id = get_chandigarh_center_id(headers)
    if not center_id:
        print("Cannot proceed without Chandigarh center")
        return

    # Read CSV
    print(f"\nReading CSV: {CSV_FILE}")
    created = 0
    skipped = 0
    errors = 0

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        total = len(rows)
        print(f"Found {total} rows to import\n")

        for i, row in enumerate(rows, 1):
            lead_id = row.get("F", f"Row {i}")
            print(f"[{i}/{total}] Processing {lead_id}...", end=" ")

            lead = create_lead(headers, center_id, row)
            if lead:
                print(f"Created lead #{lead['id']}")
                created += 1
            else:
                skipped += 1

            # Progress every 50
            if i % 50 == 0:
                print(f"\n--- Progress: {i}/{total} ({created} created, {skipped} skipped) ---\n")

    print("\n" + "=" * 60)
    print(f"Import complete!")
    print(f"  Total rows: {total}")
    print(f"  Created: {created}")
    print(f"  Skipped: {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    main()
