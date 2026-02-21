"""
End-to-End Test: Weekly Progress Tracker Module
Tests the complete weekly progress flow:
  1. Get activity categories for a curriculum
  2. Get batch students progress summary
  3. Bulk update weekly progress for a student
  4. Get child weekly progress for a specific week
  5. Get all weeks summary for a child
  6. Upsert trainer notes
  7. Get trainer notes
  8. Grade school numeric progress
  9. Navigate between weeks (week 1 vs week 2)
  10. Verify data persistence after save
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
    "child_id": None,
    "enrollment_id": None,
    "batch_id": None,
    "gym_curriculum_id": None,
    "gs_curriculum_id": None,
    "gym_categories": [],
    "gs_categories": [],
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
# PHASE 0: Login & Setup
# ============================================
print("\n=== PHASE 0: AUTHENTICATION & SETUP ===")


def test_login():
    global TOKEN, HEADERS
    data = api("post", "/api/v1/auth/login", {"email": "admin@littlegym.com", "password": "admin123"})
    if data and "access_token" in data:
        TOKEN = data["access_token"]
        HEADERS = {"Authorization": f"Bearer {TOKEN}"}
        return True
    return False


def test_get_center():
    data = api("get", "/api/v1/centers")
    if data and len(data) > 0:
        test_state["center_id"] = data[0]["id"]
        return True
    return False


def test_find_curricula():
    """Find the seeded Gymnastics and Grade School curricula"""
    data = api("get", "/api/v1/curriculum", params={"center_id": test_state["center_id"]})
    if not data:
        return False

    for c in data:
        name = c["name"]
        # Exact match for seeded curricula
        if name == "Gymnastics Foundation":
            test_state["gym_curriculum_id"] = c["id"]
        elif name == "Grade School Fitness":
            test_state["gs_curriculum_id"] = c["id"]

    found_gym = test_state["gym_curriculum_id"] is not None
    found_gs = test_state["gs_curriculum_id"] is not None
    if not found_gym:
        print(f"    WARNING: Gymnastics curriculum not found. Available: {[c['name'] for c in data]}")
    if not found_gs:
        print(f"    WARNING: Grade School curriculum not found. Available: {[c['name'] for c in data]}")
    return found_gym and found_gs


def test_find_enrolled_student():
    """Find an active enrollment to test with"""
    data = api("get", "/api/v1/enrollments", params={
        "status": "ACTIVE",
        "center_id": test_state["center_id"]
    })
    if data and len(data) > 0:
        enrollment = data[0]
        test_state["enrollment_id"] = enrollment["id"]
        test_state["child_id"] = enrollment["child_id"]
        test_state["batch_id"] = enrollment.get("batch_id")
        print(f"    Using child_id={enrollment['child_id']}, enrollment_id={enrollment['id']}, batch_id={enrollment.get('batch_id')}")
        return True
    return False


test("Login", test_login)
test("Get center", test_get_center)
test("Find seeded curricula", test_find_curricula)
test("Find enrolled student", test_find_enrolled_student)

# ============================================
# PHASE 1: Activity Categories
# ============================================
print("\n=== PHASE 1: ACTIVITY CATEGORIES ===")


def test_get_gym_categories():
    """Get gymnastics activity categories with progression levels"""
    data = api("get", "/api/v1/progress/activity-categories", params={
        "curriculum_id": test_state["gym_curriculum_id"]
    })
    if not data or len(data) == 0:
        print("    No gymnastics categories found")
        return False

    test_state["gym_categories"] = data
    # Verify structure
    first = data[0]
    has_name = "name" in first
    has_levels = "progression_levels" in first
    has_group = "category_group" in first

    # Count total activities
    print(f"    Found {len(data)} gymnastics activities")

    # Count progression levels
    total_levels = sum(len(c.get("progression_levels", [])) for c in data)
    print(f"    Total progression levels: {total_levels}")

    # Verify we have the expected 16 activities
    has_16 = len(data) >= 16
    if not has_16:
        print(f"    WARNING: Expected 16 activities, got {len(data)}")

    return has_name and has_levels and has_group and has_16


def test_get_gs_categories():
    """Get grade school activity categories (numeric, no progression levels)"""
    data = api("get", "/api/v1/progress/activity-categories", params={
        "curriculum_id": test_state["gs_curriculum_id"]
    })
    if not data or len(data) == 0:
        print("    No grade school categories found")
        return False

    test_state["gs_categories"] = data
    print(f"    Found {len(data)} grade school activities")

    # Verify they are numeric types (COUNT, TIME, MEASUREMENT)
    all_numeric = all(c["measurement_type"] in ("COUNT", "TIME", "MEASUREMENT") for c in data)
    if not all_numeric:
        print(f"    WARNING: Some activities are not numeric: {[(c['name'], c['measurement_type']) for c in data]}")

    # Verify no progression levels on numeric activities
    no_levels = all(len(c.get("progression_levels", [])) == 0 for c in data)

    has_6 = len(data) >= 6
    if not has_6:
        print(f"    WARNING: Expected 6 activities, got {len(data)}")

    return all_numeric and no_levels and has_6


def test_categories_have_progression_levels():
    """Verify gymnastics categories have progression levels with correct structure"""
    cats = test_state["gym_categories"]
    if not cats:
        return False

    # Find Cartwheel - should have multiple levels
    cartwheel = next((c for c in cats if "cartwheel" in c["name"].lower()), None)
    if not cartwheel:
        print("    Cartwheel activity not found")
        return False

    levels = cartwheel.get("progression_levels", [])
    if len(levels) == 0:
        print("    Cartwheel has no progression levels")
        return False

    print(f"    Cartwheel has {len(levels)} levels: {[l['name'] for l in sorted(levels, key=lambda x: x['level_number'])]}")

    # Verify level structure
    first_level = levels[0]
    has_id = "id" in first_level
    has_number = "level_number" in first_level
    has_name = "name" in first_level

    return has_id and has_number and has_name and len(levels) >= 2


def test_categories_grouped():
    """Verify categories have category_group values (Floor Skills, Beam Skills, etc.)"""
    cats = test_state["gym_categories"]
    if not cats:
        return False

    groups = set(c.get("category_group") for c in cats if c.get("category_group"))
    print(f"    Category groups: {groups}")

    # Should have at least 3 groups: Floor, Beam, Bar (and possibly Vault)
    return len(groups) >= 3


test("Get gymnastics activity categories", test_get_gym_categories)
test("Get grade school activity categories", test_get_gs_categories)
test("Categories have progression levels", test_categories_have_progression_levels)
test("Categories are grouped", test_categories_grouped)


# ============================================
# PHASE 2: Batch Summary
# ============================================
print("\n=== PHASE 2: BATCH SUMMARY ===")


def test_batch_summary():
    """Get batch students progress summary"""
    if not test_state["batch_id"]:
        print("    No batch_id available, skipping")
        return False

    data = api("get", f"/api/v1/progress/batch-summary/{test_state['batch_id']}", params={
        "curriculum_id": test_state["gym_curriculum_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    print(f"    Found {len(data)} students in batch")

    if len(data) > 0:
        first = data[0]
        print(f"    First student: child_id={first.get('child_id')}, name={first.get('child_name')}, week={first.get('current_week')}")
        has_fields = all(k in first for k in ["child_id", "child_name", "current_week", "total_activities", "completed_activities"])
        return has_fields

    # Empty batch is OK (might not have students)
    return isinstance(data, list)


test("Get batch students progress summary", test_batch_summary)


# ============================================
# PHASE 3: Weekly Progress CRUD
# ============================================
print("\n=== PHASE 3: WEEKLY PROGRESS CRUD ===")


def test_bulk_update_week1_gym():
    """Bulk update gymnastics progress for week 1"""
    cats = test_state["gym_categories"]
    if not cats or not test_state["child_id"]:
        return False

    # Build entries - set level for first 5 activities
    entries = []
    for i, cat in enumerate(cats[:5]):
        levels = cat.get("progression_levels", [])
        if levels:
            # Pick level 1 (first level)
            sorted_levels = sorted(levels, key=lambda x: x["level_number"])
            entries.append({
                "activity_category_id": cat["id"],
                "progression_level_id": sorted_levels[0]["id"],
                "numeric_value": None,
                "notes": None,
            })

    if len(entries) == 0:
        print("    No entries to submit")
        return False

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday of this week

    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "week_number": 1,
        "week_start_date": week_start.isoformat(),
        "entries": entries,
    }

    data = api("post", "/api/v1/progress/weekly/bulk-update", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    print(f"    Saved {len(data)} progress entries for week 1")

    # Verify response structure
    if len(data) > 0:
        first = data[0]
        return all(k in first for k in ["id", "child_id", "week_number", "activity_category_id", "progression_level_id"])
    return True


def test_bulk_update_week2_gym():
    """Bulk update gymnastics progress for week 2 - advance some levels"""
    cats = test_state["gym_categories"]
    if not cats or not test_state["child_id"]:
        return False

    # Build entries - advance first 3 activities to level 2
    entries = []
    for i, cat in enumerate(cats[:3]):
        levels = cat.get("progression_levels", [])
        if len(levels) >= 2:
            sorted_levels = sorted(levels, key=lambda x: x["level_number"])
            entries.append({
                "activity_category_id": cat["id"],
                "progression_level_id": sorted_levels[1]["id"],  # Level 2
                "numeric_value": None,
                "notes": f"Advanced to level 2",
            })

    if len(entries) == 0:
        print("    No entries to submit")
        return False

    today = date.today()
    week_start = (today - timedelta(days=today.weekday())) + timedelta(days=7)

    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "week_number": 2,
        "week_start_date": week_start.isoformat(),
        "entries": entries,
    }

    data = api("post", "/api/v1/progress/weekly/bulk-update", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    print(f"    Saved {len(data)} progress entries for week 2")
    return len(data) > 0


def test_get_weekly_progress_week1():
    """Get progress for week 1"""
    data = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}", params={
        "week_number": 1,
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    print(f"    Week 1 has {len(data)} entries")

    # Should have 5 entries (we saved 5 in week 1)
    return len(data) >= 5


def test_get_weekly_progress_week2():
    """Get progress for week 2"""
    data = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}", params={
        "week_number": 2,
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    print(f"    Week 2 has {len(data)} entries")

    # Should have 3 entries (we saved 3 in week 2)
    return len(data) >= 3


def test_get_all_weeks():
    """Get all weeks summary for a child"""
    data = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}/all-weeks", params={
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    print(f"    Found {len(data)} weeks")

    # Should have at least 2 weeks (week 1 and week 2)
    if len(data) < 2:
        print(f"    WARNING: Expected at least 2 weeks, got {len(data)}")
        return False

    # Verify structure
    first = data[0]
    has_fields = all(k in first for k in ["week_number", "week_start_date", "total_activities", "completed_activities"])

    # Print summary
    for w in data:
        print(f"    Week {w['week_number']}: {w['completed_activities']}/{w['total_activities']} activities")

    return has_fields


def test_update_overwrites():
    """Verify that bulk update overwrites existing data (upsert)"""
    cats = test_state["gym_categories"]
    if not cats:
        return False

    # Update first activity in week 1 to a different level
    first_cat = cats[0]
    levels = sorted(first_cat.get("progression_levels", []), key=lambda x: x["level_number"])
    if len(levels) < 2:
        print("    Not enough levels to test overwrite")
        return False

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Update to level 2
    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "week_number": 1,
        "week_start_date": week_start.isoformat(),
        "entries": [{
            "activity_category_id": first_cat["id"],
            "progression_level_id": levels[1]["id"],  # Changed from level[0] to level[1]
            "numeric_value": None,
            "notes": "Updated to level 2",
        }],
    }

    data = api("post", "/api/v1/progress/weekly/bulk-update", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    # Now fetch and verify
    check = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}", params={
        "week_number": 1,
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if check is None:
        return False

    # Find the first activity's entry
    entry = next((e for e in check if e["activity_category_id"] == first_cat["id"]), None)
    if not entry:
        print("    Could not find updated entry")
        return False

    updated_correctly = entry["progression_level_id"] == levels[1]["id"]
    has_notes = entry.get("notes") == "Updated to level 2"
    print(f"    Overwrite verified: level_id={entry['progression_level_id']} (expected {levels[1]['id']}), notes='{entry.get('notes')}'")
    return updated_correctly and has_notes


test("Bulk update week 1 (gymnastics)", test_bulk_update_week1_gym)
test("Bulk update week 2 (gymnastics, advance levels)", test_bulk_update_week2_gym)
test("Get weekly progress - week 1", test_get_weekly_progress_week1)
test("Get weekly progress - week 2", test_get_weekly_progress_week2)
test("Get all weeks summary", test_get_all_weeks)
test("Upsert overwrites existing data", test_update_overwrites)


# ============================================
# PHASE 4: Grade School Numeric Progress
# ============================================
print("\n=== PHASE 4: GRADE SCHOOL NUMERIC PROGRESS ===")


def test_bulk_update_grade_school():
    """Update grade school numeric progress (push-ups, sit-ups, etc.)"""
    cats = test_state["gs_categories"]
    if not cats or not test_state["child_id"]:
        return False

    entries = []
    test_values = [15, 20, 10, 12.5, 240, 8.3]  # push-ups, sit-ups, stretches, shuttle, 800m, speed

    for i, cat in enumerate(cats[:6]):
        entries.append({
            "activity_category_id": cat["id"],
            "progression_level_id": None,
            "numeric_value": test_values[i] if i < len(test_values) else 0,
            "notes": None,
        })

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "week_number": 1,
        "week_start_date": week_start.isoformat(),
        "entries": entries,
    }

    data = api("post", "/api/v1/progress/weekly/bulk-update", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    print(f"    Saved {len(data)} grade school entries")

    # Verify numeric values stored correctly
    if len(data) > 0:
        first = data[0]
        has_numeric = first.get("numeric_value") is not None
        no_level = first.get("progression_level_id") is None
        print(f"    First entry: numeric_value={first.get('numeric_value')}, progression_level_id={first.get('progression_level_id')}")
        return has_numeric and no_level
    return True


def test_get_grade_school_progress():
    """Retrieve grade school progress and verify numeric values"""
    cats = test_state["gs_categories"]
    if not cats:
        return False

    data = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}", params={
        "week_number": 1,
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    # Filter to grade school categories
    gs_cat_ids = set(c["id"] for c in cats)
    gs_entries = [e for e in data if e["activity_category_id"] in gs_cat_ids]

    print(f"    Found {len(gs_entries)} grade school entries")

    # Verify numeric values are present
    all_have_values = all(e.get("numeric_value") is not None for e in gs_entries)

    for e in gs_entries:
        cat = next((c for c in cats if c["id"] == e["activity_category_id"]), None)
        cat_name = cat["name"] if cat else "Unknown"
        print(f"    {cat_name}: {e.get('numeric_value')} {cat.get('measurement_unit', '') if cat else ''}")

    return all_have_values and len(gs_entries) >= 6


test("Bulk update grade school numeric progress", test_bulk_update_grade_school)
test("Get grade school progress with numeric values", test_get_grade_school_progress)


# ============================================
# PHASE 5: Trainer Notes
# ============================================
print("\n=== PHASE 5: TRAINER NOTES ===")


def test_upsert_trainer_notes():
    """Create trainer notes for a child"""
    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "parent_expectation": "Parents want the child to improve flexibility and balance",
        "progress_check": "Good progress on floor skills, needs work on beam confidence",
    }

    data = api("post", "/api/v1/progress/trainer-notes", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    has_fields = all(k in data for k in ["id", "child_id", "parent_expectation", "progress_check"])
    print(f"    Created notes id={data.get('id')}")
    return has_fields


def test_get_trainer_notes():
    """Get trainer notes for a child"""
    data = api("get", f"/api/v1/progress/trainer-notes/{test_state['child_id']}", params={
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    has_expectation = data.get("parent_expectation") == "Parents want the child to improve flexibility and balance"
    has_check = data.get("progress_check") == "Good progress on floor skills, needs work on beam confidence"
    print(f"    Expectation: {data.get('parent_expectation', '')[:60]}...")
    print(f"    Progress check: {data.get('progress_check', '')[:60]}...")
    return has_expectation and has_check


def test_update_trainer_notes():
    """Update existing trainer notes (upsert)"""
    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "parent_expectation": "Updated: Focus on handstand progression",
        "progress_check": "Updated: Excellent improvement this month",
    }

    data = api("post", "/api/v1/progress/trainer-notes", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        return False

    updated_exp = data.get("parent_expectation") == "Updated: Focus on handstand progression"
    updated_check = data.get("progress_check") == "Updated: Excellent improvement this month"
    print(f"    Updated notes successfully")
    return updated_exp and updated_check


test("Create trainer notes", test_upsert_trainer_notes)
test("Get trainer notes", test_get_trainer_notes)
test("Update trainer notes (upsert)", test_update_trainer_notes)


# ============================================
# PHASE 6: Edge Cases
# ============================================
print("\n=== PHASE 6: EDGE CASES ===")


def test_empty_week():
    """Get progress for a week with no data"""
    data = api("get", f"/api/v1/progress/weekly/{test_state['child_id']}", params={
        "week_number": 99,
        "enrollment_id": test_state["enrollment_id"],
        "center_id": test_state["center_id"],
    })
    if data is None:
        return False

    print(f"    Week 99 has {len(data)} entries (expected 0)")
    return len(data) == 0


def test_categories_wrong_curriculum():
    """Get categories for non-existent curriculum"""
    data = api("get", "/api/v1/progress/activity-categories", params={
        "curriculum_id": 99999
    })
    if data is None:
        return False

    print(f"    Non-existent curriculum returned {len(data)} categories (expected 0)")
    return len(data) == 0


def test_bulk_update_empty_entries():
    """Bulk update with empty entries list"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    payload = {
        "child_id": test_state["child_id"],
        "enrollment_id": test_state["enrollment_id"],
        "week_number": 50,
        "week_start_date": week_start.isoformat(),
        "entries": [],
    }

    data = api("post", "/api/v1/progress/weekly/bulk-update", json_data=payload, params={
        "center_id": test_state["center_id"]
    })
    if data is None:
        # 422 or empty is acceptable
        return True

    print(f"    Empty entries returned {len(data)} results")
    return len(data) == 0


def test_trainer_notes_nonexistent_child():
    """Get trainer notes for non-existent child"""
    data = api("get", "/api/v1/progress/trainer-notes/99999", params={
        "center_id": test_state["center_id"],
    })
    # Should return null/None (no notes found)
    print(f"    Non-existent child notes: {data}")
    return data is None or data == "null" or data == {}


test("Get empty week (no data)", test_empty_week)
test("Categories for wrong curriculum", test_categories_wrong_curriculum)
test("Bulk update with empty entries", test_bulk_update_empty_entries)
test("Trainer notes for non-existent child", test_trainer_notes_nonexistent_child)


# ============================================
# RESULTS
# ============================================
print("\n" + "=" * 50)
print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
print("=" * 50)

if results["errors"]:
    print("\nFailed tests:")
    for err in results["errors"]:
        print(f"  - {err}")

print(f"\nTest state: {json.dumps(test_state, indent=2, default=str)}")

sys.exit(1 if results["failed"] > 0 else 0)
