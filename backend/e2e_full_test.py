"""
End-to-End Test: Enquiry -> Enrollment -> Attendance -> Progress Tracker
Tests the complete lifecycle of a student in the Little Gym CRM
"""
import sys
import json
import httpx
from datetime import date, datetime, timedelta

BASE_URL = "http://localhost:8001"
TOKEN = None
HEADERS = {}

test_state = {
    "center_id": None,
    "lead_id": None,
    "child_id": None,
    "parent_id": None,
    "batch_id": None,
    "enrollment_id": None,
    "session_id": None,
    "curriculum_id": None,
    "skill_ids": [],
    "report_card_id": None,
}

results = {"passed": 0, "failed": 0, "errors": []}


def test(name, func):
    try:
        result = func()
        if result:
            results["passed"] += 1
            print(f"  PASS: {name}")
        else:
            results["failed"] += 1
            results["errors"].append(f"FAIL: {name}")
            print(f"  FAIL: {name}")
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"ERROR: {name} - {e}")
        print(f"  ERROR: {name} - {e}")


def api(method, path, json_data=None, params=None):
    url = f"{BASE_URL}{path}"
    kwargs = {"headers": HEADERS, "timeout": 30}
    if params:
        kwargs["params"] = params
    if method in ("post", "put", "patch") and json_data is not None:
        kwargs["json"] = json_data
    r = getattr(httpx, method)(url, **kwargs)
    if r.status_code >= 400:
        print(f"    HTTP {r.status_code}: {r.text[:300]}")
        return None
    try:
        return r.json()
    except Exception:
        return r.text


# ============================================
# PHASE 1: Authentication
# ============================================
print("\n=== PHASE 1: AUTHENTICATION ===")


def test_login():
    global TOKEN, HEADERS
    data = api("post", "/api/v1/auth/login", {"email": "admin@littlegym.com", "password": "admin123"})
    if data and "access_token" in data:
        TOKEN = data["access_token"]
        HEADERS = {"Authorization": f"Bearer {TOKEN}"}
        return True
    return False


def test_me():
    data = api("get", "/api/v1/auth/me")
    return data and data.get("role") == "SUPER_ADMIN"


def test_login_wrong_password():
    r = httpx.post(f"{BASE_URL}/api/v1/auth/login",
                   json={"email": "admin@littlegym.com", "password": "wrong"}, timeout=10)
    return r.status_code == 401


test("Login with valid credentials", test_login)
test("Get current user (/me)", test_me)
test("Login with wrong password returns 401", test_login_wrong_password)


# ============================================
# PHASE 2: Centers
# ============================================
print("\n=== PHASE 2: CENTERS ===")


def test_list_centers():
    data = api("get", "/api/v1/centers")
    if data and isinstance(data, list) and len(data) > 0:
        test_state["center_id"] = data[0]["id"]
        return True
    return False


def test_get_center():
    data = api("get", f"/api/v1/centers/{test_state['center_id']}")
    return data and "name" in data


test("List centers", test_list_centers)
test("Get center details", test_get_center)


# ============================================
# PHASE 3: LEAD / ENQUIRY FLOW
# ============================================
print("\n=== PHASE 3: LEAD / ENQUIRY FLOW ===")


def test_create_enquiry():
    data = api("post", "/api/v1/leads/enquiry", {
        "center_id": test_state["center_id"],
        "child_first_name": "E2ETest",
        "child_last_name": "Child",
        "child_dob": "2020-03-15",
        "age": 5,
        "gender": "Boy",
        "parent_name": "E2E Test Parent",
        "contact_number": "+919999988888",
        "email": "e2etest@test.com",
        "school": "Test School",
        "source": "WALK_IN",
        "remarks": "E2E test enquiry"
    })
    if data and "id" in data:
        test_state["lead_id"] = data["id"]
        test_state["child_id"] = data.get("child_id")
        return True
    return False


def test_get_leads():
    data = api("get", "/api/v1/leads", params={"center_id": test_state["center_id"]})
    return data is not None and isinstance(data, list)


def test_get_leads_paginated():
    data = api("get", "/api/v1/leads/list/paginated", params={
        "center_id": test_state["center_id"],
        "page": 1,
        "page_size": 10
    })
    return data is not None and "leads" in data


def test_get_lead_details():
    data = api("get", f"/api/v1/leads/{test_state['lead_id']}/details")
    if data:
        if data.get("parents"):
            test_state["parent_id"] = data["parents"][0]["id"]
        return "child" in data or "child_id" in data
    return False


def test_get_lead_activities():
    data = api("get", f"/api/v1/leads/{test_state['lead_id']}/activities")
    return data is not None and isinstance(data, list)


test("Create new enquiry (lead)", test_create_enquiry)
test("List leads", test_get_leads)
test("List leads (paginated)", test_get_leads_paginated)
test("Get lead details", test_get_lead_details)
test("Get lead activities", test_get_lead_activities)


# ============================================
# PHASE 3b: INTRO VISIT FLOW
# ============================================
print("\n=== PHASE 3b: INTRO VISIT FLOW ===")


def test_list_batches():
    data = api("get", "/api/v1/enrollments/batches", params={"center_id": test_state["center_id"]})
    if data and isinstance(data, list) and len(data) > 0:
        test_state["batch_id"] = data[0]["id"]
        return True
    # Create a batch if none exist
    batch_data = api("post", "/api/v1/enrollments/batches", {
        "name": "E2E Test Batch",
        "age_min": 3,
        "age_max": 6,
        "days_of_week": ["Mon", "Wed", "Fri"],
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "capacity": 10,
        "active": True
    }, params={"center_id": test_state["center_id"]})
    if batch_data and "id" in batch_data:
        test_state["batch_id"] = batch_data["id"]
        return True
    return False


def test_schedule_intro_visit():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    data = api("post", f"/api/v1/leads/{test_state['lead_id']}/intro-visit", {
        "lead_id": test_state["lead_id"],
        "scheduled_at": f"{tomorrow}T10:00:00",
        "batch_id": test_state["batch_id"]
    })
    if data and "id" in data:
        test_state["intro_visit_id"] = data["id"]
        return True
    return False


def test_mark_intro_attended():
    data = api("patch", f"/api/v1/leads/intro-visits/{test_state.get('intro_visit_id')}", {
        "attended_at": datetime.now().isoformat(),
        "outcome": "INTERESTED_ENROLL_NOW",
        "outcome_notes": "Child enjoyed the class"
    })
    return data is not None


test("List/create batches", test_list_batches)
test("Schedule intro visit", test_schedule_intro_visit)
test("Mark intro visit attended", test_mark_intro_attended)


# ============================================
# PHASE 3c: FOLLOW-UP FLOW
# ============================================
print("\n=== PHASE 3c: FOLLOW-UP FLOW ===")


def test_create_follow_up():
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    data = api("post", f"/api/v1/leads/{test_state['lead_id']}/follow-up", {
        "lead_id": test_state["lead_id"],
        "scheduled_date": tomorrow,
        "notes": "Follow up after trial class"
    })
    if data and "id" in data:
        test_state["follow_up_id"] = data["id"]
        return True
    return False


def test_get_pending_follow_ups():
    data = api("get", "/api/v1/leads/follow-ups/pending", params={"center_id": test_state["center_id"]})
    return data is not None and isinstance(data, list)


def test_update_follow_up():
    data = api("patch", f"/api/v1/leads/follow-ups/{test_state.get('follow_up_id')}", {
        "outcome": "ENROLLED",
        "notes": "Parent agreed to enroll"
    })
    return data is not None


test("Create follow-up", test_create_follow_up)
test("Get pending follow-ups", test_get_pending_follow_ups)
test("Update follow-up with outcome", test_update_follow_up)


# ============================================
# PHASE 4: ENROLLMENT FLOW
# ============================================
print("\n=== PHASE 4: ENROLLMENT FLOW ===")


def test_create_enrollment():
    today = date.today().isoformat()
    end_date = (date.today() + timedelta(days=90)).isoformat()
    data = api("post", "/api/v1/enrollments", {
        "child_id": test_state["child_id"],
        "batch_id": test_state["batch_id"],
        "plan_type": "QUARTERLY",
        "start_date": today,
        "end_date": end_date,
        "days_selected": ["Mon", "Wed", "Fri"],
        "payment": {
            "amount": 15000,
            "method": "UPI",
            "reference": "UPI-E2E-TEST-001",
            "paid_at": datetime.now().isoformat()
        }
    }, params={
        "center_id": test_state["center_id"],
        "lead_id": test_state["lead_id"]
    })
    if data and "id" in data:
        test_state["enrollment_id"] = data["id"]
        return True
    return False


def test_list_enrollments():
    data = api("get", "/api/v1/enrollments", params={"center_id": test_state["center_id"]})
    return data is not None and isinstance(data, list)


def test_get_enrollment():
    data = api("get", f"/api/v1/enrollments/{test_state['enrollment_id']}")
    return data and data.get("status") == "ACTIVE"


def test_get_enrolled_students():
    data = api("get", "/api/v1/enrollments/students", params={"center_id": test_state["center_id"]})
    return data is not None and isinstance(data, list)


def test_convert_lead():
    # Lead is already auto-converted by the enrollment creation step
    # Verify it's already CONVERTED
    data = api("get", f"/api/v1/leads/{test_state['lead_id']}")
    return data and data.get("status") == "CONVERTED"


def test_get_expiring_enrollments():
    data = api("get", "/api/v1/enrollments/expiring/list", params={
        "center_id": test_state["center_id"],
        "days": 90
    })
    return data is not None and isinstance(data, list)


test("Create enrollment with payment", test_create_enrollment)
test("List enrollments", test_list_enrollments)
test("Get enrollment details", test_get_enrollment)
test("Get enrolled students", test_get_enrolled_students)
test("Convert lead to enrolled", test_convert_lead)
test("Get expiring enrollments", test_get_expiring_enrollments)


# ============================================
# PHASE 5: ATTENDANCE FLOW
# ============================================
print("\n=== PHASE 5: ATTENDANCE FLOW ===")


def test_create_session():
    today = date.today().isoformat()
    data = api("post", "/api/v1/attendance/sessions", {
        "batch_id": test_state["batch_id"],
        "session_date": today,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "status": "SCHEDULED"
    }, params={"center_id": test_state["center_id"]})
    if data and "id" in data:
        test_state["session_id"] = data["id"]
        return True
    return False


def test_list_sessions():
    data = api("get", "/api/v1/attendance/sessions", params={
        "center_id": test_state["center_id"]
    })
    return data is not None and isinstance(data, list)


def test_mark_attendance():
    data = api("post", "/api/v1/attendance/mark", {
        "class_session_id": test_state["session_id"],
        "child_id": test_state["child_id"],
        "status": "PRESENT"
    })
    return data is not None


def test_get_session_attendance():
    data = api("get", f"/api/v1/attendance/sessions/{test_state['session_id']}/attendance")
    return data is not None and isinstance(data, list)


def test_get_child_attendance():
    data = api("get", f"/api/v1/attendance/children/{test_state['child_id']}")
    return data is not None and isinstance(data, list)


def test_get_batch_students():
    data = api("get", f"/api/v1/attendance/batches/{test_state['batch_id']}/students",
               params={"center_id": test_state["center_id"]})
    return data is not None


test("Create class session", test_create_session)
test("List sessions", test_list_sessions)
test("Mark attendance (present)", test_mark_attendance)
test("Get session attendance", test_get_session_attendance)
test("Get child attendance history", test_get_child_attendance)
test("Get batch students", test_get_batch_students)


# ============================================
# PHASE 6: CURRICULUM & PROGRESS TRACKER
# ============================================
print("\n=== PHASE 6: CURRICULUM & PROGRESS TRACKER ===")


def test_create_curriculum():
    data = api("post", "/api/v1/curriculum", {
        "name": "E2E Gymnastics Curriculum",
        "is_global": False,
        "active": True
    })
    if data and "id" in data:
        test_state["curriculum_id"] = data["id"]
        return True
    # Try listing existing
    curricula = api("get", "/api/v1/curriculum", params={"center_id": test_state["center_id"]})
    if curricula and isinstance(curricula, list) and len(curricula) > 0:
        test_state["curriculum_id"] = curricula[0]["id"]
        return True
    return False


def test_list_curricula():
    data = api("get", "/api/v1/curriculum", params={"center_id": test_state["center_id"]})
    return data is not None and isinstance(data, list)


def test_create_skills():
    skills_to_create = [
        {"name": "E2E Cartwheel", "category": "Floor", "display_order": 1, "curriculum_id": test_state["curriculum_id"]},
        {"name": "E2E Forward Roll", "category": "Floor", "display_order": 2, "curriculum_id": test_state["curriculum_id"]},
        {"name": "E2E Monkey Kick", "category": "Bar", "display_order": 3, "curriculum_id": test_state["curriculum_id"]},
    ]
    test_state["skill_ids"] = []
    created = 0
    for skill in skills_to_create:
        data = api("post", "/api/v1/curriculum/skills", skill)
        if data and "id" in data:
            test_state["skill_ids"].append(data["id"])
            created += 1
    if created == 0:
        # Try listing existing skills
        data = api("get", f"/api/v1/curriculum/{test_state['curriculum_id']}/skills")
        if data and isinstance(data, list) and len(data) > 0:
            test_state["skill_ids"] = [s["id"] for s in data[:3]]
            return True
    return created > 0


def test_update_skill_progress():
    if not test_state["skill_ids"]:
        return False
    data = api("post", "/api/v1/curriculum/progress", {
        "child_id": test_state["child_id"],
        "skill_id": test_state["skill_ids"][0],
        "level": "IN_PROGRESS",
        "notes": "Good initial progress"
    }, params={"center_id": test_state["center_id"]})
    return data is not None


def test_bulk_update_progress():
    if len(test_state["skill_ids"]) < 2:
        return False
    progress_items = [
        {"skill_id": test_state["skill_ids"][1], "level": "ACHIEVED", "notes": "Excellent form"},
    ]
    if len(test_state["skill_ids"]) > 2:
        progress_items.append(
            {"skill_id": test_state["skill_ids"][2], "level": "IN_PROGRESS", "notes": "Needs more practice"}
        )
    data = api("post", "/api/v1/curriculum/progress/bulk", {
        "child_id": test_state["child_id"],
        "progress": progress_items
    }, params={"center_id": test_state["center_id"]})
    return data is not None


def test_get_child_progress():
    data = api("get", f"/api/v1/curriculum/progress/children/{test_state['child_id']}")
    return data is not None and isinstance(data, list)


def test_get_progress_summary():
    data = api("get", f"/api/v1/curriculum/progress/children/{test_state['child_id']}/summary")
    return data is not None


test("Create/list curriculum", test_create_curriculum)
test("List curricula", test_list_curricula)
test("Create skills", test_create_skills)
test("Update single skill progress", test_update_skill_progress)
test("Bulk update skill progress", test_bulk_update_progress)
test("Get child progress", test_get_child_progress)
test("Get progress summary", test_get_progress_summary)


# ============================================
# PHASE 7: REPORT CARDS
# ============================================
print("\n=== PHASE 7: REPORT CARDS ===")


def test_generate_report_card():
    start = (date.today() - timedelta(days=30)).isoformat()
    end = date.today().isoformat()
    data = api("post", "/api/v1/report-cards", {
        "child_id": test_state["child_id"],
        "period_start": start,
        "period_end": end,
        "summary_notes": "E2E test report card"
    }, params={"center_id": test_state["center_id"]})
    if data and "id" in data:
        test_state["report_card_id"] = data["id"]
        return True
    return False


def test_list_report_cards():
    data = api("get", "/api/v1/report-cards", params={
        "center_id": test_state["center_id"],
        "child_id": test_state["child_id"]
    })
    return data is not None and isinstance(data, list)


def test_get_report_card():
    if not test_state.get("report_card_id"):
        return False
    data = api("get", f"/api/v1/report-cards/{test_state['report_card_id']}")
    return data is not None and "skill_snapshot" in data


test("Generate report card", test_generate_report_card)
test("List report cards", test_list_report_cards)
test("Get report card details", test_get_report_card)


# ============================================
# PHASE 8: EDGE CASES & STATUS CHECKS
# ============================================
print("\n=== PHASE 8: EDGE CASES & STATUS CHECKS ===")


def test_lead_status_after_conversion():
    data = api("get", f"/api/v1/leads/{test_state['lead_id']}")
    return data and data.get("status") == "CONVERTED"


def test_enrollment_status_active():
    data = api("get", f"/api/v1/enrollments/{test_state['enrollment_id']}")
    return data and data.get("status") == "ACTIVE"


test("Lead status = CONVERTED after conversion", test_lead_status_after_conversion)
test("Enrollment status = ACTIVE", test_enrollment_status_active)


# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 50)
print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
print("=" * 50)

if results["errors"]:
    print("\nFailed tests:")
    for err in results["errors"]:
        print(f"  - {err}")

print(f"\nTest state: {json.dumps(test_state, indent=2, default=str)}")

sys.exit(0 if results["failed"] == 0 else 1)
