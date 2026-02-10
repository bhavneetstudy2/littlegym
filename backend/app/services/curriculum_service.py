from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Curriculum, Skill, SkillProgress, Child
from app.schemas.curriculum import (
    CurriculumCreate,
    CurriculumUpdate,
    SkillCreate,
    SkillUpdate,
    SkillProgressCreate,
    SkillProgressBulkUpdate,
    SkillProgressUpdate
)
from app.utils.enums import SkillLevel


class CurriculumService:
    """Service for curriculum and skill progress management"""

    @staticmethod
    def create_curriculum(
        db: Session,
        curriculum_data: CurriculumCreate,
        center_id: Optional[int] = None,
        created_by_id: int = None
    ) -> Curriculum:
        """Create a curriculum (global or center-specific)"""
        curriculum = Curriculum(
            name=curriculum_data.name,
            description=curriculum_data.description,
            center_id=center_id if not curriculum_data.is_global else None,
            is_global=curriculum_data.is_global,
            active=curriculum_data.active,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.add(curriculum)
        db.commit()
        db.refresh(curriculum)
        return curriculum

    @staticmethod
    def get_curricula(
        db: Session,
        center_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[Curriculum]:
        """Get curricula (global or for specific center)"""
        query = db.query(Curriculum)

        if center_id:
            # Get global curricula + center-specific curricula
            query = query.filter(
                (Curriculum.is_global == True) | (Curriculum.center_id == center_id)
            )
        else:
            # Super admin sees all
            pass

        if active_only:
            query = query.filter(Curriculum.active == True)

        return query.order_by(Curriculum.name).all()

    @staticmethod
    def get_curriculum_by_id(db: Session, curriculum_id: int) -> Optional[Curriculum]:
        """Get a single curriculum by ID"""
        return db.query(Curriculum).filter(Curriculum.id == curriculum_id).first()

    @staticmethod
    def create_skill(
        db: Session,
        skill_data: SkillCreate,
        created_by_id: int
    ) -> Skill:
        """Add a skill to a curriculum"""
        skill = Skill(
            curriculum_id=skill_data.curriculum_id,
            name=skill_data.name,
            category=skill_data.category,
            description=skill_data.description,
            display_order=skill_data.display_order,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def get_curriculum_skills(db: Session, curriculum_id: int) -> List[Skill]:
        """Get all skills for a curriculum"""
        return db.query(Skill).filter(
            Skill.curriculum_id == curriculum_id
        ).order_by(Skill.display_order, Skill.name).all()

    @staticmethod
    def update_skill_progress(
        db: Session,
        child_id: int,
        skill_id: int,
        level: SkillLevel,
        center_id: int,
        updated_by_id: int,
        notes: Optional[str] = None
    ) -> SkillProgress:
        """Update or create skill progress for a child"""
        try:
            # Check if progress record exists
            existing = db.query(SkillProgress).filter(
                SkillProgress.child_id == child_id,
                SkillProgress.skill_id == skill_id,
                SkillProgress.is_archived == False
            ).first()

            if existing:
                # Update existing progress
                existing.level = level
                existing.notes = notes
                existing.last_updated_at = datetime.utcnow()
                existing.updated_by_user_id = updated_by_id
                existing.updated_by_id = updated_by_id
                db.commit()
                db.refresh(existing)
                return existing

            # Create new progress record
            progress = SkillProgress(
                center_id=center_id,
                child_id=child_id,
                skill_id=skill_id,
                level=level,
                notes=notes,
                last_updated_at=datetime.utcnow(),
                updated_by_user_id=updated_by_id,
                created_by_id=updated_by_id,
                updated_by_id=updated_by_id,
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
            return progress

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def bulk_update_skill_progress(
        db: Session,
        bulk_data: SkillProgressBulkUpdate,
        center_id: int,
        updated_by_id: int
    ) -> List[SkillProgress]:
        """Update multiple skills for a child at once"""
        try:
            progress_records = []

            for progress_item in bulk_data.progress:
                progress = CurriculumService.update_skill_progress(
                    db=db,
                    child_id=bulk_data.child_id,
                    skill_id=progress_item.skill_id,
                    level=progress_item.level,
                    center_id=center_id,
                    updated_by_id=updated_by_id,
                    notes=progress_item.notes
                )
                progress_records.append(progress)

            return progress_records

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_child_progress(
        db: Session,
        child_id: int,
        curriculum_id: Optional[int] = None
    ) -> List[SkillProgress]:
        """Get all skill progress for a child"""
        query = db.query(SkillProgress).filter(
            SkillProgress.child_id == child_id,
            SkillProgress.is_archived == False
        )

        if curriculum_id:
            query = query.join(Skill).filter(Skill.curriculum_id == curriculum_id)

        return query.all()

    @staticmethod
    def get_skill_progress_summary(
        db: Session,
        child_id: int,
        curriculum_id: Optional[int] = None
    ) -> dict:
        """Get summary statistics of child's skill progress"""
        progress_records = CurriculumService.get_child_progress(
            db=db,
            child_id=child_id,
            curriculum_id=curriculum_id
        )

        summary = {
            "total_skills": len(progress_records),
            "not_started": len([p for p in progress_records if p.level == SkillLevel.NOT_STARTED]),
            "in_progress": len([p for p in progress_records if p.level == SkillLevel.IN_PROGRESS]),
            "achieved": len([p for p in progress_records if p.level == SkillLevel.ACHIEVED]),
            "mastered": len([p for p in progress_records if p.level == SkillLevel.MASTERED]),
        }

        return summary
