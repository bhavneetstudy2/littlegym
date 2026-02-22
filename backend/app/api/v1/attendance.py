from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models import Batch, Child, Enrollment, Attendance, ClassSession
from app.schemas.attendance import (
    ClassSessionCreate,
    ClassSessionUpdate,
    ClassSessionResponse,
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceUpdate,
    AttendanceResponse,
    BatchStudentSummary,
    QuickAttendanceCreate,
)
from app.services.attendance_service import AttendanceService
from app.utils.enums import UserRole, EnrollmentStatus, AttendanceStatus, SessionStatus

router = APIRouter(prefix="/attendance", tags=["attendance"])


# Class Session Endpoints
@router.post("/sessions", response_model=ClassSessionResponse)
def create_class_session(
    session_data: ClassSessionCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.TRAINER))
):
    """Create a class session"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    try:
        session = AttendanceService.create_class_session(
            db=db,
            session_data=session_data,
            center_id=effective_center_id,
            created_by_id=current_user.id
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[ClassSessionResponse])
def get_class_sessions(
    session_date: Optional[date] = Query(None),
    batch_id: Optional[int] = Query(None),
    trainer_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get class sessions with optional filters"""
    # Trainers can only see their own sessions
    if current_user.role == UserRole.TRAINER:
        trainer_id = current_user.id

    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    sessions = AttendanceService.get_sessions(
        db=db,
        center_id=effective_center_id,
        session_date=session_date,
        batch_id=batch_id,
        trainer_id=trainer_id,
        skip=skip,
        limit=limit
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=ClassSessionResponse)
def get_class_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single class session"""
    session = AttendanceService.get_session_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check tenant access
    if session.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return session


# Attendance Endpoints
@router.post("/mark", response_model=AttendanceResponse)
def mark_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER))
):
    """Mark attendance for a single student"""
    # Verify session exists and belongs to center
    session = AttendanceService.get_session_by_id(db=db, session_id=attendance_data.class_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role != UserRole.SUPER_ADMIN and session.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Trainers can only mark attendance for their sessions
    if current_user.role == UserRole.TRAINER:
        if session.trainer_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only mark attendance for your own sessions")

    effective_center_id = session.center_id if current_user.role == UserRole.SUPER_ADMIN else current_user.center_id

    try:
        attendance = AttendanceService.mark_attendance(
            db=db,
            attendance_data=attendance_data,
            center_id=effective_center_id,
            marked_by_id=current_user.id
        )
        # Include visit exhaustion warning if present
        response = AttendanceResponse.model_validate(attendance)
        if hasattr(attendance, '_visit_warning'):
            response.visit_warning = attendance._visit_warning
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mark-bulk", response_model=List[AttendanceResponse])
def mark_bulk_attendance(
    bulk_data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER))
):
    """Mark attendance for multiple students at once"""
    # Verify session exists and belongs to center
    session = AttendanceService.get_session_by_id(db=db, session_id=bulk_data.class_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role != UserRole.SUPER_ADMIN and session.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Trainers can only mark attendance for their sessions
    if current_user.role == UserRole.TRAINER:
        if session.trainer_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only mark attendance for your own sessions")

    effective_center_id = session.center_id if current_user.role == UserRole.SUPER_ADMIN else current_user.center_id

    try:
        attendances = AttendanceService.mark_bulk_attendance(
            db=db,
            bulk_data=bulk_data,
            center_id=effective_center_id,
            marked_by_id=current_user.id
        )
        return attendances
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/attendance", response_model=List[AttendanceResponse])
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attendance records for a session"""
    session = AttendanceService.get_session_by_id(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    attendance_records = AttendanceService.get_session_attendance(db=db, session_id=session_id)
    return attendance_records


@router.get("/children/{child_id}", response_model=List[AttendanceResponse])
def get_child_attendance(
    child_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance history for a child"""
    attendance_records = AttendanceService.get_child_attendance(
        db=db,
        child_id=child_id,
        start_date=start_date,
        end_date=end_date
    )
    return attendance_records


@router.get("/batches/{batch_id}/students", response_model=List[BatchStudentSummary])
def get_batch_students_with_summary(
    batch_id: int,
    center_id: Optional[int] = Query(None),
    include_exhausted: bool = Query(False, description="Include students with exhausted visits"),
    session_date: Optional[date] = Query(None, description="Date to check existing attendance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get students in a batch with attendance summary.
    Excludes exhausted students by default. Pass session_date to include today's attendance in one call."""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Single query: enrollments + children + batch via eager loading
    enrollments = (
        db.query(Enrollment)
        .options(joinedload(Enrollment.child), joinedload(Enrollment.batch))
        .filter(
            Enrollment.batch_id == batch_id,
            Enrollment.center_id == effective_center_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.is_archived == False,
        )
        .all()
    )

    if not enrollments:
        return []

    batch_name = enrollments[0].batch.name if enrollments[0].batch else ""

    # If session_date provided, fetch present child IDs in one joined query
    present_child_ids: set = set()
    if session_date:
        present_records = (
            db.query(Attendance.child_id)
            .join(ClassSession, Attendance.class_session_id == ClassSession.id)
            .filter(
                ClassSession.batch_id == batch_id,
                ClassSession.session_date == session_date,
                ClassSession.center_id == effective_center_id,
                Attendance.status == AttendanceStatus.PRESENT,
            )
            .all()
        )
        present_child_ids = {r[0] for r in present_records}

    results = []
    for enrollment in enrollments:
        child = enrollment.child
        if not child:
            continue

        # If visits_included is NULL, treat as unlimited (date-based plan)
        if enrollment.visits_included is not None:
            classes_remaining = max(0, enrollment.visits_included - (enrollment.visits_used or 0))
        else:
            classes_remaining = 999  # unlimited

        # Skip exhausted students unless explicitly requested
        if not include_exhausted and enrollment.visits_included is not None and classes_remaining <= 0:
            continue

        results.append(BatchStudentSummary(
            child_id=child.id,
            child_name=f"{child.first_name} {child.last_name or ''}".strip(),
            enrollment_id=enrollment.id,
            batch_id=batch_id,
            batch_name=batch_name,
            classes_booked=enrollment.visits_included or 0,
            classes_attended=enrollment.visits_used or 0,
            classes_remaining=classes_remaining,
            last_attendance_date=None,
            enrollment_status=enrollment.status.value,
            is_present_today=child.id in present_child_ids if session_date else None,
        ))

    return sorted(results, key=lambda x: x.child_name)


@router.post("/quick-mark", response_model=List[AttendanceResponse])
def quick_mark_attendance(
    data: QuickAttendanceCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN))
):
    """Quick attendance marking - auto-creates session if needed"""
    # Determine center_id
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Find existing session OR verify batch + create session in one flow
    session = db.query(ClassSession).filter(
        ClassSession.batch_id == data.batch_id,
        ClassSession.session_date == data.session_date,
        ClassSession.center_id == effective_center_id
    ).first()

    if not session:
        # Only query batch if we need to create a session (need start/end time)
        batch = db.query(Batch).filter(Batch.id == data.batch_id, Batch.center_id == effective_center_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        session = ClassSession(
            center_id=effective_center_id,
            batch_id=data.batch_id,
            session_date=data.session_date,
            start_time=batch.start_time,
            end_time=batch.end_time,
            status=SessionStatus.SCHEDULED,
            created_by_id=current_user.id if current_user.id else 1,
            updated_by_id=current_user.id if current_user.id else 1
        )
        db.add(session)
        db.flush()  # Need session.id for attendance records

    # Pre-fetch all child IDs from the request
    child_ids = [att.child_id for att in data.attendances]

    # Batch-fetch existing attendance + enrollments in 2 queries
    existing_records = {
        att_rec.child_id: att_rec
        for att_rec in db.query(Attendance).filter(
            Attendance.class_session_id == session.id,
            Attendance.child_id.in_(child_ids)
        ).all()
    }
    enrollment_map = {
        enr.child_id: enr
        for enr in db.query(Enrollment).filter(
            Enrollment.child_id.in_(child_ids),
            Enrollment.batch_id == data.batch_id,
            Enrollment.center_id == effective_center_id
        ).all()
    }

    # Mark attendance for each child
    results = []
    for att in data.attendances:
        existing = existing_records.get(att.child_id)
        enrollment = enrollment_map.get(att.child_id)

        # UNDO: If marking ABSENT, delete existing record and decrement visits_used
        if att.status == AttendanceStatus.ABSENT:
            if existing:
                was_present = existing.status == AttendanceStatus.PRESENT
                db.delete(existing)
                # Decrement visits_used if was previously PRESENT
                if was_present and enrollment and (enrollment.visits_used or 0) > 0:
                    enrollment.visits_used = (enrollment.visits_used or 0) - 1
            # Return a placeholder response for the deleted record
            now = datetime.utcnow()
            placeholder = Attendance(
                id=existing.id if existing else 0,
                center_id=effective_center_id,
                class_session_id=session.id,
                child_id=att.child_id,
                enrollment_id=enrollment.id if enrollment else None,
                status=AttendanceStatus.ABSENT,
                notes=att.notes,
                marked_by_user_id=current_user.id,
                marked_at=now,
                created_at=now,
                updated_at=now,
                created_by_id=current_user.id if current_user.id else 1,
                updated_by_id=current_user.id if current_user.id else 1,
            )
            results.append(placeholder)
            continue

        if existing:
            existing.status = att.status
            existing.notes = att.notes
            existing.marked_at = datetime.utcnow()
            existing.marked_by_user_id = current_user.id
            results.append(existing)
        else:
            attendance = Attendance(
                center_id=effective_center_id,
                class_session_id=session.id,
                child_id=att.child_id,
                enrollment_id=enrollment.id if enrollment else None,
                status=att.status,
                notes=att.notes,
                marked_by_user_id=current_user.id,
                marked_at=datetime.utcnow(),
                created_by_id=current_user.id if current_user.id else 1,
                updated_by_id=current_user.id if current_user.id else 1
            )
            db.add(attendance)
            results.append(attendance)

            # Update enrollment visits_used if marked PRESENT
            if att.status == AttendanceStatus.PRESENT and enrollment:
                if enrollment.visits_included and enrollment.visits_used >= enrollment.visits_included:
                    attendance._visit_warning = (
                        f"Plan exhausted: {enrollment.visits_used}/{enrollment.visits_included} "
                        f"visits used. Consider creating a renewal enrollment."
                    )
                enrollment.visits_used = (enrollment.visits_used or 0) + 1

    # Commit flushes all pending changes (inserts, updates, deletes) in one round trip
    db.commit()

    # Build responses with warnings
    response_list = []
    for att_record in results:
        resp = AttendanceResponse.model_validate(att_record)
        if hasattr(att_record, '_visit_warning'):
            resp.visit_warning = att_record._visit_warning
        response_list.append(resp)

    return response_list
