"""
CSV Import API endpoints.

All endpoints require CENTER_ADMIN or SUPER_ADMIN role.
Accepts multipart/form-data with a CSV file and a JSON column_mapping body.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.utils.enums import UserRole
from app.schemas.csv_import import (
    CSVPreviewResponse,
    ImportResult,
    LeadsColumnMapping,
    EnrollmentsColumnMapping,
    AttendanceColumnMapping,
    ProgressColumnMapping,
)
from app.services import csv_import_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["csv-import"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _read_upload(file: UploadFile) -> bytes:
    """Read and validate the uploaded CSV file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported. Please upload a .csv file."
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB."
        )
    return contents


def _parse_mapping(mapping_json: str) -> dict:
    """Parse and return the column mapping JSON string."""
    try:
        return json.loads(mapping_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid column_mapping JSON: {e}"
        )


def _effective_center_id(current_user: User, center_id: Optional[int]) -> int:
    """Resolve the effective center_id based on the user's role."""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(
                status_code=400,
                detail="center_id is required for super admin imports"
            )
        return center_id
    return current_user.center_id


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """
    Upload a CSV file and return its column headers plus the first 5 rows.
    This allows the frontend to present a column-mapping UI before the
    actual import.
    """
    contents = await _read_upload(file)
    try:
        preview = csv_import_service.preview_csv(contents)
        return CSVPreviewResponse(**preview)
    except Exception as e:
        logger.error(f"CSV preview error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")


# ---------------------------------------------------------------------------
# Leads Import
# ---------------------------------------------------------------------------

@router.post("/leads", response_model=ImportResult)
async def import_leads(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    center_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """
    Import leads from a mapped CSV file.

    Expects multipart/form-data with:
      - file: the CSV file
      - column_mapping: JSON string mapping target fields to CSV column names
        Example: {"child_first_name": "First Name", "parent_name": "Parent", ...}
      - center_id: (optional, required for super admin) target center ID

    Deduplication: parent phone + child first name.
    """
    contents = await _read_upload(file)
    mapping = _parse_mapping(column_mapping)

    # Validate required mapping fields
    mapping_obj = LeadsColumnMapping(**mapping)
    effective_mapping = mapping_obj.model_dump()

    cid = _effective_center_id(current_user, center_id)

    try:
        result = csv_import_service.import_leads(
            db=db,
            file_bytes=contents,
            column_mapping=effective_mapping,
            center_id=cid,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.error(f"Leads import error: {e}")
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")


# ---------------------------------------------------------------------------
# Enrollments Import
# ---------------------------------------------------------------------------

@router.post("/enrollments", response_model=ImportResult)
async def import_enrollments(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    center_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """
    Import enrollments from a mapped CSV file.

    Expects multipart/form-data with:
      - file: the CSV file
      - column_mapping: JSON string mapping target fields to CSV column names
        Example: {"enquiry_id": "Enquiry ID", "plan_type": "Plan", ...}
      - center_id: (optional, required for super admin) target center ID

    Requires matching an existing child by enquiry_id or child_name.
    """
    contents = await _read_upload(file)
    mapping = _parse_mapping(column_mapping)

    mapping_obj = EnrollmentsColumnMapping(**mapping)
    effective_mapping = mapping_obj.model_dump()

    # At least one child identifier is required
    if not effective_mapping.get("child_name") and not effective_mapping.get("enquiry_id"):
        raise HTTPException(
            status_code=400,
            detail="column_mapping must include either child_name or enquiry_id"
        )

    cid = _effective_center_id(current_user, center_id)

    try:
        result = csv_import_service.import_enrollments(
            db=db,
            file_bytes=contents,
            column_mapping=effective_mapping,
            center_id=cid,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.error(f"Enrollments import error: {e}")
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")


# ---------------------------------------------------------------------------
# Attendance Import
# ---------------------------------------------------------------------------

@router.post("/attendance", response_model=ImportResult)
async def import_attendance(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    center_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """
    Import attendance records from a mapped CSV file.

    Expects multipart/form-data with:
      - file: the CSV file
      - column_mapping: JSON string mapping target fields to CSV column names
        Example: {"enquiry_id": "ID", "session_date": "Date", "status": "Status", ...}
      - center_id: (optional, required for super admin) target center ID

    Requires matching an existing child by enquiry_id or child_name.
    """
    contents = await _read_upload(file)
    mapping = _parse_mapping(column_mapping)

    mapping_obj = AttendanceColumnMapping(**mapping)
    effective_mapping = mapping_obj.model_dump()

    if not effective_mapping.get("child_name") and not effective_mapping.get("enquiry_id"):
        raise HTTPException(
            status_code=400,
            detail="column_mapping must include either child_name or enquiry_id"
        )

    cid = _effective_center_id(current_user, center_id)

    try:
        result = csv_import_service.import_attendance(
            db=db,
            file_bytes=contents,
            column_mapping=effective_mapping,
            center_id=cid,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.error(f"Attendance import error: {e}")
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")


# ---------------------------------------------------------------------------
# Skill Progress Import
# ---------------------------------------------------------------------------

@router.post("/progress", response_model=ImportResult)
async def import_progress(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    center_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """
    Import skill progress records from a mapped CSV file.

    Expects multipart/form-data with:
      - file: the CSV file
      - column_mapping: JSON string mapping target fields to CSV column names
        Example: {"enquiry_id": "ID", "skill_name": "Skill", "level": "Level", ...}
      - center_id: (optional, required for super admin) target center ID

    Requires matching an existing child by enquiry_id or child_name.
    Skills must already exist in the system.
    """
    contents = await _read_upload(file)
    mapping = _parse_mapping(column_mapping)

    mapping_obj = ProgressColumnMapping(**mapping)
    effective_mapping = mapping_obj.model_dump()

    if not effective_mapping.get("child_name") and not effective_mapping.get("enquiry_id"):
        raise HTTPException(
            status_code=400,
            detail="column_mapping must include either child_name or enquiry_id"
        )

    cid = _effective_center_id(current_user, center_id)

    try:
        result = csv_import_service.import_progress(
            db=db,
            file_bytes=contents,
            column_mapping=effective_mapping,
            center_id=cid,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.error(f"Progress import error: {e}")
        raise HTTPException(status_code=400, detail=f"Import failed: {e}")
