from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from app.models import ReportCard, SkillProgress, Skill, Curriculum, Child
from app.schemas.report_card import ReportCardCreate
from app.utils.enums import SkillLevel


class ReportCardService:
    """Service for report card generation and management"""

    @staticmethod
    def generate_report_card(
        db: Session,
        report_data: ReportCardCreate,
        center_id: int,
        generated_by_id: int
    ) -> ReportCard:
        """
        Generate a report card for a child.
        Creates a frozen snapshot of skills at generation time.
        """
        try:
            # Get child's current skill progress with related skill/curriculum in ONE query
            progress_records = (
                db.query(SkillProgress, Skill, Curriculum)
                .join(Skill, SkillProgress.skill_id == Skill.id)
                .join(Curriculum, Skill.curriculum_id == Curriculum.id)
                .filter(
                    SkillProgress.child_id == report_data.child_id,
                    SkillProgress.is_archived == False
                )
                .all()
            )

            # Build skill snapshot and compute summary in one pass
            skills_list = []
            summary_counts = {"not_started": 0, "in_progress": 0, "achieved": 0, "mastered": 0}
            for progress, skill, curriculum in progress_records:
                skills_list.append({
                    "skill_id": progress.skill_id,
                    "skill_name": skill.name,
                    "category": skill.category,
                    "curriculum_name": curriculum.name,
                    "level": progress.level.value,
                    "notes": progress.notes,
                    "last_updated_at": progress.last_updated_at.isoformat() if progress.last_updated_at else None
                })
                level_key = progress.level.value.lower()
                if level_key in summary_counts:
                    summary_counts[level_key] += 1

            skill_snapshot = {
                "generated_at": datetime.utcnow().isoformat(),
                "period": {
                    "start": report_data.period_start.isoformat(),
                    "end": report_data.period_end.isoformat()
                },
                "skills": skills_list,
                "summary": {
                    "total_skills": len(skills_list),
                    **summary_counts
                }
            }

            # Create report card
            report_card = ReportCard(
                center_id=center_id,
                child_id=report_data.child_id,
                period_start=report_data.period_start,
                period_end=report_data.period_end,
                generated_at=datetime.utcnow(),
                generated_by_user_id=generated_by_id,
                summary_notes=report_data.summary_notes,
                skill_snapshot=skill_snapshot,
                created_by_id=generated_by_id,
                updated_by_id=generated_by_id,
            )

            db.add(report_card)
            db.commit()
            db.refresh(report_card)

            return report_card

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_report_cards(
        db: Session,
        center_id: int,
        child_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportCard]:
        """Get report cards with filters"""
        query = db.query(ReportCard).options(
            joinedload(ReportCard.child)
        ).filter(
            ReportCard.center_id == center_id,
            ReportCard.is_archived == False
        )

        if child_id:
            query = query.filter(ReportCard.child_id == child_id)

        return query.order_by(ReportCard.generated_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_report_card_by_id(db: Session, report_card_id: int) -> Optional[ReportCard]:
        """Get a single report card by ID"""
        return db.query(ReportCard).filter(
            ReportCard.id == report_card_id,
            ReportCard.is_archived == False
        ).first()

    @staticmethod
    def regenerate_report_card(
        db: Session,
        report_card_id: int,
        updated_by_id: int
    ) -> ReportCard:
        """Regenerate a report card with current skill data"""
        existing = db.query(ReportCard).filter(
            ReportCard.id == report_card_id
        ).first()

        if not existing:
            raise ValueError("Report card not found")

        # Create new report card with same parameters
        new_report_data = ReportCardCreate(
            child_id=existing.child_id,
            period_start=existing.period_start,
            period_end=existing.period_end,
            summary_notes=existing.summary_notes
        )

        # Archive old report card
        existing.is_archived = True
        existing.updated_by_id = updated_by_id

        # Generate new report card
        new_report = ReportCardService.generate_report_card(
            db=db,
            report_data=new_report_data,
            center_id=existing.center_id,
            generated_by_id=updated_by_id
        )

        return new_report
