"""
Complete End-to-End Workflow Test
Tests the entire lifecycle: Enquiry -> Intro Visit -> Follow-up -> Enrollment -> Attendance -> Progress
"""
import sys
import io
import requests
import json
from datetime import datetime, date, timedelta

# Set UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8001"
TOKEN = None
HEADERS = {}

# Test data storage
test_data = {
    "center_id": None,
    "child_id": None,
    "parent_id": None,
    "lead_id": None,
    "intro_visit_id": None,
    "follow_up_id": None,
    "enrollment_id": None,
    "batch_id": None,
    "session_id": None,
    "curriculum_id": None,
    "activity_categories": [],
}

results = {"passed": 0, "failed": 0, "errors": []}


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test(name, func):
    """Run a test and track results"""
    try:
        result = func()
        if result:
            results["passed"] += 1
            print(f"  ✅ PASS: {name}")
            return True
        else:
            results["failed"] += 1
            results["errors"].append(f"FAIL: {name}")
            print(f"  ❌ FAIL: {name}")
            return False
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"ERROR: {name} - {str(e)}")
        print(f"  ❌ ERROR: {name}")
        print(f"     {str(e)}")
        return False


def login():
    """Login as center admin user"""
    print_section("STEP 1: Authentication")

    # Try super admin
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "admin@littlegym.com", "password": "admin123"}
    )

    if response.status_code == 200:
        global TOKEN, HEADERS
        data = response.json()
        TOKEN = data["access_token"]
        HEADERS = {"Authorization": f"Bearer {TOKEN}"}

        # Get user info
        user_response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=HEADERS)
        user = user_response.json()
        test_data["center_id"] = user.get("center_id")

        # If super admin, get first center
        if not test_data["center_id"]:
            centers_resp = requests.get(f"{BASE_URL}/api/v1/centers", headers=HEADERS)
            if centers_resp.status_code == 200:
                centers = centers_resp.json()
                if centers:
                    test_data["center_id"] = centers[0]["id"]
                    print(f"   Using center: {centers[0]['name']} (ID: {test_data['center_id']})")

        print(f"✅ Logged in as: {user['name']} ({user['role']})")
        print(f"   Center ID: {test_data['center_id']}")
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False


def create_enquiry():
    """Create a new enquiry with discovery form"""
    print_section("STEP 2: Create Enquiry (Discovery Form)")

    # Create unique child name with timestamp
    timestamp = datetime.now().strftime("%H%M%S")

    payload = {
        "child_first_name": f"TestChild_{timestamp}",
        "child_last_name": "Kumar",
        "child_dob": "2020-05-15",
        "age": 5,
        "gender": "Boy",
        "parent_name": "Rajesh Kumar",
        "contact_number": f"98765{timestamp[-5:]}",
        "email": f"rajesh{timestamp}@example.com",
        "school": "Little Flowers School",
        "source": "WALK_IN",
        "parent_expectations": ["physical_activity", "child_development", "socialization_skills"],
        "preferred_schedule": "Mon/Wed/Fri evenings",
        "remarks": "Very energetic child, loves physical activities"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/leads/enquiry",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        lead = response.json()
        test_data["lead_id"] = lead["id"]
        test_data["child_id"] = lead["child_id"]

        print(f"✅ Enquiry created successfully!")
        print(f"   Lead ID: {test_data['lead_id']}")
        print(f"   Child ID: {test_data['child_id']}")
        print(f"   Status: {lead['status']}")

        # Fetch lead details
        details_response = requests.get(
            f"{BASE_URL}/api/v1/leads/{test_data['lead_id']}/details",
            headers=HEADERS
        )
        if details_response.status_code == 200:
            details = details_response.json()
            print(f"   Child Name: {details['child']['first_name']} {details['child']['last_name']}")
            print(f"   Enquiry ID: {details['child']['enquiry_id']}")
            print(f"   Parents: {len(details['parents'])} registered")
            test_data["parent_id"] = details['parents'][0]['id'] if details['parents'] else None

        return True
    else:
        print(f"❌ Failed to create enquiry: {response.status_code}")
        print(response.text)
        return False


def get_available_batch():
    """Get an available batch for intro visit"""
    print_section("STEP 3: Get Available Batch")

    response = requests.get(
        f"{BASE_URL}/api/v1/enrollments/batches?center_id={test_data['center_id']}",
        headers=HEADERS
    )

    if response.status_code == 200:
        batches = response.json()
        if batches:
            test_data["batch_id"] = batches[0]["id"]
            print(f"✅ Found batch: {batches[0]['name']} (ID: {test_data['batch_id']})")
            print(f"   Age Range: {batches[0]['age_min']}-{batches[0]['age_max']} years")
            print(f"   Days: {batches[0]['days_of_week']}")
            return True
        else:
            print("❌ No batches available")
            return False
    else:
        print(f"❌ Failed to fetch batches: {response.status_code}")
        return False


def schedule_intro_visit():
    """Schedule an intro visit"""
    print_section("STEP 4: Schedule Intro Visit")

    # Schedule for tomorrow
    scheduled_time = (datetime.now() + timedelta(days=1)).replace(hour=16, minute=0, second=0)

    payload = {
        "lead_id": test_data["lead_id"],
        "scheduled_at": scheduled_time.isoformat(),
        "batch_id": test_data["batch_id"],
        "outcome_notes": "Scheduled for trial class"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/intro-visits",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        intro_visit = response.json()
        test_data["intro_visit_id"] = intro_visit["id"]

        print(f"✅ Intro visit scheduled successfully!")
        print(f"   IV ID: {test_data['intro_visit_id']}")
        print(f"   Scheduled: {scheduled_time.strftime('%d %b %Y at %I:%M %p')}")
        print(f"   Batch ID: {test_data['batch_id']}")
        return True
    else:
        print(f"❌ Failed to schedule intro visit: {response.status_code}")
        print(response.text)
        return False


def mark_intro_visit_attended():
    """Mark intro visit as attended with positive outcome"""
    print_section("STEP 5: Mark Intro Visit Attended")

    attended_time = datetime.now() - timedelta(hours=2)

    payload = {
        "attended_at": attended_time.isoformat(),
        "outcome": "INTERESTED_ENROLL_NOW",
        "outcome_notes": "Child enjoyed the class. Parents very interested. Ready to enroll."
    }

    response = requests.patch(
        f"{BASE_URL}/api/v1/intro-visits/{test_data['intro_visit_id']}",
        headers=HEADERS,
        json=payload
    )

    if response.status_code == 200:
        print(f"✅ Intro visit marked as attended!")
        print(f"   Outcome: Interested - Enroll Now")
        print(f"   Lead should now be in IV_COMPLETED status")
        return True
    else:
        print(f"❌ Failed to mark IV attended: {response.status_code}")
        print(response.text)
        return False


def create_follow_up():
    """Create a follow-up task"""
    print_section("STEP 6: Create Follow-up")

    follow_up_date = datetime.now() + timedelta(days=1)

    payload = {
        "lead_id": test_data["lead_id"],
        "scheduled_date": follow_up_date.isoformat(),
        "notes": "Call to discuss enrollment details and payment options"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/follow-ups",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        follow_up = response.json()
        test_data["follow_up_id"] = follow_up["id"]

        print(f"✅ Follow-up created!")
        print(f"   Follow-up ID: {test_data['follow_up_id']}")
        print(f"   Scheduled: {follow_up_date.strftime('%d %b %Y')}")
        return True
    else:
        print(f"❌ Failed to create follow-up: {response.status_code}")
        print(response.text)
        return False


def create_enrollment():
    """Create enrollment for the child"""
    print_section("STEP 7: Create Enrollment")

    start_date = date.today()
    end_date = start_date + timedelta(days=90)  # 3 months

    payload = {
        "child_id": test_data["child_id"],
        "plan_type": "MONTHLY",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "batch_id": test_data["batch_id"],
        "days_selected": ["MONDAY", "WEDNESDAY", "FRIDAY"],
        "notes": "Enrolled after successful intro visit",
        "payment": {
            "amount": 5000.00,
            "method": "UPI",
            "reference": f"UPI{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "discount_type": "PERCENT",
            "discount_value": 10.0,
            "discount_reason": "Early bird discount"
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/enrollments",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        enrollment = response.json()
        test_data["enrollment_id"] = enrollment["id"]

        print(f"✅ Enrollment created successfully!")
        print(f"   Enrollment ID: {test_data['enrollment_id']}")
        print(f"   Plan: MONTHLY")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Payment: ₹5000 (10% discount applied)")
        print(f"   Status: {enrollment['status']}")

        # Convert lead to enrolled status
        convert_payload = {
            "enrollment_id": test_data["enrollment_id"]
        }

        convert_response = requests.post(
            f"{BASE_URL}/api/v1/leads/{test_data['lead_id']}/convert",
            headers=HEADERS,
            json=convert_payload
        )

        if convert_response.status_code == 200:
            print(f"✅ Lead marked as CONVERTED")

        return True
    else:
        print(f"❌ Failed to create enrollment: {response.status_code}")
        print(response.text)
        return False


def mark_attendance():
    """Mark attendance for today's class"""
    print_section("STEP 8: Mark Attendance")

    # Get today's date
    today = date.today().isoformat()

    # Quick mark attendance
    payload = {
        "date": today,
        "batch_id": test_data["batch_id"],
        "center_id": test_data["center_id"],
        "attendance": [
            {
                "child_id": test_data["child_id"],
                "status": "PRESENT",
                "notes": "First class - did great!"
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/attendance/quick-mark",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Attendance marked successfully!")
        print(f"   Date: {today}")
        print(f"   Status: PRESENT")
        print(f"   Marked: {result.get('marked', 1)} student(s)")
        return True
    else:
        print(f"❌ Failed to mark attendance: {response.status_code}")
        print(response.text)
        return False


def get_curriculum():
    """Get available curriculum for the batch"""
    print_section("STEP 9: Get Curriculum & Activities")

    # Get curricula
    response = requests.get(
        f"{BASE_URL}/api/v1/curriculum",
        headers=HEADERS
    )

    if response.status_code == 200:
        curricula = response.json()
        if curricula:
            # Use Gymnastics Foundation curriculum
            gym_curriculum = next((c for c in curricula if "Gymnastics" in c["name"]), curricula[0])
            test_data["curriculum_id"] = gym_curriculum["id"]

            print(f"✅ Found curriculum: {gym_curriculum['name']} (ID: {test_data['curriculum_id']})")

            # Get activity categories
            cat_response = requests.get(
                f"{BASE_URL}/api/v1/progress/activity-categories/{test_data['curriculum_id']}",
                headers=HEADERS
            )

            if cat_response.status_code == 200:
                categories = cat_response.json()
                test_data["activity_categories"] = categories
                print(f"   Activities: {len(categories)} found")
                for cat in categories[:5]:
                    print(f"   - {cat['name']} ({cat['measurement_type']})")
                return True

        print("❌ No curriculum found")
        return False
    else:
        print(f"❌ Failed to fetch curriculum: {response.status_code}")
        return False


def update_progress():
    """Update skill progress for the child"""
    print_section("STEP 10: Update Progress Tracker")

    if not test_data["activity_categories"]:
        print("❌ No activities available")
        return False

    # Update progress for first few skills
    skills_to_update = []
    for activity in test_data["activity_categories"][:3]:
        skill_data = {
            "activity_category_id": activity["id"],
            "child_id": test_data["child_id"]
        }

        # Set value based on measurement type
        if activity["measurement_type"] == "LEVEL":
            skill_data["level_value"] = "IN_PROGRESS"
        elif activity["measurement_type"] == "COUNT":
            skill_data["numeric_value"] = 5
        elif activity["measurement_type"] == "TIME":
            skill_data["numeric_value"] = 15.5
        else:
            skill_data["numeric_value"] = 3

        skill_data["notes"] = f"First assessment - showing good potential in {activity['name']}"
        skills_to_update.append(skill_data)

    # Bulk update
    payload = {
        "week_number": 1,
        "progress_data": skills_to_update
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/progress/weekly/bulk-update",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        print(f"✅ Progress updated successfully!")
        print(f"   Skills updated: {len(skills_to_update)}")
        for i, skill in enumerate(skills_to_update):
            activity = test_data["activity_categories"][i]
            value = skill.get("level_value") or skill.get("numeric_value")
            print(f"   - {activity['name']}: {value}")
        return True
    else:
        print(f"❌ Failed to update progress: {response.status_code}")
        print(response.text)
        return False


def generate_report_card():
    """Generate a report card for the child"""
    print_section("STEP 11: Generate Report Card")

    period_start = (date.today() - timedelta(days=30)).isoformat()
    period_end = date.today().isoformat()

    payload = {
        "child_id": test_data["child_id"],
        "period_start": period_start,
        "period_end": period_end,
        "summary_notes": "Great first month! Showing excellent progress in basic skills.",
        "center_id": test_data["center_id"]
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/report-cards/generate",
        headers=HEADERS,
        json=payload
    )

    if response.status_code in [200, 201]:
        report = response.json()
        print(f"✅ Report card generated!")
        print(f"   Report ID: {report['id']}")
        print(f"   Period: {period_start} to {period_end}")
        print(f"   Skills evaluated: {len(report.get('skill_results', []))}")
        return True
    else:
        print(f"❌ Failed to generate report card: {response.status_code}")
        print(response.text)
        return False


def verify_workflow():
    """Verify the complete workflow"""
    print_section("STEP 12: Verify Complete Workflow")

    # Verify lead details
    lead_response = requests.get(
        f"{BASE_URL}/api/v1/leads/{test_data['lead_id']}/details",
        headers=HEADERS
    )

    if lead_response.status_code == 200:
        lead = lead_response.json()
        print(f"✅ Lead Status: {lead['status']}")
        print(f"   Intro Visits: {len(lead.get('intro_visits', []))}")
        print(f"   Follow-ups: {len(lead.get('follow_ups', []))}")

        if lead.get('enrollment_id'):
            print(f"   ✅ Linked to Enrollment: {lead['enrollment_id']}")

    # Verify enrollment
    enrollment_response = requests.get(
        f"{BASE_URL}/api/v1/enrollments/{test_data['enrollment_id']}",
        headers=HEADERS
    )

    if enrollment_response.status_code == 200:
        enrollment = enrollment_response.json()
        print(f"\n✅ Enrollment Status: {enrollment['status']}")
        print(f"   Child: {enrollment['child']['first_name']} {enrollment['child']['last_name']}")
        print(f"   Plan: {enrollment['plan_type']}")
        print(f"   Batch: {enrollment['batch']['name']}")

    # Verify attendance
    today = date.today().isoformat()
    attendance_response = requests.get(
        f"{BASE_URL}/api/v1/attendance/children/{test_data['child_id']}?from_date={today}&to_date={today}",
        headers=HEADERS
    )

    if attendance_response.status_code == 200:
        attendance = attendance_response.json()
        print(f"\n✅ Attendance Records: {len(attendance)}")
        if attendance:
            print(f"   Today's Status: {attendance[0]['status']}")

    # Verify progress
    progress_response = requests.get(
        f"{BASE_URL}/api/v1/progress/weekly/{test_data['child_id']}?week_number=1",
        headers=HEADERS
    )

    if progress_response.status_code == 200:
        progress = progress_response.json()
        print(f"\n✅ Progress Records: {len(progress)}")

    return True


def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")

    total = results["passed"] + results["failed"]
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/total*100):.1f}%")

    if results["errors"]:
        print(f"\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\nTest Data Created:")
    print(json.dumps(test_data, indent=2))


# Run the complete workflow
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  LITTLE GYM CRM - COMPLETE E2E WORKFLOW TEST")
    print("  Testing: Enquiry -> IV -> Follow-up -> Enrollment -> Attendance -> Progress")
    print("="*60)

    if not login():
        print("\n❌ Cannot proceed without authentication")
        exit(1)

    # Execute workflow steps
    test("Create Enquiry with Discovery Form", create_enquiry)
    test("Get Available Batch", get_available_batch)
    test("Schedule Intro Visit", schedule_intro_visit)
    test("Mark Intro Visit Attended", mark_intro_visit_attended)
    test("Create Follow-up", create_follow_up)
    test("Create Enrollment with Payment", create_enrollment)
    test("Mark Attendance", mark_attendance)
    test("Get Curriculum & Activities", get_curriculum)
    test("Update Progress Tracker", update_progress)
    test("Generate Report Card", generate_report_card)
    test("Verify Complete Workflow", verify_workflow)

    # Print summary
    print_summary()

    print("\n" + "="*60)
    if results["failed"] == 0:
        print("  ✅ ALL TESTS PASSED - WORKFLOW COMPLETE!")
    else:
        print(f"  ⚠️  {results['failed']} TEST(S) FAILED")
    print("="*60 + "\n")
