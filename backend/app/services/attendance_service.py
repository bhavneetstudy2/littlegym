from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models import ClassSession, Attendance, Enrollment, Child, Batch
from app.schemas.attendance import (
    ClassSessionCreate,
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceUpdate
)
from app.utils.enums import AttendanceStatus, EnrollmentStatus, SessionStatus


class AttendanceService:
    """Service for attendance and class session management"""

    @staticmethod
    def create_class_session(
        db: Session,
        session_data: ClassSessionCreate,
        center_id: int,
        created_by_id: int
    ) -> ClassSession:
        """Create a class session"""
        session = ClassSession(
            center_id=center_id,
            batch_id=session_data.batch_id,
            session_date=session_data.session_date,
            start_time=session_data.start_time,
            end_time=session_data.end_time,
            trainer_user_id=session_data.trainer_user_id,
            status=session_data.status,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_sessions(
        db: Session,
        center_id: int,
        session_date: Optional[date] = None,
        batch_id: Optional[int] = None,
        trainer_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassSession]:
        """Get class sessions with filters"""
        query = db.query(ClassSession).filter(
            ClassSession.center_id == center_id,
            ClassSession.is_archived == False
        )

        if session_date:
            query = query.filter(ClassSession.session_date == session_date)

        if batch_id:
            query = query.filter(ClassSession.batch_id == batch_id)

        if trainer_id:
            query = query.filter(ClassSession.trainer_user_id == trainer_id)

        return query.order_by(ClassSession.session_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[ClassSession]:
        """Get a single session by ID"""
        return db.query(ClassSession).filter(
            ClassSession.id == session_id,
            ClassSession.is_archived == False
        ).first()

    @staticmethod
    def mark_attendance(
        db: Session,
        attendance_data: AttendanceCreate,
        center_id: int,
        marked_by_id: int
    ) -> Attendance:
        """Mark attendance for a single student"""
        try:
            # Check if attendance already exists
            existing = db.query(Attendance).filter(
                Attendance.class_session_id == attendance_data.class_session_id,
                Attendance.child_id == attendance_data.child_id,
                Attendance.is_archived == False
            ).first()

            if existing:
                # Update existing attendance
                existing.status = attendance_data.status
                existing.notes = attendance_data.notes
                existing.marked_by_user_id = marked_by_id
                existing.marked_at = datetime.utcnow()
                existing.updated_by_id = marked_by_id
                db.commit()
                db.refresh(existing)
                return existing

            # Create new attendance record
            attendance = Attendance(
                center_id=center_id,
                class_session_id=attendance_data.class_session_id,
                child_id=attendance_data.child_id,
                enrollment_id=attendance_data.enrollment_id,
                status=attendance_data.status,
                notes=attendance_data.notes,
                marked_by_user_id=marked_by_id,
                marked_at=datetime.utcnow(),
                created_by_id=marked_by_id,
                updated_by_id=marked_by_id,
            )
            db.add(attendance)

            # If present, increment visits_used for visit-based plans
            warning = None
            if attendance_data.status == AttendanceStatus.PRESENT and attendance_data.enrollment_id:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.id == attendance_data.enrollment_id
                ).first()
                if enrollment and enrollment.visits_included:
                    # Warn if visits are already exhausted before incrementing
                    if enrollment.visits_used >= enrollment.visits_included:
                        remaining_after = enrollment.visits_included - (enrollment.visits_used + 1)
                        warning = (
                            f"Plan exhausted: {enrollment.visits_used}/{enrollment.visits_included} "
                            f"visits used. This attendance takes it to {remaining_after} remaining. "
                            f"Consider creating a renewal enrollment."
                        )
                    enrollment.visits_used += 1
                    enrollment.updated_by_id = marked_by_id

            db.commit()
            db.refresh(attendance)
            # Store warning on the attendance object for the API layer to access
            if warning:
                attendance._visit_warning = warning
            return attendance

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def mark_bulk_attendance(
        db: Session,
        bulk_data: AttendanceBulkCreate,
        center_id: int,
        marked_by_id: int
    ) -> List[Attendance]:
        """Mark attendance for multiple students at once"""
        try:
            attendance_records = []

            for attendance_item in bulk_data.attendances:
                # Create AttendanceCreate object
                attendance_data = AttendanceCreate(
                    class_session_id=bulk_data.class_session_id,
                    child_id=attendance_item.child_id,
                    enrollment_id=None,  # Will be auto-detected
                    status=attendance_item.status,
                    notes=attendance_item.notes
                )

                # Auto-detect active enrollment
                session = db.query(ClassSession).filter(
                    ClassSession.id == bulk_data.class_session_id
                ).first()

                if session:
                    active_enrollment = db.query(Enrollment).filter(
                        Enrollment.child_id == attendance_item.child_id,
                        Enrollment.batch_id == session.batch_id,
                        Enrollment.status == EnrollmentStatus.ACTIVE,
                        Enrollment.is_archived == False
                    ).first()

                    if active_enrollment:
                        attendance_data.enrollment_id = active_enrollment.id

                # Mark attendance
                attendance = AttendanceService.mark_attendance(
                    db=db,
                    attendance_data=attendance_data,
                    center_id=center_id,
                    marked_by_id=marked_by_id
                )
                attendance_records.append(attendance)

            return attendance_records

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_session_attendance(
        db: Session,
        session_id: int
    ) -> List[Attendance]:
        """Get all attendance records for a session"""
        return db.query(Attendance).filter(
            Attendance.class_session_id == session_id,
            Attendance.is_archived == False
        ).all()

    @staticmethod
    def get_child_attendance(
        db: Session,
        child_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Attendance]:
        """Get attendance history for a child"""
        query = db.query(Attendance).join(ClassSession).options(
            joinedload(Attendance.class_session).joinedload(ClassSession.batch)
        ).filter(
            Attendance.child_id == child_id,
            Attendance.is_archived == False
        )

        if start_date:
            query = query.filter(ClassSession.session_date >= start_date)

        if end_date:
            query = query.filter(ClassSession.session_date <= end_date)

        return query.order_by(ClassSession.session_date.desc()).all()
