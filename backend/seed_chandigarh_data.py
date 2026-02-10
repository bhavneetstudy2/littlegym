"""Seed comprehensive data for Chandigarh center with enrolled students and attendance."""
import requests
from datetime import datetime, date, timedelta
import random

BASE_URL = "http://localhost:8000/api/v1"

# Sample data
CHILDREN = [
    {"first_name": "Aarav", "last_name": "Sharma", "dob": "2019-03-15", "school": "DPS Chandigarh"},
    {"first_name": "Vihaan", "last_name": "Gupta", "dob": "2020-06-22", "school": "St. Johns"},
    {"first_name": "Aanya", "last_name": "Singh", "dob": "2018-11-10", "school": "Carmel Convent"},
    {"first_name": "Advika", "last_name": "Patel", "dob": "2019-08-05", "school": "DPS Chandigarh"},
    {"first_name": "Vivaan", "last_name": "Kumar", "dob": "2020-01-30", "school": "The Gurukul"},
    {"first_name": "Kiara", "last_name": "Mehta", "dob": "2018-04-18", "school": "St. Annes"},
    {"first_name": "Reyansh", "last_name": "Verma", "dob": "2019-12-03", "school": "DPS Chandigarh"},
    {"first_name": "Anaya", "last_name": "Jain", "dob": "2020-09-25", "school": "Little Flower"},
    {"first_name": "Arjun", "last_name": "Kapoor", "dob": "2018-07-08", "school": "Bhavan Vidyalaya"},
    {"first_name": "Myra", "last_name": "Malhotra", "dob": "2019-05-12", "school": "Sacred Heart"},
    {"first_name": "Kabir", "last_name": "Chadha", "dob": "2020-02-28", "school": "St. Johns"},
    {"first_name": "Ira", "last_name": "Ahuja", "dob": "2018-10-19", "school": "Carmel Convent"},
]

PARENTS = [
    {"name": "Rajesh Sharma", "phone": "+91-9876543210", "email": "rajesh.sharma@gmail.com"},
    {"name": "Priya Sharma", "phone": "+91-9876543211", "email": "priya.sharma@gmail.com"},
    {"name": "Amit Gupta", "phone": "+91-9812345678", "email": "amit.gupta@outlook.com"},
    {"name": "Neha Gupta", "phone": "+91-9812345679", "email": "neha.gupta@gmail.com"},
    {"name": "Vikram Singh", "phone": "+91-9988776655", "email": "vikram.singh@yahoo.com"},
    {"name": "Pooja Singh", "phone": "+91-9988776656", "email": None},
    {"name": "Harsh Patel", "phone": "+91-9771234567", "email": "harsh.patel@gmail.com"},
    {"name": "Sanjay Kumar", "phone": "+91-9654321098", "email": "sanjay.k@gmail.com"},
    {"name": "Meera Kumar", "phone": "+91-9654321099", "email": "meera.kumar@outlook.com"},
    {"name": "Rohit Mehta", "phone": "+91-9823456789", "email": "rohit.mehta@gmail.com"},
    {"name": "Anita Mehta", "phone": "+91-9823456790", "email": None},
    {"name": "Deepak Verma", "phone": "+91-9765432100", "email": "deepak.v@gmail.com"},
]

BATCHES = [
    {"name": "Tiny Tumblers (2-3 yrs)", "age_min": 2, "age_max": 3, "days": ["Mon", "Wed", "Fri"], "start": "09:00", "end": "10:00", "capacity": 8},
    {"name": "Jungle Gym (3-4 yrs)", "age_min": 3, "age_max": 4, "days": ["Mon", "Wed", "Fri"], "start": "10:30", "end": "11:30", "capacity": 10},
    {"name": "Super Beasts (4-5 yrs)", "age_min": 4, "age_max": 5, "days": ["Tue", "Thu", "Sat"], "start": "09:00", "end": "10:00", "capacity": 10},
    {"name": "Funny Bugs (5-6 yrs)", "age_min": 5, "age_max": 6, "days": ["Tue", "Thu", "Sat"], "start": "10:30", "end": "11:30", "capacity": 12},
    {"name": "Weekend Warriors (4-6 yrs)", "age_min": 4, "age_max": 6, "days": ["Sat", "Sun"], "start": "15:00", "end": "16:00", "capacity": 15},
]


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


def get_chandigarh_center(headers):
    """Get Chandigarh center ID."""
    response = requests.get(f"{BASE_URL}/centers", headers=headers)
    centers = response.json()
    for c in centers:
        if "Chandigarh" in c["name"]:
            print(f"Found center: {c['id']} - {c['name']}")
            return c["id"]
    print("Chandigarh center not found!")
    return None


def create_center_admin(headers, center_id):
    """Create a center admin for Chandigarh."""
    response = requests.post(f"{BASE_URL}/users", headers=headers, json={
        "name": "Chandigarh Admin",
        "email": "admin.chandigarh@thelittlegym.in",
        "phone": "+91-9800000001",
        "password": "admin123",
        "role": "CENTER_ADMIN",
        "center_id": center_id
    })
    if response.status_code == 200:
        user = response.json()
        print(f"Created center admin: {user['id']} - {user['name']}")
        return user
    elif "already registered" in response.text.lower():
        print("Center admin already exists, logging in...")
        # Login as center admin
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin.chandigarh@thelittlegym.in",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            return login_resp.json()["user"]
    else:
        print(f"Failed to create center admin: {response.text}")
    return None


def get_center_admin_token():
    """Get center admin token."""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin.chandigarh@thelittlegym.in",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def create_batches(headers, center_id):
    """Create batches for the center."""
    created = []

    # First check existing batches
    existing = requests.get(f"{BASE_URL}/enrollments/batches?center_id={center_id}", headers=headers)
    if existing.status_code == 200 and len(existing.json()) > 0:
        print(f"Found {len(existing.json())} existing batches")
        return existing.json()

    for batch_data in BATCHES:
        response = requests.post(f"{BASE_URL}/enrollments/batches", headers=headers, json={
            "name": batch_data["name"],
            "age_min": batch_data["age_min"],
            "age_max": batch_data["age_max"],
            "days_of_week": batch_data["days"],
            "start_time": batch_data["start"],
            "end_time": batch_data["end"],
            "capacity": batch_data["capacity"],
            "active": True
        })
        if response.status_code == 200:
            batch = response.json()
            print(f"Created batch: {batch['id']} - {batch['name']}")
            created.append(batch)
        else:
            print(f"Failed to create batch {batch_data['name']}: {response.text}")

    return created


def create_lead_and_enrollment(headers, center_id, child_data, parent_data, batch):
    """Create a lead and convert to enrollment."""

    # Calculate child's age to match batch
    dob = datetime.strptime(child_data["dob"], "%Y-%m-%d").date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # Create lead with flat child fields (matching LeadCreate schema)
    lead_payload = {
        "child_first_name": child_data["first_name"],
        "child_last_name": child_data.get("last_name"),
        "child_dob": child_data["dob"],
        "child_school": child_data.get("school"),
        "child_interests": ["gymnastics"],
        "child_notes": f"Age {age} years",
        "parents": [
            {
                "name": parent_data["name"],
                "phone": parent_data["phone"],
                "email": parent_data.get("email"),
                "notes": None
            }
        ],
        "source": random.choice(["WALK_IN", "REFERRAL", "INSTAGRAM", "FACEBOOK"]),
        "discovery_notes": f"Interested in {batch['name']}"
    }

    response = requests.post(f"{BASE_URL}/leads", headers=headers, json=lead_payload)
    if response.status_code != 200:
        print(f"Failed to create lead for {child_data['first_name']}: {response.text}")
        return None

    lead = response.json()
    print(f"Created lead: {lead['id']} - {child_data['first_name']} {child_data.get('last_name', '')}")

    # Create enrollment
    plan_types = ["MONTHLY", "QUARTERLY", "YEARLY", "PAY_PER_VISIT"]
    plan_type = random.choice(plan_types)

    start_date = date.today() - timedelta(days=random.randint(0, 60))
    paid_at = datetime.combine(start_date, datetime.now().time()).isoformat()

    enrollment_payload = {
        "child_id": lead["child_id"],  # Use child_id from lead response
        "batch_id": batch["id"],
        "plan_type": plan_type,
        "start_date": start_date.isoformat(),
        "days_selected": batch.get("days_of_week", ["Mon", "Wed", "Fri"]),
        "notes": f"Enrolled in {batch['name']}"
    }

    # Set end date or visits based on plan type
    if plan_type == "MONTHLY":
        enrollment_payload["end_date"] = (start_date + timedelta(days=30)).isoformat()
        enrollment_payload["payment"] = {"amount": 5000, "method": "UPI", "paid_at": paid_at}
    elif plan_type == "QUARTERLY":
        enrollment_payload["end_date"] = (start_date + timedelta(days=90)).isoformat()
        enrollment_payload["payment"] = {"amount": 12000, "method": "BANK_TRANSFER", "paid_at": paid_at}
    elif plan_type == "YEARLY":
        enrollment_payload["end_date"] = (start_date + timedelta(days=365)).isoformat()
        enrollment_payload["payment"] = {"amount": 40000, "method": "BANK_TRANSFER", "paid_at": paid_at}
    else:  # PAY_PER_VISIT
        enrollment_payload["visits_included"] = random.randint(10, 20)
        enrollment_payload["payment"] = {"amount": enrollment_payload["visits_included"] * 500, "method": "CASH", "paid_at": paid_at}

    response = requests.post(f"{BASE_URL}/enrollments?lead_id={lead['id']}", headers=headers, json=enrollment_payload)
    if response.status_code != 200:
        print(f"Failed to create enrollment: {response.text}")
        return None

    enrollment = response.json()
    print(f"Created enrollment: {enrollment['id']} - {plan_type}")
    return enrollment


def create_attendance_sessions(headers, batches, center_id):
    """Create class sessions and attendance records."""
    today = date.today()

    for batch in batches:
        # Create sessions for the past 2 weeks
        for days_ago in range(14, -1, -1):
            session_date = today - timedelta(days=days_ago)
            day_name = session_date.strftime("%a")

            # Check if this day matches batch schedule
            if day_name not in (batch.get("days_of_week") or []):
                continue

            # Create session
            session_payload = {
                "batch_id": batch["id"],
                "session_date": session_date.isoformat(),
                "start_time": batch.get("start_time", "09:00:00"),
                "end_time": batch.get("end_time", "10:00:00"),
                "status": "COMPLETED" if days_ago > 0 else "SCHEDULED"
            }

            response = requests.post(f"{BASE_URL}/attendance/sessions", headers=headers, json=session_payload)
            if response.status_code == 200:
                session = response.json()
                print(f"Created session: {session['id']} - {batch['name']} on {session_date}")
            elif "already exists" not in response.text.lower():
                print(f"Session creation note: {response.text[:100]}")


def main():
    print("=" * 60)
    print("Seeding Chandigarh Center Data")
    print("=" * 60)

    # Login as super admin
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    # Get Chandigarh center
    center_id = get_chandigarh_center(headers)
    if not center_id:
        print("Cannot proceed without Chandigarh center")
        return

    # Create center admin
    admin = create_center_admin(headers, center_id)

    # Get center admin token for creating batches/enrollments
    admin_token = get_center_admin_token()
    if admin_token:
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("Switched to center admin context")

    # Create batches
    print("\n--- Creating Batches ---")
    batches = create_batches(headers, center_id)

    if not batches:
        print("No batches created or found!")
        return

    # Create enrollments
    print("\n--- Creating Enrollments ---")
    enrollments = []
    for i, child in enumerate(CHILDREN):
        parent = PARENTS[i % len(PARENTS)]
        # Assign to appropriate batch based on child age
        dob = datetime.strptime(child["dob"], "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Find matching batch
        batch = None
        for b in batches:
            if b.get("age_min", 0) <= age <= b.get("age_max", 99):
                batch = b
                break

        if not batch:
            batch = random.choice(batches)

        enrollment = create_lead_and_enrollment(headers, center_id, child, parent, batch)
        if enrollment:
            enrollments.append(enrollment)

    # Create attendance sessions
    print("\n--- Creating Attendance Sessions ---")
    create_attendance_sessions(headers, batches, center_id)

    print("\n" + "=" * 60)
    print(f"Seeding complete!")
    print(f"  Batches: {len(batches)}")
    print(f"  Enrollments: {len(enrollments)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
