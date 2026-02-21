from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models import (
    ReportCard, SkillProgress, Skill, Curriculum, Child,
    WeeklyProgress, ActivityCategory, Enrollment
)
from app.schemas.report_card import ReportCardCreate
from app.utils.enums import SkillLevel, CurriculumType


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
        Creates a frozen snapshot of skills or weekly progress depending on what data exists.
        """
        try:
            # Get child's active enrollment
            enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.child_id == report_data.child_id,
                    Enrollment.status == "ACTIVE"
                )
                .first()
            )

            # Check if child has weekly progress records
            has_weekly_progress = (
                db.query(WeeklyProgress)
                .filter(WeeklyProgress.child_id == report_data.child_id)
                .first()
            ) is not None

            if has_weekly_progress:
                # Generate Grade School weekly progress report
                skill_snapshot = ReportCardService._generate_weekly_progress_snapshot(
                    db, report_data, enrollment
                )
            else:
                # Generate traditional gymnastics skill progress report
                skill_snapshot = ReportCardService._generate_skill_progress_snapshot(
                    db, report_data
                )

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
    def _generate_skill_progress_snapshot(
        db: Session,
        report_data: ReportCardCreate
    ) -> dict:
        """Generate snapshot for traditional gymnastics skill progress"""
        # Get child's current skill progress with related skill/curriculum
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

        # Build skill snapshot and compute summary
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

        return {
            "report_type": "SKILL_PROGRESS",
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

    @staticmethod
    def _generate_weekly_progress_snapshot(
        db: Session,
        report_data: ReportCardCreate,
        enrollment: Optional[Enrollment]
    ) -> dict:
        """Generate snapshot for Grade School weekly progress"""
        # Calculate week range for the report period
        start_date = report_data.period_start
        end_date = report_data.period_end

        if enrollment and enrollment.start_date:
            enrollment_start = enrollment.start_date
            # Calculate week numbers for the period
            start_week = max(1, ((start_date - enrollment_start).days // 7) + 1)
            end_week = ((end_date - enrollment_start).days // 7) + 1
            enrollment_id = enrollment.id
        else:
            # If no enrollment, use date-based filtering
            start_week = None
            end_week = None
            enrollment_id = None

        # Get all weekly progress records in the period
        query = (
            db.query(WeeklyProgress, ActivityCategory)
            .join(ActivityCategory, WeeklyProgress.activity_category_id == ActivityCategory.id)
            .filter(WeeklyProgress.child_id == report_data.child_id)
        )

        if start_week and end_week:
            # Filter by week number if we have enrollment data
            query = query.filter(
                and_(
                    WeeklyProgress.week_number >= start_week,
                    WeeklyProgress.week_number <= end_week
                )
            )
            if enrollment_id:
                query = query.filter(WeeklyProgress.enrollment_id == enrollment_id)
        else:
            # Filter by date range
            query = query.filter(
                and_(
                    WeeklyProgress.week_start_date >= start_date,
                    WeeklyProgress.week_start_date <= end_date
                )
            )

        weekly_records = query.order_by(
            ActivityCategory.display_order,
            WeeklyProgress.week_number
        ).all()

        # Group by activity category
        activities_data = {}
        for progress, activity in weekly_records:
            if activity.id not in activities_data:
                activities_data[activity.id] = {
                    "activity_id": activity.id,
                    "activity_name": activity.name,
                    "category_group": activity.category_group,
                    "measurement_type": activity.measurement_type.value,
                    "measurement_unit": activity.measurement_unit,
                    "weekly_values": []
                }

            # Add weekly value
            value_data = {
                "week_number": progress.week_number,
                "week_start_date": progress.week_start_date.isoformat() if progress.week_start_date else None,
            }

            if progress.progression_level_id:
                # For LEVEL type activities
                value_data["progression_level_id"] = progress.progression_level_id
                value_data["value_type"] = "LEVEL"
            elif progress.numeric_value is not None:
                # For COUNT/TIME/MEASUREMENT type activities
                value_data["numeric_value"] = float(progress.numeric_value)
                value_data["value_type"] = "NUMERIC"

            if progress.notes:
                value_data["notes"] = progress.notes

            activities_data[activity.id]["weekly_values"].append(value_data)

        # Calculate improvements and trends
        activities_list = list(activities_data.values())
        for activity in activities_list:
            if activity["measurement_type"] in ["COUNT", "TIME", "MEASUREMENT"]:
                # Calculate average and trend for numeric activities
                values = [v["numeric_value"] for v in activity["weekly_values"] if "numeric_value" in v]
                if values:
                    activity["average_value"] = round(sum(values) / len(values), 2)
                    if len(values) >= 2:
                        first_val = values[0]
                        last_val = values[-1]
                        if first_val > 0:
                            improvement_pct = round(((last_val - first_val) / first_val) * 100, 1)
                            activity["improvement_percentage"] = improvement_pct

        snapshot = {
            "report_type": "WEEKLY_PROGRESS",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": report_data.period_start.isoformat(),
                "end": report_data.period_end.isoformat()
            },
            "activities": activities_list,
            "summary": {
                "total_activities": len(activities_list),
                "total_records": len(weekly_records)
            }
        }

        # Add week range if available
        if start_week and end_week:
            snapshot["week_range"] = {
                "start_week": start_week,
                "end_week": end_week
            }
            snapshot["summary"]["total_weeks"] = end_week - start_week + 1

        return snapshot

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
