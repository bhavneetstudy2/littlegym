from typing import Optional
from pydantic import BaseModel
from app.utils.enums import UserRole


# ── Permission keys and their display labels ──

MODULE_PERMISSIONS = {
    "module:dashboard": "Dashboard",
    "module:leads": "Leads / Enquiry",
    "module:students": "Students",
    "module:enrollments": "Enrollments",
    "module:attendance": "Attendance",
    "module:progress": "Progress",
    "module:report_cards": "Report Cards",
    "module:renewals": "Renewals",
}

ACTION_PERMISSIONS = {
    "action:create_enrollment": "Create Enrollment",
    "action:edit_student": "Edit Student Details",
    "action:manage_payments": "View / Manage Payments",
    "action:mark_attendance": "Mark Attendance",
    "action:update_progress": "Update Skill Progress",
    "action:generate_report_card": "Generate Report Cards",
    "action:import_data": "Import Data",
}

ALL_PERMISSION_KEYS = list(MODULE_PERMISSIONS.keys()) + list(ACTION_PERMISSIONS.keys())

# ── Default permissions per configurable role ──

DEFAULT_PERMISSIONS: dict[str, dict[str, bool]] = {
    UserRole.CENTER_MANAGER: {
        "module:dashboard": False,
        "module:leads": True,
        "module:students": True,
        "module:enrollments": True,
        "module:attendance": True,
        "module:progress": True,
        "module:report_cards": False,
        "module:renewals": True,
        "action:create_enrollment": True,
        "action:edit_student": True,
        "action:manage_payments": False,
        "action:mark_attendance": True,
        "action:update_progress": True,
        "action:generate_report_card": False,
        "action:import_data": False,
    },
    UserRole.TRAINER: {
        "module:dashboard": False,
        "module:leads": False,
        "module:students": False,
        "module:enrollments": False,
        "module:attendance": True,
        "module:progress": True,
        "module:report_cards": False,
        "module:renewals": False,
        "action:create_enrollment": False,
        "action:edit_student": False,
        "action:manage_payments": False,
        "action:mark_attendance": True,
        "action:update_progress": True,
        "action:generate_report_card": False,
        "action:import_data": False,
    },
    UserRole.COUNSELOR: {
        "module:dashboard": True,
        "module:leads": True,
        "module:students": True,
        "module:enrollments": True,
        "module:attendance": False,
        "module:progress": False,
        "module:report_cards": False,
        "module:renewals": True,
        "action:create_enrollment": True,
        "action:edit_student": True,
        "action:manage_payments": False,
        "action:mark_attendance": False,
        "action:update_progress": False,
        "action:generate_report_card": False,
        "action:import_data": False,
    },
}


# ── Pydantic schemas ──

class PermissionItem(BaseModel):
    permission_key: str
    is_allowed: bool


class RolePermissionsResponse(BaseModel):
    role: str
    permissions: dict[str, bool]


class BulkPermissionUpdate(BaseModel):
    center_id: int
    role: str
    permissions: dict[str, bool]


class PermissionDefinition(BaseModel):
    key: str
    label: str
    category: str  # "module" or "action"


class PermissionsConfigResponse(BaseModel):
    """Returns the full permissions config: definitions + current values per role."""
    definitions: list[PermissionDefinition]
    roles: list[RolePermissionsResponse]
