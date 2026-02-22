from typing import List, Optional
from datetime import date as date_type
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.child import Child
from app.schemas.enrollment import (
    BatchCreate,
    BatchUpdate,
    BatchResponse,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentDetailResponse,
    PaymentCreate,
    PaymentResponse,
    EnrolledStudentResponse,
    ChildInfo,
    ParentInfo,
    BatchInfo,
)
from app.services.enrollment_service import EnrollmentService
from app.models import Batch, Enrollment, Payment, Child, FamilyLink, Parent
from app.utils.enums import UserRole, EnrollmentStatus
from decimal import Decimal

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


# Batch Endpoints
@router.post("/batches", response_model=BatchResponse)
def create_batch(
    batch_data: BatchCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN))
):
    """Create a new batch"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    batch = Batch(
        center_id=effective_center_id,
        name=batch_data.name,
        age_min=batch_data.age_min,
        age_max=batch_data.age_max,
        days_of_week=batch_data.days_of_week,
        start_time=batch_data.start_time,
        end_time=batch_data.end_time,
        capacity=batch_data.capacity,
        active=batch_data.active,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/batches", response_model=List[BatchResponse])
def get_batches(
    center_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all batches for the center"""
    query = db.query(Batch)

    # Super admin can filter by center_id, others see only their center
    if current_user.role == UserRole.SUPER_ADMIN:
        if center_id:
            query = query.filter(Batch.center_id == center_id)
    else:
        query = query.filter(Batch.center_id == current_user.center_id)

    if active_only:
        query = query.filter(Batch.active == True)

    return query.order_by(Batch.name).all()


@router.patch("/batches/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int,
    batch_data: BatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN))
):
    """Update a batch"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Authorization check
    if current_user.role != UserRole.SUPER_ADMIN and batch.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = batch_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(batch, key, value)
    batch.updated_by_id = current_user.id

    db.commit()
    db.refresh(batch)
    return batch


@router.delete("/batches/{batch_id}")
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN))
):
    """Delete a batch (soft delete by marking inactive, or hard delete if no references)"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Authorization check
    if current_user.role != UserRole.SUPER_ADMIN and batch.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check for references
    from app.models import Enrollment, ClassSession
    from app.models.intro_visit import IntroVisit

    enrollment_count = db.query(Enrollment).filter(Enrollment.batch_id == batch_id).count()
    session_count = db.query(ClassSession).filter(ClassSession.batch_id == batch_id).count()
    iv_count = db.query(IntroVisit).filter(IntroVisit.batch_id == batch_id).count()

    if enrollment_count > 0 or session_count > 0 or iv_count > 0:
        # Soft delete - mark as inactive
        batch.active = False
        batch.updated_by_id = current_user.id
        db.commit()
        return {"detail": "Batch deactivated (has existing references)", "deactivated": True}

    # Hard delete if no references
    db.delete(batch)
    db.commit()
    return {"detail": "Batch deleted", "deactivated": False}


# Enrollment Endpoints
@router.post("", response_model=EnrollmentDetailResponse)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    lead_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.COUNSELOR, UserRole.SUPER_ADMIN))
):
    """Create a new enrollment with payment and optional discount"""
    # Determine center_id: super admin must provide it, others use their assigned center
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    try:
        enrollment = EnrollmentService.create_enrollment(
            db=db,
            enrollment_data=enrollment_data,
            center_id=effective_center_id,
            created_by_id=current_user.id,
            lead_id=lead_id
        )

        # Reload with relationships
        db.refresh(enrollment)
        return enrollment

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[EnrollmentResponse])
def get_enrollments(
    status: Optional[EnrollmentStatus] = Query(None),
    child_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get enrollments with optional filters"""
    # Super admin can filter by center_id, regular users only see their center
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id  # Use provided center_id or None for all
    else:
        effective_center_id = current_user.center_id

    enrollments = EnrollmentService.get_enrollments(
        db=db,
        center_id=effective_center_id,
        status=status,
        child_id=child_id,
        skip=skip,
        limit=limit
    )
    return enrollments


@router.get("/students", response_model=List[EnrolledStudentResponse])
def get_enrolled_students(
    status: Optional[EnrollmentStatus] = Query(None),
    batch_id: Optional[int] = Query(None),
    child_id: Optional[int] = Query(None, description="Filter by specific child ID"),
    search: Optional[str] = Query(None, description="Search by child name, parent name/phone, or enquiry ID"),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all enrolled students with full details using raw SQL (2 queries instead of 500+)"""
    # Determine effective center_id
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Build WHERE clause dynamically
    where_clauses = ["e.is_archived = false"]
    params: dict = {"lim": limit, "off": skip}

    if effective_center_id:
        where_clauses.append("e.center_id = :cid")
        params["cid"] = effective_center_id
    if status:
        where_clauses.append("e.status = :status")
        params["status"] = status.value
    if batch_id:
        where_clauses.append("e.batch_id = :bid")
        params["bid"] = batch_id
    if child_id:
        where_clauses.append("e.child_id = :child_id")
        params["child_id"] = child_id

    if search and search.strip():
        # Build center filter for the subquery too
        sub_center_filter = ""
        if effective_center_id:
            sub_center_filter = "AND e2.center_id = :cid"
        where_clauses.append(f"""e.id IN (
            SELECT DISTINCT e2.id FROM enrollments e2
            JOIN children c2 ON e2.child_id = c2.id
            LEFT JOIN family_links fl ON fl.child_id = c2.id
            LEFT JOIN parents p ON fl.parent_id = p.id
            WHERE (
                c2.first_name ILIKE :search
                OR c2.last_name ILIKE :search
                OR CONCAT(c2.first_name, ' ', c2.last_name) ILIKE :search
                OR c2.enquiry_id ILIKE :search
                OR p.phone ILIKE :search
                OR p.name ILIKE :search
            ) {sub_center_filter}
        )""")
        params["search"] = f"%{search.strip()}%"

    where_sql = " AND ".join(where_clauses)

    # Query 1: Get enrollments + children + batches + payment totals in ONE query
    main_sql = text(f"""
        SELECT
            e.id as enrollment_id, e.plan_type, e.status,
            e.start_date, e.end_date, e.visits_included, e.visits_used,
            e.days_selected, e.notes as enrollment_notes, e.created_at as enrolled_at,
            c.id as child_id, c.enquiry_id, c.first_name, c.last_name, c.dob,
            c.school, c.interests, c.notes as child_notes,
            b.id as batch_id, b.name as batch_name,
            b.age_min, b.age_max, b.days_of_week,
            b.start_time, b.end_time,
            COALESCE(pay.total_paid, 0) as total_paid,
            COALESCE(pay.total_discount, 0) as total_discount
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        LEFT JOIN batches b ON e.batch_id = b.id
        LEFT JOIN (
            SELECT enrollment_id,
                   SUM(amount) as total_paid,
                   SUM(COALESCE(discount_total, 0)) as total_discount
            FROM payments
            GROUP BY enrollment_id
        ) pay ON pay.enrollment_id = e.id
        WHERE {where_sql}
        ORDER BY e.created_at DESC
        LIMIT :lim OFFSET :off
    """)

    rows = db.execute(main_sql, params).fetchall()

    if not rows:
        return []

    # Collect child IDs for parent lookup
    child_ids = list(set(row.child_id for row in rows))

    # Query 2: Get ALL parents for ALL children in one query
    parents_sql = text("""
        SELECT fl.child_id, p.id as parent_id, p.name, p.phone, p.email,
               fl.relationship_type, fl.is_primary_contact
        FROM family_links fl
        JOIN parents p ON fl.parent_id = p.id
        WHERE fl.child_id = ANY(:child_ids)
    """)
    parent_rows = db.execute(parents_sql, {"child_ids": child_ids}).fetchall()

    # Group parents by child_id
    parents_by_child: dict = {}
    for pr in parent_rows:
        if pr.child_id not in parents_by_child:
            parents_by_child[pr.child_id] = []
        parents_by_child[pr.child_id].append(ParentInfo(
            id=pr.parent_id,
            name=pr.name,
            phone=pr.phone,
            email=pr.email,
            relationship_type=pr.relationship_type,
            is_primary_contact=pr.is_primary_contact
        ))

    # Build response from raw rows (no ORM lazy loading)
    results = []
    for row in rows:
        child_info = ChildInfo(
            id=row.child_id,
            enquiry_id=row.enquiry_id,
            first_name=row.first_name,
            last_name=row.last_name,
            dob=row.dob,
            school=row.school,
            interests=row.interests if isinstance(row.interests, list) else (json.loads(row.interests) if row.interests else None),
            notes=row.child_notes
        )

        batch_info = None
        if row.batch_id:
            batch_info = BatchInfo(
                id=row.batch_id,
                name=row.batch_name,
                age_min=row.age_min,
                age_max=row.age_max,
                days_of_week=row.days_of_week if isinstance(row.days_of_week, list) else (json.loads(row.days_of_week) if row.days_of_week else None),
                start_time=row.start_time,
                end_time=row.end_time
            )

        days_selected = row.days_selected
        if days_selected and not isinstance(days_selected, list):
            days_selected = json.loads(days_selected)

        results.append(EnrolledStudentResponse(
            enrollment_id=row.enrollment_id,
            plan_type=row.plan_type,
            status=row.status,
            start_date=row.start_date,
            end_date=row.end_date,
            visits_included=row.visits_included,
            visits_used=row.visits_used,
            days_selected=days_selected,
            enrollment_notes=row.enrollment_notes,
            enrolled_at=row.enrolled_at,
            child=child_info,
            parents=parents_by_child.get(row.child_id, []),
            batch=batch_info,
            total_paid=Decimal(str(row.total_paid)),
            total_discount=Decimal(str(row.total_discount))
        ))

    return results


@router.get("/expiring/list", response_model=List[EnrollmentResponse])
def get_expiring_enrollments(
    days: int = Query(30, ge=1, le=90),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.COUNSELOR))
):
    """Get enrollments expiring within specified days"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    enrollments = EnrollmentService.get_expiring_enrollments(
        db=db,
        center_id=effective_center_id,
        days=days
    )
    return enrollments


class ChildUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date_type] = None
    school: Optional[str] = None
    notes: Optional[str] = None


@router.patch("/children/{child_id}")
def update_child(
    child_id: int,
    data: ChildUpdate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.COUNSELOR))
):
    """Update child info (name, DOB, school, notes)"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    child = db.query(Child).filter(Child.id == child_id, Child.center_id == effective_center_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    child.updated_by_id = current_user.id
    db.commit()
    db.refresh(child)

    return {
        "id": child.id,
        "first_name": child.first_name,
        "last_name": child.last_name,
        "dob": str(child.dob) if child.dob else None,
        "school": child.school,
        "notes": child.notes,
        "enquiry_id": child.enquiry_id,
    }


@router.get("/{enrollment_id}", response_model=EnrollmentDetailResponse)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single enrollment by ID with details"""
    enrollment = EnrollmentService.get_enrollment_by_id(db=db, enrollment_id=enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Check tenant access
    if enrollment.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return enrollment


@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN))
):
    """Update enrollment information (admin only)"""
    enrollment = EnrollmentService.get_enrollment_by_id(db=db, enrollment_id=enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and enrollment.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_enrollment = EnrollmentService.update_enrollment(
            db=db,
            enrollment_id=enrollment_id,
            enrollment_data=enrollment_data,
            updated_by_id=current_user.id
        )
        return updated_enrollment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Payment Endpoints
@router.post("/{enrollment_id}/payments", response_model=PaymentResponse)
def add_payment(
    enrollment_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN))
):
    """Add an additional payment to an enrollment"""
    enrollment = EnrollmentService.get_enrollment_by_id(db=db, enrollment_id=enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if current_user.role != UserRole.SUPER_ADMIN and enrollment.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    effective_center_id = enrollment.center_id if current_user.role == UserRole.SUPER_ADMIN else current_user.center_id

    payment = Payment(
        center_id=effective_center_id,
        enrollment_id=enrollment_id,
        amount=payment_data.amount,
        currency="INR",
        method=payment_data.method,
        reference=payment_data.reference,
        paid_at=payment_data.paid_at,
        discount_total=0,
        net_amount=payment_data.amount,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@router.get("/{enrollment_id}/payments", response_model=List[PaymentResponse])
def get_enrollment_payments(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all payments for an enrollment"""
    enrollment = EnrollmentService.get_enrollment_by_id(db=db, enrollment_id=enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if enrollment.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    payments = db.query(Payment).filter(Payment.enrollment_id == enrollment_id).all()
    return payments
