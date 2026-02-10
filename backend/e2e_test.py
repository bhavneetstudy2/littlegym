"""End-to-end test script for Little Gym CRM API"""
import requests
import json
from datetime import datetime, timedelta

BASE = "http://localhost:8000/api/v1"

# Login
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@littlegym.com", "password": "admin123"})
assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
user = r.json()["user"]
print(f"[OK] Login: {user['name']} ({user['role']})")

# Health check
r = requests.get("http://localhost:8000/health")
assert r.status_code == 200
print(f"[OK] Health: {r.json()}")

# Auth/me
r = requests.get(f"{BASE}/auth/me", headers=headers)
assert r.status_code == 200
print(f"[OK] Auth/me: {r.json()['name']}")

# Centers
r = requests.get(f"{BASE}/centers", headers=headers)
assert r.status_code == 200
centers = r.json()
print(f"[OK] Centers: {len(centers)} found")

# Center Stats
for c in centers:
    r = requests.get(f"{BASE}/centers/{c['id']}/stats", headers=headers)
    if r.status_code == 200:
        stats = r.json()
        print(f"[OK] Center {c['id']} stats: leads={stats['total_leads']}, enrollments={stats['active_enrollments']}, batches={stats['total_batches']}")
    else:
        print(f"[FAIL] Center {c['id']} stats: {r.status_code}")

# Use center 3 (Chandigarh) which has the most data
CENTER_ID = 3
lead_id = None
child_id = None
enrollment_id = None
batch_id = None

# Create Lead
print("\n--- LEAD CREATION ---")
lead_data = {
    "child_first_name": "E2E Test",
    "child_last_name": "Child",
    "child_dob": "2020-06-15",
    "child_school": "Test School",
    "child_interests": ["gymnastics"],
    "parents": [
        {
            "name": "E2E Test Parent",
            "phone": "+91 99999 00099",
            "email": "e2e.test@example.com"
        }
    ],
    "center_id": CENTER_ID,
    "source": "WALK_IN",
    "discovery_notes": "E2E automated test"
}
r = requests.post(f"{BASE}/leads", headers=headers, json=lead_data)
if r.status_code in [200, 201]:
    lead = r.json()
    lead_id = lead["id"]
    print(f"[OK] Lead created: id={lead_id}, status={lead['status']}")
else:
    print(f"[FAIL] Create lead: {r.status_code} - {r.text[:200]}")
    lead_id = None

# Get Lead Details
if lead_id:
    r = requests.get(f"{BASE}/leads/{lead_id}/details", headers=headers)
    if r.status_code == 200:
        details = r.json()
        child_id = details.get("child_id") or details.get("child", {}).get("id")
        print(f"[OK] Lead details: child_id={child_id}")
    else:
        print(f"[FAIL] Lead details: {r.status_code} - {r.text[:200]}")
        child_id = None

# Schedule Intro Visit
if lead_id:
    print("\n--- INTRO VISIT ---")
    visit_data = {
        "lead_id": lead_id,
        "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat(),
        "outcome_notes": "E2E test visit"
    }
    r = requests.post(f"{BASE}/intro-visits?center_id={CENTER_ID}", headers=headers, json=visit_data)
    if r.status_code in [200, 201]:
        visit = r.json()
        visit_id = visit["id"]
        print(f"[OK] Intro visit scheduled: id={visit_id}")

        # Check lead status updated
        r = requests.get(f"{BASE}/leads/{lead_id}", headers=headers)
        if r.status_code == 200:
            print(f"[OK] Lead status after scheduling: {r.json()['status']}")

        # Mark attended
        r = requests.patch(f"{BASE}/intro-visits/{visit_id}/mark-attended", headers=headers, json={
            "attended_at": datetime.now().isoformat(),
            "outcome_notes": "Child enjoyed it"
        })
        if r.status_code == 200:
            print(f"[OK] Intro visit marked attended")
        else:
            print(f"[FAIL] Mark attended: {r.status_code} - {r.text[:200]}")

        # Check lead status
        r = requests.get(f"{BASE}/leads/{lead_id}", headers=headers)
        if r.status_code == 200:
            print(f"[OK] Lead status after attendance: {r.json()['status']}")
    else:
        print(f"[FAIL] Intro visit: {r.status_code} - {r.text[:200]}")

# Follow up
if lead_id:
    print("\n--- FOLLOW UP ---")
    r = requests.patch(f"{BASE}/leads/{lead_id}", headers=headers, json={
        "status": "FOLLOW_UP",
        "discovery_notes": "Parent interested, discussing pricing"
    })
    if r.status_code == 200:
        print(f"[OK] Lead updated to FOLLOW_UP: {r.json()['status']}")
    else:
        print(f"[FAIL] Follow up: {r.status_code} - {r.text[:200]}")

# Get Batches
print("\n--- BATCHES ---")
r = requests.get(f"{BASE}/enrollments/batches", headers=headers, params={"center_id": CENTER_ID})
batches = r.json() if r.status_code == 200 else []
print(f"[OK] Batches: {len(batches)} found")
batch_id = batches[0]["id"] if batches else None
if batch_id:
    print(f"[OK] Using batch: {batches[0]['name']} (id={batch_id})")

# Create Enrollment
if child_id and batch_id:
    print("\n--- ENROLLMENT ---")
    enrollment_data = {
        "child_id": child_id,
        "plan_type": "MONTHLY",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "days_selected": ["Mon", "Wed", "Fri"],
        "batch_id": batch_id,
        "payment": {
            "amount": 5000,
            "method": "UPI",
            "reference": "TEST-E2E-TXN-001",
            "paid_at": datetime.now().isoformat()
        },
        "notes": "E2E test enrollment"
    }
    r = requests.post(f"{BASE}/enrollments?center_id={CENTER_ID}", headers=headers, json=enrollment_data)
    if r.status_code in [200, 201]:
        enrollment = r.json()
        enrollment_id = enrollment["id"]
        print(f"[OK] Enrollment created: id={enrollment_id}, status={enrollment['status']}")
    else:
        print(f"[FAIL] Enrollment: {r.status_code} - {r.text[:300]}")
        enrollment_id = None
else:
    enrollment_id = None

# Check students list
if enrollment_id:
    print("\n--- STUDENTS ---")
    r = requests.get(f"{BASE}/enrollments/students", headers=headers, params={"center_id": CENTER_ID})
    if r.status_code == 200:
        students = r.json()
        test_student = [s for s in students if s.get("child", {}).get("first_name") == "E2E Test"]
        print(f"[OK] Students: {len(students)} total, test student found: {len(test_student) > 0}")
    else:
        print(f"[FAIL] Students: {r.status_code}")

# Attendance
if enrollment_id and batch_id and child_id:
    print("\n--- ATTENDANCE ---")
    session_data = {
        "batch_id": batch_id,
        "session_date": datetime.now().strftime("%Y-%m-%d"),
        "start_time": "10:00",
        "end_time": "11:00"
    }
    r = requests.post(f"{BASE}/attendance/sessions?center_id={CENTER_ID}", headers=headers, json=session_data)
    if r.status_code in [200, 201]:
        session = r.json()
        session_id = session["id"]
        print(f"[OK] Session created: id={session_id}")

        # Mark attendance
        att_data = {
            "class_session_id": session_id,
            "child_id": child_id,
            "enrollment_id": enrollment_id,
            "status": "PRESENT",
            "notes": "E2E test"
        }
        r = requests.post(f"{BASE}/attendance/mark", headers=headers, json=att_data)
        if r.status_code in [200, 201]:
            print(f"[OK] Attendance marked: {r.json()['status']}")
        else:
            print(f"[FAIL] Mark attendance: {r.status_code} - {r.text[:300]}")

        # Get session attendance
        r = requests.get(f"{BASE}/attendance/sessions/{session_id}/attendance", headers=headers)
        if r.status_code == 200:
            print(f"[OK] Session attendance: {len(r.json())} records")

        # Get child attendance
        r = requests.get(f"{BASE}/attendance/children/{child_id}", headers=headers, params={"center_id": CENTER_ID})
        if r.status_code == 200:
            print(f"[OK] Child attendance history: {len(r.json())} records")
        else:
            print(f"[FAIL] Child attendance: {r.status_code} - {r.text[:200]}")

        # Get batch students
        r = requests.get(f"{BASE}/attendance/batches/{batch_id}/students", headers=headers, params={"center_id": CENTER_ID})
        if r.status_code == 200:
            print(f"[OK] Batch students: {len(r.json())} records")
        else:
            print(f"[FAIL] Batch students: {r.status_code} - {r.text[:200]}")
    else:
        print(f"[FAIL] Session: {r.status_code} - {r.text[:300]}")

# Curriculum & Progress
if child_id:
    print("\n--- CURRICULUM & PROGRESS ---")
    r = requests.get(f"{BASE}/curriculum", headers=headers)
    if r.status_code == 200:
        curricula = r.json()
        print(f"[OK] Curricula: {len(curricula)} found")
        if curricula:
            cid = curricula[0]["id"]
            r2 = requests.get(f"{BASE}/curriculum/{cid}/skills", headers=headers)
            if r2.status_code == 200:
                skills = r2.json()
                print(f"[OK] Skills: {len(skills)} in curriculum '{curricula[0]['name']}'")
                if skills:
                    # Update skill progress
                    progress_data = {
                        "child_id": child_id,
                        "skill_id": skills[0]["id"],
                        "level": "IN_PROGRESS",
                        "notes": "E2E test"
                    }
                    r3 = requests.post(f"{BASE}/curriculum/progress?center_id={CENTER_ID}", headers=headers, json=progress_data)
                    if r3.status_code in [200, 201]:
                        print(f"[OK] Skill progress updated: {skills[0]['name']} -> IN_PROGRESS")
                    else:
                        print(f"[FAIL] Skill progress: {r3.status_code} - {r3.text[:200]}")

                    # Get child progress
                    r4 = requests.get(f"{BASE}/curriculum/progress/children/{child_id}", headers=headers)
                    if r4.status_code == 200:
                        print(f"[OK] Child progress: {len(r4.json())} skills tracked")

                    # Get progress summary
                    r5 = requests.get(f"{BASE}/curriculum/progress/children/{child_id}/summary", headers=headers)
                    if r5.status_code == 200:
                        print(f"[OK] Progress summary: {r5.json()}")
                    else:
                        print(f"[FAIL] Progress summary: {r5.status_code} - {r5.text[:200]}")

# Report Cards
if child_id:
    print("\n--- REPORT CARDS ---")
    rc_data = {
        "child_id": child_id,
        "period_start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "period_end": datetime.now().strftime("%Y-%m-%d"),
        "summary_notes": "E2E test report card"
    }
    r = requests.post(f"{BASE}/report-cards?center_id={CENTER_ID}", headers=headers, json=rc_data)
    if r.status_code in [200, 201]:
        rc = r.json()
        rc_id = rc["id"]
        print(f"[OK] Report card generated: id={rc_id}")

        # Get report card
        r2 = requests.get(f"{BASE}/report-cards/{rc_id}", headers=headers)
        if r2.status_code == 200:
            print(f"[OK] Report card retrieved")
        else:
            print(f"[FAIL] Get report card: {r2.status_code}")

        # List report cards
        r3 = requests.get(f"{BASE}/report-cards", headers=headers, params={"center_id": CENTER_ID, "child_id": child_id})
        if r3.status_code == 200:
            print(f"[OK] Report cards list: {len(r3.json())} found")
    else:
        print(f"[FAIL] Report card: {r.status_code} - {r.text[:300]}")

# MDM Class Types (known issue)
print("\n--- MDM CLASS TYPES ---")
r = requests.get(f"{BASE}/mdm/class-types", headers=headers)
if r.status_code == 200:
    print(f"[OK] Class types: {len(r.json())} found")
else:
    print(f"[FAIL] Class types: {r.status_code} - {r.text[:200]}")

# Mark Lead as Dead (test dead lead flow too)
print("\n--- DEAD LEAD FLOW ---")
dead_lead_data = {
    "child_first_name": "Dead Lead",
    "child_last_name": "Test",
    "child_dob": "2019-01-01",
    "parents": [
        {"name": "Dead Lead Parent", "phone": "+91 88888 00001"}
    ],
    "center_id": CENTER_ID,
    "source": "INSTAGRAM",
    "discovery_notes": "Testing dead lead flow"
}
r = requests.post(f"{BASE}/leads", headers=headers, json=dead_lead_data)
if r.status_code in [200, 201]:
    dead_lead = r.json()
    dead_lead_id = dead_lead["id"]
    print(f"[OK] Dead lead created: id={dead_lead_id}")

    r = requests.post(f"{BASE}/leads/{dead_lead_id}/mark-dead", headers=headers, json={
        "reason": "NOT_INTERESTED"
    })
    if r.status_code == 200:
        print(f"[OK] Lead marked dead: {r.json()['status']}")
    else:
        print(f"[FAIL] Mark dead: {r.status_code} - {r.text[:200]}")
else:
    print(f"[FAIL] Dead lead: {r.status_code} - {r.text[:200]}")

# Expiring enrollments (known RBAC issue for SUPER_ADMIN)
print("\n--- EXPIRING ENROLLMENTS (RBAC TEST) ---")
r = requests.get(f"{BASE}/enrollments/expiring/list", headers=headers, params={"days": 30})
if r.status_code == 200:
    print(f"[OK] Expiring enrollments: {len(r.json())} found")
elif r.status_code == 403:
    print(f"[BUG] Expiring endpoint returns 403 for SUPER_ADMIN (RBAC issue)")
else:
    print(f"[FAIL] Expiring: {r.status_code} - {r.text[:200]}")

# Quick attendance
if batch_id and child_id and enrollment_id:
    print("\n--- QUICK ATTENDANCE ---")
    quick_data = {
        "batch_id": batch_id,
        "session_date": datetime.now().strftime("%Y-%m-%d"),
        "attendances": [
            {"child_id": child_id, "status": "PRESENT", "notes": "quick mark test"}
        ]
    }
    r = requests.post(f"{BASE}/attendance/quick-mark?center_id={CENTER_ID}", headers=headers, json=quick_data)
    if r.status_code in [200, 201]:
        print(f"[OK] Quick attendance: {r.json()}")
    else:
        print(f"[FAIL/EXPECTED] Quick attendance: {r.status_code} - {r.text[:200]}")

# Bulk attendance mark
print("\n--- BULK ATTENDANCE ---")
r = requests.get(f"{BASE}/attendance/sessions", headers=headers, params={"center_id": CENTER_ID})
if r.status_code == 200 and r.json():
    latest_session = r.json()[0]
    bulk_data = {
        "class_session_id": latest_session["id"],
        "attendances": [
            {"child_id": child_id, "status": "PRESENT", "notes": "bulk test"}
        ]
    }
    r = requests.post(f"{BASE}/attendance/mark-bulk", headers=headers, json=bulk_data)
    if r.status_code in [200, 201]:
        print(f"[OK] Bulk attendance marked")
    else:
        print(f"[FAIL] Bulk attendance: {r.status_code} - {r.text[:300]}")

print("\n" + "=" * 60)
print("E2E TEST COMPLETE")
print("=" * 60)
