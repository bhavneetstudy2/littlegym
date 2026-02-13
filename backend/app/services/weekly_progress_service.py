from typing import Optional, List
from datetime import datetime, date
from math import ceil
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, case
from app.models import (
    ActivityCategory, ProgressionLevel, WeeklyProgress,
    ChildTrainerNotes, Curriculum, Enrollment, Child, Batch
)
from app.schemas.weekly_progress import (
    ActivityCategoryCreate,
    ProgressionLevelCreate,
    WeeklyProgressBulkUpdate,
    ChildTrainerNotesCreate,
    BatchStudentProgressSummary,
    WeeklyProgressWeekSummary,
)


class WeeklyProgressService:
    """Service for weekly progress tracking"""

    # ── Activity Categories ──

    @staticmethod
    def get_activity_categories(
        db: Session,
        curriculum_id: int
    ) -> List[ActivityCategory]:
        """Get activity categories with progression levels for a curriculum"""
        return (
            db.query(ActivityCategory)
            .filter(ActivityCategory.curriculum_id == curriculum_id)
            .options(joinedload(ActivityCategory.progression_levels))
            .order_by(ActivityCategory.display_order, ActivityCategory.name)
            .all()
        )

    @staticmethod
    def create_activity_category(
        db: Session,
        data: ActivityCategoryCreate,
        created_by_id: int
    ) -> ActivityCategory:
        """Create an activity category"""
        category = ActivityCategory(
            curriculum_id=data.curriculum_id,
            name=data.name,
            category_group=data.category_group,
            measurement_type=data.measurement_type,
            measurement_unit=data.measurement_unit,
            display_order=data.display_order,
            description=data.description,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def create_progression_level(
        db: Session,
        data: ProgressionLevelCreate,
        created_by_id: int
    ) -> ProgressionLevel:
        """Add a progression level to an activity category"""
        level = ProgressionLevel(
            activity_category_id=data.activity_category_id,
            level_number=data.level_number,
            name=data.name,
            description=data.description,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.add(level)
        db.commit()
        db.refresh(level)
        return level

    # ── Weekly Progress ──

    @staticmethod
    def get_child_weekly_progress(
        db: Session,
        child_id: int,
        week_number: int,
        enrollment_id: Optional[int] = None,
    ) -> List[WeeklyProgress]:
        """Get all progress entries for a child for a specific week"""
        query = db.query(WeeklyProgress).filter(
            WeeklyProgress.child_id == child_id,
            WeeklyProgress.week_number == week_number,
        )
        if enrollment_id:
            query = query.filter(WeeklyProgress.enrollment_id == enrollment_id)

        return (
            query
            .options(
                joinedload(WeeklyProgress.activity_category)
                .joinedload(ActivityCategory.progression_levels),
                joinedload(WeeklyProgress.progression_level),
            )
            .all()
        )

    @staticmethod
    def get_child_all_weeks(
        db: Session,
        child_id: int,
        enrollment_id: Optional[int] = None,
    ) -> List[WeeklyProgressWeekSummary]:
        """Get summary of all recorded weeks for a child"""
        query = db.query(
            WeeklyProgress.week_number,
            WeeklyProgress.week_start_date,
            func.count(WeeklyProgress.id).label("total_activities"),
            func.count(
                case(
                    (WeeklyProgress.progression_level_id.isnot(None), 1),
                    (WeeklyProgress.numeric_value.isnot(None), 1),
                )
            ).label("completed_activities"),
        ).filter(
            WeeklyProgress.child_id == child_id,
        )
        if enrollment_id:
            query = query.filter(WeeklyProgress.enrollment_id == enrollment_id)

        rows = (
            query
            .group_by(WeeklyProgress.week_number, WeeklyProgress.week_start_date)
            .order_by(WeeklyProgress.week_number)
            .all()
        )
        return [
            WeeklyProgressWeekSummary(
                week_number=r.week_number,
                week_start_date=r.week_start_date,
                total_activities=r.total_activities,
                completed_activities=r.completed_activities,
            )
            for r in rows
        ]

    @staticmethod
    def bulk_update_weekly_progress(
        db: Session,
        data: WeeklyProgressBulkUpdate,
        center_id: int,
        updated_by_id: int
    ) -> List[WeeklyProgress]:
        """Bulk upsert weekly progress for one child, one week, multiple activities"""
        try:
            results = []
            for entry in data.entries:
                # Check for existing record
                existing = db.query(WeeklyProgress).filter(
                    WeeklyProgress.child_id == data.child_id,
                    WeeklyProgress.activity_category_id == entry.activity_category_id,
                    WeeklyProgress.week_number == data.week_number,
                    WeeklyProgress.enrollment_id == data.enrollment_id,
                ).first()

                if existing:
                    existing.progression_level_id = entry.progression_level_id
                    existing.numeric_value = entry.numeric_value
                    existing.notes = entry.notes
                    existing.week_start_date = data.week_start_date
                    existing.last_updated_at = datetime.utcnow()
                    existing.updated_by_user_id = updated_by_id
                    existing.updated_by_id = updated_by_id
                    results.append(existing)
                else:
                    wp = WeeklyProgress(
                        center_id=center_id,
                        child_id=data.child_id,
                        enrollment_id=data.enrollment_id,
                        activity_category_id=entry.activity_category_id,
                        week_number=data.week_number,
                        week_start_date=data.week_start_date,
                        progression_level_id=entry.progression_level_id,
                        numeric_value=entry.numeric_value,
                        notes=entry.notes,
                        last_updated_at=datetime.utcnow(),
                        updated_by_user_id=updated_by_id,
                        created_by_id=updated_by_id,
                        updated_by_id=updated_by_id,
                    )
                    db.add(wp)
                    results.append(wp)

            db.commit()
            for r in results:
                db.refresh(r)
            return results

        except Exception as e:
            db.rollback()
            raise e

    # ── Trainer Notes ──

    @staticmethod
    def get_trainer_notes(
        db: Session,
        child_id: int,
        enrollment_id: Optional[int] = None,
    ) -> Optional[ChildTrainerNotes]:
        """Get trainer notes for a child"""
        query = db.query(ChildTrainerNotes).filter(
            ChildTrainerNotes.child_id == child_id,
        )
        if enrollment_id:
            query = query.filter(ChildTrainerNotes.enrollment_id == enrollment_id)
        else:
            query = query.filter(ChildTrainerNotes.enrollment_id.is_(None))
        return query.first()

    @staticmethod
    def upsert_trainer_notes(
        db: Session,
        data: ChildTrainerNotesCreate,
        center_id: int,
        updated_by_id: int,
    ) -> ChildTrainerNotes:
        """Create or update trainer notes"""
        try:
            existing = db.query(ChildTrainerNotes).filter(
                ChildTrainerNotes.child_id == data.child_id,
                ChildTrainerNotes.enrollment_id == data.enrollment_id,
            ).first()

            if existing:
                if data.parent_expectation is not None:
                    existing.parent_expectation = data.parent_expectation
                if data.progress_check is not None:
                    existing.progress_check = data.progress_check
                existing.updated_by_user_id = updated_by_id
                existing.updated_by_id = updated_by_id
                db.commit()
                db.refresh(existing)
                return existing

            notes = ChildTrainerNotes(
                center_id=center_id,
                child_id=data.child_id,
                enrollment_id=data.enrollment_id,
                parent_expectation=data.parent_expectation,
                progress_check=data.progress_check,
                updated_by_user_id=updated_by_id,
                created_by_id=updated_by_id,
                updated_by_id=updated_by_id,
            )
            db.add(notes)
            db.commit()
            db.refresh(notes)
            return notes

        except Exception as e:
            db.rollback()
            raise e

    # ── Batch Summary ──

    @staticmethod
    def get_batch_students_progress_summary(
        db: Session,
        batch_id: int,
        center_id: int,
        curriculum_id: int,
    ) -> List[BatchStudentProgressSummary]:
        """Get all students in a batch with their progress summary"""
        # Get enrolled students in this batch via Enrollment.batch_id
        students = (
            db.query(
                Child.id.label("child_id"),
                Child.first_name,
                Child.last_name,
                Enrollment.id.label("enrollment_id"),
                Enrollment.start_date,
            )
            .join(Enrollment, and_(
                Enrollment.child_id == Child.id,
                Enrollment.status == "ACTIVE",
                Enrollment.batch_id == batch_id,
            ))
            .filter(Child.center_id == center_id)
            .all()
        )

        # Count total activities in curriculum
        total_activities = (
            db.query(func.count(ActivityCategory.id))
            .filter(ActivityCategory.curriculum_id == curriculum_id)
            .scalar() or 0
        )

        today = date.today()
        results = []
        for s in students:
            child_name = s.first_name or ""
            if s.last_name:
                child_name += f" {s.last_name}"

            # Calculate current week
            if s.start_date:
                days_since = (today - s.start_date).days
                current_week = max(1, ceil(days_since / 7))
            else:
                current_week = 1

            # Get latest recorded week for this child
            latest = (
                db.query(func.max(WeeklyProgress.week_number))
                .filter(
                    WeeklyProgress.child_id == s.child_id,
                    WeeklyProgress.enrollment_id == s.enrollment_id,
                )
                .scalar()
            )

            # Count completed activities in latest week
            completed = 0
            if latest:
                completed = (
                    db.query(func.count(WeeklyProgress.id))
                    .filter(
                        WeeklyProgress.child_id == s.child_id,
                        WeeklyProgress.enrollment_id == s.enrollment_id,
                        WeeklyProgress.week_number == latest,
                        (WeeklyProgress.progression_level_id.isnot(None))
                        | (WeeklyProgress.numeric_value.isnot(None)),
                    )
                    .scalar() or 0
                )

            results.append(BatchStudentProgressSummary(
                child_id=s.child_id,
                child_name=child_name.strip(),
                enrollment_id=s.enrollment_id,
                enrollment_start_date=s.start_date,
                current_week=current_week,
                latest_recorded_week=latest,
                total_activities=total_activities,
                completed_activities=completed,
            ))

        return sorted(results, key=lambda x: x.child_name)
