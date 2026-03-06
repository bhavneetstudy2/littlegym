from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role, get_current_user
from app.models.user import User
from app.models import ActivityCategory, ProgressionLevel, Curriculum, BatchMapping, Batch
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


# ──────────────────────────────────────────────
# Curriculum management (center-scoped)
# ──────────────────────────────────────────────

@router.get("/curricula")
def list_curricula(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List curricula visible to the current center (global + center-specific)"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    query = db.query(Curriculum).filter(Curriculum.active == True)
    if effective_center_id:
        query = query.filter(
            (Curriculum.is_global == True) | (Curriculum.center_id == effective_center_id)
        )
    else:
        query = query.filter(Curriculum.is_global == True)

    return query.order_by(Curriculum.name).all()


@router.post("/curricula")
def create_curriculum(
    data: dict,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN)),
):
    """Create a center-specific curriculum"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id required")

    curriculum = Curriculum(
        name=data.get("name"),
        description=data.get("description"),
        level=data.get("level"),
        age_min=data.get("age_min"),
        age_max=data.get("age_max"),
        center_id=effective_center_id,
        is_global=False,
        active=True,
        curriculum_type=data.get("curriculum_type", "GYMNASTICS"),
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    return curriculum


@router.patch("/curricula/{curriculum_id}")
def update_curriculum(
    curriculum_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN)),
):
    """Update a center-specific curriculum"""
    curriculum = db.query(Curriculum).filter(Curriculum.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    if curriculum.is_global and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot edit global curriculum")
    if not curriculum.is_global and curriculum.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    for field in ("name", "description", "level", "age_min", "age_max", "active"):
        if field in data:
            setattr(curriculum, field, data[field])
    curriculum.updated_by_id = current_user.id
    db.commit()
    db.refresh(curriculum)
    return curriculum


@router.delete("/curricula/{curriculum_id}")
def delete_curriculum(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Soft-delete a curriculum (mark inactive)"""
    curriculum = db.query(Curriculum).filter(Curriculum.id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    if curriculum.is_global and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete global curriculum")
    curriculum.active = False
    curriculum.updated_by_id = current_user.id
    db.commit()
    return {"ok": True}


# ──────────────────────────────────────────────
# Activity Categories
# ──────────────────────────────────────────────

@router.get("/activity-categories", response_model=List[ActivityCategoryResponse])
def get_activity_categories(
    curriculum_id: int = Query(...),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Get activity categories with progression levels for a curriculum"""
    query = (
        db.query(ActivityCategory)
        .filter(ActivityCategory.curriculum_id == curriculum_id)
        .options(joinedload(ActivityCategory.progression_levels))
        .order_by(ActivityCategory.display_order, ActivityCategory.name)
    )
    if not include_inactive:
        query = query.filter((ActivityCategory.active == True) | (ActivityCategory.active == None))
    categories = query.all()
    return categories


@router.post("/activity-categories", response_model=ActivityCategoryResponse)
def create_activity_category(
    data: ActivityCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Create an activity category"""
    category = WeeklyProgressService.create_activity_category(
        db=db, data=data, created_by_id=current_user.id,
    )
    return category


@router.patch("/activity-categories/{category_id}")
def update_activity_category(
    category_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Update an activity category (name, group, order, active toggle)"""
    cat = db.query(ActivityCategory).filter(ActivityCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Activity category not found")
    for field in ("name", "category_group", "measurement_type", "measurement_unit", "display_order", "active", "description"):
        if field in data:
            setattr(cat, field, data[field])
    cat.updated_by_id = current_user.id
    db.commit()
    db.refresh(cat)
    # reload progression levels
    db.refresh(cat)
    return cat


@router.delete("/activity-categories/{category_id}")
def delete_activity_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Delete an activity category"""
    cat = db.query(ActivityCategory).filter(ActivityCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Activity category not found")
    db.delete(cat)
    db.commit()
    return {"ok": True}


# ──────────────────────────────────────────────
# Progression Levels
# ──────────────────────────────────────────────

@router.post("/progression-levels", response_model=ProgressionLevelResponse)
def create_progression_level(
    data: ProgressionLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Add a progression level to an activity category"""
    level = WeeklyProgressService.create_progression_level(
        db=db, data=data, created_by_id=current_user.id,
    )
    return level


@router.patch("/levels/{level_id}", response_model=ProgressionLevelResponse)
def update_progression_level(
    level_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Update a progression level"""
    level = db.query(ProgressionLevel).filter(ProgressionLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    for field in ("name", "level_number", "description"):
        if field in data:
            setattr(level, field, data[field])
    level.updated_by_id = current_user.id
    db.commit()
    db.refresh(level)
    return level


@router.delete("/levels/{level_id}")
def delete_progression_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Delete a progression level"""
    level = db.query(ProgressionLevel).filter(ProgressionLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")
    db.delete(level)
    db.commit()
    return {"ok": True}


# ──────────────────────────────────────────────
# Batch-Curriculum Mappings
# ──────────────────────────────────────────────

@router.get("/batch-mappings")
def list_batch_mappings(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all batch-curriculum mappings for a center"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    mappings = (
        db.query(BatchMapping)
        .options(
            joinedload(BatchMapping.batch),
            joinedload(BatchMapping.curriculum),
        )
        .filter(BatchMapping.center_id == effective_center_id)
        .all()
    )
    return [
        {
            "id": m.id,
            "batch_id": m.batch_id,
            "curriculum_id": m.curriculum_id,
            "batch_name": m.batch.name if m.batch else None,
            "curriculum_name": m.curriculum.name if m.curriculum else None,
        }
        for m in mappings
    ]


@router.post("/batch-mappings")
def create_batch_mapping(
    data: dict,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Map a batch to a curriculum (upsert: replace existing mapping for this batch)"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id required")

    batch_id = data.get("batch_id")
    curriculum_id = data.get("curriculum_id")

    # Remove any existing mapping for this batch
    db.query(BatchMapping).filter(
        BatchMapping.batch_id == batch_id,
        BatchMapping.center_id == effective_center_id,
    ).delete()

    mapping = BatchMapping(
        batch_id=batch_id,
        curriculum_id=curriculum_id,
        center_id=effective_center_id,
        is_archived=False,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return {"id": mapping.id, "batch_id": mapping.batch_id, "curriculum_id": mapping.curriculum_id}


@router.delete("/batch-mappings/{mapping_id}")
def delete_batch_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Remove a batch-curriculum mapping"""
    mapping = db.query(BatchMapping).filter(BatchMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()
    return {"ok": True}


@router.delete("/batch-mappings/by-batch/{batch_id}")
def delete_batch_mapping_by_batch(
    batch_id: int,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Remove batch-curriculum mapping by batch id"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    db.query(BatchMapping).filter(
        BatchMapping.batch_id == batch_id,
        BatchMapping.center_id == effective_center_id,
    ).delete()
    db.commit()
    return {"ok": True}


# ──────────────────────────────────────────────
# Weekly Progress
# ──────────────────────────────────────────────

@router.get("/weekly/{child_id}", response_model=List[WeeklyProgressResponse])
def get_child_weekly_progress(
    child_id: int,
    week_number: int = Query(...),
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Get weekly progress for a child for a specific week"""
    return WeeklyProgressService.get_child_weekly_progress(
        db=db, child_id=child_id, week_number=week_number, enrollment_id=enrollment_id,
    )


@router.get("/weekly/{child_id}/all-weeks", response_model=List[WeeklyProgressWeekSummary])
def get_child_all_weeks(
    child_id: int,
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Get summary of all recorded weeks for a child"""
    return WeeklyProgressService.get_child_all_weeks(
        db=db, child_id=child_id, enrollment_id=enrollment_id,
    )


@router.post("/weekly/bulk-update", response_model=List[WeeklyProgressResponse])
def bulk_update_weekly_progress(
    data: WeeklyProgressBulkUpdate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Bulk upsert weekly progress for one child, one week"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id is required")

    return WeeklyProgressService.bulk_update_weekly_progress(
        db=db, data=data, center_id=effective_center_id, updated_by_id=current_user.id,
    )


# ──────────────────────────────────────────────
# Trainer Notes
# ──────────────────────────────────────────────

@router.get("/trainer-notes/{child_id}", response_model=Optional[ChildTrainerNotesResponse])
def get_trainer_notes(
    child_id: int,
    enrollment_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Get trainer notes for a child"""
    return WeeklyProgressService.get_trainer_notes(
        db=db, child_id=child_id, enrollment_id=enrollment_id,
    )


@router.post("/trainer-notes", response_model=ChildTrainerNotesResponse)
def upsert_trainer_notes(
    data: ChildTrainerNotesCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Create or update trainer notes for a child"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id is required")

    return WeeklyProgressService.upsert_trainer_notes(
        db=db, data=data, center_id=effective_center_id, updated_by_id=current_user.id,
    )


# ──────────────────────────────────────────────
# Batch Summary
# ──────────────────────────────────────────────

@router.get("/batch-summary/{batch_id}", response_model=List[BatchStudentProgressSummary])
def get_batch_students_progress_summary(
    batch_id: int,
    curriculum_id: int = Query(...),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    """Get all students in a batch with their progress summary"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id is required")

    return WeeklyProgressService.get_batch_students_progress_summary(
        db=db, batch_id=batch_id, center_id=effective_center_id, curriculum_id=curriculum_id,
    )
