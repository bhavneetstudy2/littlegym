"""
Settings API – Role-based permissions management.
CENTER_ADMIN and SUPER_ADMIN can configure what CENTER_MANAGER, TRAINER,
and COUNSELOR roles are allowed to do within their center.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.utils.enums import UserRole
from app.schemas.role_permission import (
    PermissionDefinition,
    PermissionsConfigResponse,
    RolePermissionsResponse,
    BulkPermissionUpdate,
    MODULE_PERMISSIONS,
    ACTION_PERMISSIONS,
    ALL_PERMISSION_KEYS,
    DEFAULT_PERMISSIONS,
)

router = APIRouter(prefix="/settings", tags=["settings"])

CONFIGURABLE_ROLES = [UserRole.CENTER_MANAGER, UserRole.TRAINER, UserRole.COUNSELOR]


def _get_effective_permissions(db: Session, center_id: int, role: str) -> dict[str, bool]:
    """
    Get the effective permissions for a role at a center.
    Starts with defaults, then applies any stored overrides.
    """
    defaults = DEFAULT_PERMISSIONS.get(role, {})
    effective = {k: defaults.get(k, False) for k in ALL_PERMISSION_KEYS}

    # Apply stored overrides
    stored = (
        db.query(RolePermission)
        .filter(
            RolePermission.center_id == center_id,
            RolePermission.role == role,
        )
        .all()
    )
    for perm in stored:
        if perm.permission_key in effective:
            effective[perm.permission_key] = perm.is_allowed

    return effective


@router.get("/permissions", response_model=PermissionsConfigResponse)
def get_permissions_config(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.CENTER_ADMIN)),
):
    """
    Get the full permissions configuration for a center.
    Returns permission definitions and current values per configurable role.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id is required for SUPER_ADMIN")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Build definitions list
    definitions = []
    for key, label in MODULE_PERMISSIONS.items():
        definitions.append(PermissionDefinition(key=key, label=label, category="module"))
    for key, label in ACTION_PERMISSIONS.items():
        definitions.append(PermissionDefinition(key=key, label=label, category="action"))

    # Build per-role permissions
    roles = []
    for role in CONFIGURABLE_ROLES:
        perms = _get_effective_permissions(db, effective_center_id, role)
        roles.append(RolePermissionsResponse(role=role.value, permissions=perms))

    return PermissionsConfigResponse(definitions=definitions, roles=roles)


@router.put("/permissions")
def update_permissions(
    data: BulkPermissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.CENTER_ADMIN)),
):
    """
    Bulk update permissions for a role at a center.
    Only CENTER_ADMIN (and SUPER_ADMIN) can do this.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = data.center_id
    else:
        effective_center_id = current_user.center_id
        if data.center_id and data.center_id != effective_center_id:
            raise HTTPException(status_code=403, detail="Cannot modify permissions for another center")

    # Validate role
    if data.role not in [r.value for r in CONFIGURABLE_ROLES]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot configure permissions for role: {data.role}. Only CENTER_MANAGER, TRAINER, COUNSELOR are configurable."
        )

    # Validate permission keys
    for key in data.permissions:
        if key not in ALL_PERMISSION_KEYS:
            raise HTTPException(status_code=400, detail=f"Invalid permission key: {key}")

    # Upsert each permission
    for key, is_allowed in data.permissions.items():
        existing = (
            db.query(RolePermission)
            .filter(
                RolePermission.center_id == effective_center_id,
                RolePermission.role == data.role,
                RolePermission.permission_key == key,
            )
            .first()
        )
        if existing:
            existing.is_allowed = is_allowed
        else:
            db.add(RolePermission(
                center_id=effective_center_id,
                role=data.role,
                permission_key=key,
                is_allowed=is_allowed,
            ))

    db.commit()
    return {"status": "ok", "message": f"Permissions updated for {data.role}"}


@router.get("/my-permissions")
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get the current user's effective permissions.
    SUPER_ADMIN and CENTER_ADMIN always get full access.
    Other roles get their configured (or default) permissions.
    """
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN):
        # Full access for admins
        return {"permissions": {k: True for k in ALL_PERMISSION_KEYS}}

    if not current_user.center_id:
        return {"permissions": {k: False for k in ALL_PERMISSION_KEYS}}

    perms = _get_effective_permissions(db, current_user.center_id, current_user.role)
    return {"permissions": perms}
