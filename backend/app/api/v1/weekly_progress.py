from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User
from app.utils.enums import UserRole

from app.schemas.weekly_progress import (
    ActivityCategoryCreate,
    ActivityCategoryResponse,
    ProgressionLevelCreate,
    ProgressionLevelResponse,
    WeeklyProgressBulkUpdate,
    WeeklyProgressResponse,
    WeeklyProgressWithDetails,
    WeeklyProgressWeekSummary,
    ChildTrainerNotesCreate,
    ChildTrainerNotesResponse,
    BatchStudentProgressSummary,
)
from app.services.weekly_progress_service import WeeklyProgressService

router = APIRouter(prefix="/progress", tags=["weekly-progress"])


# ── Activity Categories ──

@router.get("/activity-categories", response_model=List[ActivityCategoryResponse])
def get_activity_categories(
    curriculum_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Get activity categories with progression levels for a curriculum"""
    categories = WeeklyProgressService.get_activity_categories(db, curriculum_id)
    return categories


@router.post("/activity-categories", response_model=ActivityCategoryResponse)
def create_activity_category(
    data: ActivityCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN)),
):
    """Create an activity category (admin only)"""
    category = WeeklyProgressService.create_activity_category(
        db=db,
        data=data,
        created_by_id=current_user.id,
    )
    return category


@router.post("/progression-levels", response_model=ProgressionLevelResponse)
def create_progression_level(
    data: ProgressionLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN)),
):
    """Add a progression level to an activity category (admin only)"""
    level = WeeklyProgressService.create_progression_level(
        db=db,
        data=data,
        created_by_id=current_user.id,
    )
    return level


# ── Weekly Progress ──

@router.get("/weekly/{child_id}", response_model=List[WeeklyProgressResponse])
def get_child_weekly_progress(
    child_id: int,
    week_number: int = Query(...),
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Get weekly progress for a child for a specific week"""
    progress = WeeklyProgressService.get_child_weekly_progress(
        db=db,
        child_id=child_id,
        week_number=week_number,
        enrollment_id=enrollment_id,
    )
    return progress


@router.get("/weekly/{child_id}/all-weeks", response_model=List[WeeklyProgressWeekSummary])
def get_child_all_weeks(
    child_id: int,
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Get summary of all recorded weeks for a child"""
    return WeeklyProgressService.get_child_all_weeks(
        db=db,
        child_id=child_id,
        enrollment_id=enrollment_id,
    )


@router.post("/weekly/bulk-update", response_model=List[WeeklyProgressResponse])
def bulk_update_weekly_progress(
    data: WeeklyProgressBulkUpdate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Bulk upsert weekly progress for one child, one week"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="center_id is required",
        )

    results = WeeklyProgressService.bulk_update_weekly_progress(
        db=db,
        data=data,
        center_id=effective_center_id,
        updated_by_id=current_user.id,
    )
    return results


# ── Trainer Notes ──

@router.get("/trainer-notes/{child_id}", response_model=Optional[ChildTrainerNotesResponse])
def get_trainer_notes(
    child_id: int,
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Get trainer notes for a child"""
    notes = WeeklyProgressService.get_trainer_notes(
        db=db,
        child_id=child_id,
        enrollment_id=enrollment_id,
    )
    return notes


@router.post("/trainer-notes", response_model=ChildTrainerNotesResponse)
def upsert_trainer_notes(
    data: ChildTrainerNotesCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Create or update trainer notes for a child"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="center_id is required",
        )

    return WeeklyProgressService.upsert_trainer_notes(
        db=db,
        data=data,
        center_id=effective_center_id,
        updated_by_id=current_user.id,
    )


# ── Batch Summary ──

@router.get("/batch-summary/{batch_id}", response_model=List[BatchStudentProgressSummary])
def get_batch_students_progress_summary(
    batch_id: int,
    curriculum_id: int = Query(...),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN)),
):
    """Get all students in a batch with their progress summary"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="center_id is required",
        )

    return WeeklyProgressService.get_batch_students_progress_summary(
        db=db,
        batch_id=batch_id,
        center_id=effective_center_id,
        curriculum_id=curriculum_id,
    )
