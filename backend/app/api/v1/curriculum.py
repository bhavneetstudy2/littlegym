from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.curriculum import (
    CurriculumCreate,
    CurriculumUpdate,
    CurriculumResponse,
    CurriculumWithSkills,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillProgressCreate,
    SkillProgressBulkUpdate,
    SkillProgressUpdate,
    SkillProgressResponse,
    SkillProgressWithDetails,
)
from app.services.curriculum_service import CurriculumService
from app.utils.enums import UserRole

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


# Curriculum Endpoints
@router.post("", response_model=CurriculumResponse)
def create_curriculum(
    curriculum_data: CurriculumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN))
):
    """Create a curriculum (global for super admin, center-specific for center admin)"""
    # Only super admin can create global curricula
    if curriculum_data.is_global and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can create global curricula")

    center_id = None if curriculum_data.is_global else current_user.center_id

    try:
        curriculum = CurriculumService.create_curriculum(
            db=db,
            curriculum_data=curriculum_data,
            center_id=center_id,
            created_by_id=current_user.id
        )
        return curriculum
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[CurriculumResponse])
def get_curricula(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all curricula (global + center-specific for current center)"""
    curricula = CurriculumService.get_curricula(
        db=db,
        center_id=current_user.center_id if current_user.role != UserRole.SUPER_ADMIN else None,
        active_only=active_only
    )
    return curricula


@router.get("/{curriculum_id}", response_model=CurriculumWithSkills)
def get_curriculum(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single curriculum with all its skills"""
    curriculum = CurriculumService.get_curriculum_by_id(db=db, curriculum_id=curriculum_id)
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    # Check access: global curricula are accessible to all, center-specific only to that center
    if not curriculum.is_global and curriculum.center_id != current_user.center_id:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")

    return curriculum


# Skill Endpoints
@router.post("/skills", response_model=SkillResponse)
def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN))
):
    """Add a skill to a curriculum"""
    # Verify curriculum exists and user has access
    curriculum = CurriculumService.get_curriculum_by_id(db=db, curriculum_id=skill_data.curriculum_id)
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    # Check permissions
    if curriculum.is_global and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can modify global curricula")

    if not curriculum.is_global and curriculum.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        skill = CurriculumService.create_skill(
            db=db,
            skill_data=skill_data,
            created_by_id=current_user.id
        )
        return skill
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{curriculum_id}/skills", response_model=List[SkillResponse])
def get_curriculum_skills(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all skills for a curriculum"""
    curriculum = CurriculumService.get_curriculum_by_id(db=db, curriculum_id=curriculum_id)
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")

    # Check access
    if not curriculum.is_global and curriculum.center_id != current_user.center_id:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")

    skills = CurriculumService.get_curriculum_skills(db=db, curriculum_id=curriculum_id)
    return skills


# Skill Progress Endpoints
@router.post("/progress", response_model=SkillProgressResponse)
def update_skill_progress(
    progress_data: SkillProgressCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN))
):
    """Update skill progress for a child"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    try:
        progress = CurriculumService.update_skill_progress(
            db=db,
            child_id=progress_data.child_id,
            skill_id=progress_data.skill_id,
            level=progress_data.level,
            center_id=effective_center_id,
            updated_by_id=current_user.id,
            notes=progress_data.notes
        )
        return progress
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/progress/bulk", response_model=List[SkillProgressResponse])
def bulk_update_skill_progress(
    bulk_data: SkillProgressBulkUpdate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN))
):
    """Update multiple skills for a child at once"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    try:
        progress_records = CurriculumService.bulk_update_skill_progress(
            db=db,
            bulk_data=bulk_data,
            center_id=effective_center_id,
            updated_by_id=current_user.id
        )
        return progress_records
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/progress/children/{child_id}", response_model=List[SkillProgressWithDetails])
def get_child_progress(
    child_id: int,
    curriculum_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all skill progress for a child"""
    progress_records = CurriculumService.get_child_progress(
        db=db,
        child_id=child_id,
        curriculum_id=curriculum_id
    )
    return progress_records


@router.get("/progress/children/{child_id}/summary")
def get_child_progress_summary(
    child_id: int,
    curriculum_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics of child's skill progress"""
    summary = CurriculumService.get_skill_progress_summary(
        db=db,
        child_id=child_id,
        curriculum_id=curriculum_id
    )
    return summary
