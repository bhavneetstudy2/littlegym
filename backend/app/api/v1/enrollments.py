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

    # Duplicate check: same child + same batch + ACTIVE enrollment
    if enrollment_data.batch_id:
        existing = db.query(Enrollment).filter(
            Enrollment.child_id == enrollment_data.child_id,
            Enrollment.batch_id == enrollment_data.batch_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.center_id == effective_center_id,
            Enrollment.is_archived == False,
        ).first()
        if existing:
            # Get child name for error message
            child = db.query(Child).filter(Child.id == enrollment_data.child_id).first()
            child_name = f"{child.first_name} {child.last_name or ''}" if child else f"Child #{enrollment_data.child_id}"
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate: {child_name.strip()} already has an ACTIVE enrollment (#{existing.id}) in this batch. "
                       f"Expire or cancel the existing enrollment first, or choose a different batch."
            )

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
            COALESCE(pay.total_discount, 0) as total_discount,
            c.age_years,
            latest_pay.method as payment_method
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
        LEFT JOIN LATERAL (
            SELECT p2.method::text as method
            FROM payments p2
            WHERE p2.enrollment_id = e.id
            ORDER BY p2.paid_at DESC
            LIMIT 1
        ) latest_pay ON true
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
            age_years=row.age_years,
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
            total_discount=Decimal(str(row.total_discount)),
            payment_method=row.payment_method
        ))

    return results


@router.get("/expiring/list")
def get_expiring_enrollments(
    days: int = Query(30, ge=1, le=90),
    visit_threshold: int = Query(5, ge=1, le=50),
    include_visit_expiring: bool = Query(True),
    include_expired: bool = Query(False),
    search: Optional[str] = Query(None),
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.COUNSELOR))
):
    """Get enrollments expiring by date or visits, with full student details"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Build WHERE conditions
    date_condition = """
        (e.end_date IS NOT NULL AND e.end_date <= :cutoff AND e.end_date >= CURRENT_DATE)
    """
    visit_condition = """
        (e.visits_included IS NOT NULL AND e.visits_included > 0
         AND e.visits_included - e.visits_used <= :visit_threshold
         AND e.visits_included - e.visits_used > 0)
    """

    expired_condition = """
        (e.status = 'EXPIRED' OR (e.status = 'ACTIVE' AND e.visits_included IS NOT NULL
         AND e.visits_used >= e.visits_included))
    """

    if include_expired:
        # Show active expiring + already expired
        if include_visit_expiring:
            expiry_filter = f"(({date_condition} OR {visit_condition}) OR {expired_condition})"
        else:
            expiry_filter = f"({date_condition} OR {expired_condition})"
    else:
        if include_visit_expiring:
            expiry_filter = f"({date_condition} OR {visit_condition})"
        else:
            expiry_filter = date_condition

    search_filter = ""
    params: dict = {
        'cid': effective_center_id,
        'cutoff': f"CURRENT_DATE + INTERVAL '{days} days'",
        'visit_threshold': visit_threshold,
    }

    if search:
        search_filter = """AND (
            LOWER(c.first_name || ' ' || COALESCE(c.last_name, '')) LIKE :search
            OR LOWER(COALESCE(c.enquiry_id, '')) LIKE :search
            OR EXISTS (
                SELECT 1 FROM family_links fl
                JOIN parents p ON fl.parent_id = p.id
                WHERE fl.child_id = c.id
                AND (LOWER(p.name) LIKE :search OR p.phone LIKE :search)
            )
        )"""
        params['search'] = f"%{search.lower()}%"

    sql = f'''
        SELECT
            e.id as enrollment_id, e.child_id, e.batch_id, e.plan_type::text, e.status::text,
            e.start_date, e.end_date, e.visits_included, e.visits_used,
            e.days_selected,
            c.enquiry_id, c.first_name, c.last_name, c.age_years,
            (SELECT p.name FROM family_links fl JOIN parents p ON fl.parent_id = p.id
             WHERE fl.child_id = c.id ORDER BY fl.is_primary_contact DESC LIMIT 1) as parent_name,
            (SELECT p.phone FROM family_links fl JOIN parents p ON fl.parent_id = p.id
             WHERE fl.child_id = c.id ORDER BY fl.is_primary_contact DESC LIMIT 1) as parent_phone,
            b.name as batch_name,
            COALESCE(pay.total_paid, 0) as total_paid,
            CASE WHEN e.end_date IS NOT NULL THEN (e.end_date - CURRENT_DATE) ELSE NULL END as days_remaining,
            CASE WHEN e.visits_included IS NOT NULL AND e.visits_included > 0
                 THEN e.visits_included - e.visits_used ELSE NULL END as visits_remaining
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        LEFT JOIN batches b ON e.batch_id = b.id
        LEFT JOIN LATERAL (
            SELECT SUM(p.amount) as total_paid
            FROM payments p WHERE p.enrollment_id = e.id AND p.is_archived = false
        ) pay ON true
        WHERE e.center_id = :cid
          AND e.status IN ('ACTIVE', 'EXPIRED')
          AND e.is_archived = false
          AND {expiry_filter}
          {search_filter}
        ORDER BY
            COALESCE(e.end_date - CURRENT_DATE, e.visits_included - e.visits_used) ASC NULLS LAST
    '''

    # Use raw SQL with interval expression
    from datetime import timedelta
    cutoff_date = __import__('datetime').date.today() + timedelta(days=days)
    params['cutoff'] = cutoff_date

    rows = db.execute(text(sql), params).fetchall()

    results = []
    for r in rows:
        days_rem = r[18]
        visits_rem = r[19]

        # Determine expiry reason
        date_expiring = days_rem is not None and days_rem <= days
        visits_expiring = visits_rem is not None and visits_rem <= visit_threshold
        if date_expiring and visits_expiring:
            reason = "both"
        elif visits_expiring:
            reason = "visits"
        else:
            reason = "date"

        child_name = r[11]
        if r[12]:
            child_name += f" {r[12]}"

        results.append({
            "enrollment_id": r[0],
            "child_id": r[1],
            "batch_id": r[2],
            "plan_type": r[3],
            "status": r[4],
            "start_date": str(r[5]) if r[5] else None,
            "end_date": str(r[6]) if r[6] else None,
            "visits_included": r[7],
            "visits_used": r[8],
            "days_selected": r[9] if isinstance(r[9], list) else (json.loads(r[9]) if isinstance(r[9], str) else None),
            "enquiry_id": r[10],
            "child_name": child_name,
            "age_years": r[13],
            "parent_name": r[14],
            "parent_phone": r[15],
            "batch_name": r[16],
            "total_paid": float(r[17]) if r[17] else 0,
            "days_remaining": int(days_rem) if days_rem is not None else None,
            "visits_remaining": int(visits_rem) if visits_rem is not None else None,
            "expiry_reason": reason,
        })

    return results


class ChildUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date_type] = None
    age_years: Optional[int] = None
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


# ── Master Students Endpoints ──────────────────────────────────────

@router.get("/master-students/stats")
def get_master_student_stats(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.COUNSELOR))
):
    """Get summary stats for master students view"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    result = db.execute(text('''
        SELECT
            COUNT(DISTINCT c.id) as total,
            COUNT(DISTINCT c.id) FILTER (WHERE sub.enrollment_count = 1) as new_count,
            COUNT(DISTINCT c.id) FILTER (WHERE sub.enrollment_count > 1) as renewal_count
        FROM children c
        INNER JOIN (
            SELECT child_id, COUNT(*) as enrollment_count
            FROM enrollments
            WHERE center_id = :cid AND is_archived = false
            GROUP BY child_id
        ) sub ON sub.child_id = c.id
        WHERE c.center_id = :cid AND c.is_archived = false
    '''), {'cid': effective_center_id}).fetchone()

    # By latest enrollment status
    status_rows = db.execute(text('''
        SELECT latest.status, COUNT(*) as cnt
        FROM (
            SELECT DISTINCT ON (e.child_id) e.child_id, e.status
            FROM enrollments e
            WHERE e.center_id = :cid AND e.is_archived = false
            ORDER BY e.child_id, e.created_at DESC, e.id DESC
        ) latest
        GROUP BY latest.status
    '''), {'cid': effective_center_id}).fetchall()

    by_status = {row[0]: row[1] for row in status_rows}

    return {
        "total": result[0] or 0,
        "new_count": result[1] or 0,
        "renewal_count": result[2] or 0,
        "by_status": by_status,
    }


@router.get("/master-students/list")
def get_master_students(
    center_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    batch_id: Optional[int] = Query(None),
    enrollment_status: Optional[str] = Query(None),
    enrollment_type: Optional[str] = Query(None, description="'new' or 'renewal'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.COUNSELOR))
):
    """Get child-centric master students list with enrollment aggregates"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Build WHERE clauses
    where_clauses = ["c.center_id = :cid", "c.is_archived = false"]
    params: dict = {'cid': effective_center_id}

    if search:
        where_clauses.append("""(
            LOWER(c.first_name || ' ' || COALESCE(c.last_name, '')) LIKE :search
            OR LOWER(c.enquiry_id) LIKE :search
            OR EXISTS (
                SELECT 1 FROM family_links fl
                JOIN parents p ON fl.parent_id = p.id
                WHERE fl.child_id = c.id
                AND (LOWER(p.name) LIKE :search OR p.phone LIKE :search)
            )
        )""")
        params['search'] = f"%{search.lower()}%"

    if batch_id:
        where_clauses.append("latest_e.batch_id = :batch_id")
        params['batch_id'] = batch_id

    if enrollment_status:
        where_clauses.append("latest_e.status = :estatus")
        params['estatus'] = enrollment_status

    where_sql = " AND ".join(where_clauses)

    # Having clause for new/renewal filter
    having_clause = ""
    if enrollment_type == 'new':
        having_clause = "HAVING COUNT(e.id) = 1"
    elif enrollment_type == 'renewal':
        having_clause = "HAVING COUNT(e.id) > 1"

    # Count query
    count_sql = f'''
        SELECT COUNT(*) FROM (
            SELECT c.id
            FROM children c
            INNER JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false AND e.center_id = :cid
            INNER JOIN LATERAL (
                SELECT e2.id, e2.status, e2.batch_id, e2.plan_type,
                       e2.start_date, e2.end_date, e2.visits_included, e2.visits_used, e2.created_at
                FROM enrollments e2
                WHERE e2.child_id = c.id AND e2.is_archived = false AND e2.center_id = :cid
                ORDER BY e2.created_at DESC, e2.id DESC
                LIMIT 1
            ) latest_e ON true
            WHERE {where_sql}
            GROUP BY c.id, latest_e.id, latest_e.status, latest_e.batch_id, latest_e.plan_type,
                     latest_e.start_date, latest_e.end_date, latest_e.visits_included,
                     latest_e.visits_used, latest_e.created_at
            {having_clause}
        ) sub
    '''
    total = db.execute(text(count_sql), params).scalar() or 0

    offset = (page - 1) * page_size

    # Main query
    main_sql = f'''
        SELECT
            c.id as child_id, c.enquiry_id, c.first_name, c.last_name, c.dob,
            c.age_years, c.school, c.notes as child_notes,
            COUNT(e.id) as enrollment_count,
            latest_e.id as latest_enrollment_id,
            latest_e.plan_type, latest_e.status as latest_status,
            latest_e.start_date, latest_e.end_date,
            latest_e.visits_included, latest_e.visits_used,
            latest_e.batch_id, latest_e.created_at as latest_enrolled_at,
            b.id as batch_id_out, b.name as batch_name,
            b.age_min as batch_age_min, b.age_max as batch_age_max,
            b.days_of_week as batch_days, b.start_time as batch_start, b.end_time as batch_end,
            COALESCE(pay.total_paid, 0) as total_paid,
            l.source as lead_source, l.converted_at
        FROM children c
        INNER JOIN enrollments e ON e.child_id = c.id AND e.is_archived = false AND e.center_id = :cid
        INNER JOIN LATERAL (
            SELECT e2.id, e2.status, e2.batch_id, e2.plan_type,
                   e2.start_date, e2.end_date, e2.visits_included, e2.visits_used, e2.created_at
            FROM enrollments e2
            WHERE e2.child_id = c.id AND e2.is_archived = false AND e2.center_id = :cid
            ORDER BY e2.created_at DESC, e2.id DESC
            LIMIT 1
        ) latest_e ON true
        LEFT JOIN batches b ON latest_e.batch_id = b.id
        LEFT JOIN LATERAL (
            SELECT SUM(p.amount) as total_paid
            FROM payments p
            JOIN enrollments e3 ON p.enrollment_id = e3.id
            WHERE e3.child_id = c.id AND e3.center_id = :cid AND p.is_archived = false
        ) pay ON true
        LEFT JOIN leads l ON l.child_id = c.id AND l.center_id = :cid AND l.status = 'CONVERTED'
        WHERE {where_sql}
        GROUP BY c.id, c.enquiry_id, c.first_name, c.last_name, c.dob,
                 c.age_years, c.school, c.notes,
                 latest_e.id, latest_e.plan_type, latest_e.status,
                 latest_e.start_date, latest_e.end_date,
                 latest_e.visits_included, latest_e.visits_used,
                 latest_e.batch_id, latest_e.created_at,
                 b.id, b.name, b.age_min, b.age_max, b.days_of_week::text, b.start_time, b.end_time,
                 pay.total_paid, l.source, l.converted_at
        {having_clause}
        ORDER BY c.first_name, c.last_name
        LIMIT :limit OFFSET :offset
    '''
    params['limit'] = page_size
    params['offset'] = offset

    rows = db.execute(text(main_sql), params).fetchall()

    # Batch-fetch parents
    child_ids = [row[0] for row in rows]
    parent_map: dict = {}
    if child_ids:
        parent_rows = db.execute(text('''
            SELECT fl.child_id, p.id, p.name, p.phone, p.email,
                   fl.relationship_type, fl.is_primary_contact
            FROM family_links fl
            JOIN parents p ON fl.parent_id = p.id
            WHERE fl.child_id = ANY(:child_ids)
            ORDER BY fl.is_primary_contact DESC
        '''), {'child_ids': child_ids}).fetchall()
        for pr in parent_rows:
            parent_map.setdefault(pr[0], []).append({
                "id": pr[1],
                "name": pr[2],
                "phone": pr[3],
                "email": pr[4],
                "relationship_type": pr[5],
                "is_primary_contact": pr[6],
            })

    # Build response
    students = []
    for row in rows:
        child_id = row[0]
        enrollment_count = row[8]
        batch_info = None
        if row[18]:  # batch_id_out
            batch_info = {
                "id": row[18], "name": row[19],
                "age_min": row[20], "age_max": row[21],
                "days_of_week": json.loads(row[22]) if isinstance(row[22], str) else row[22],
                "start_time": str(row[23]) if row[23] else None,
                "end_time": str(row[24]) if row[24] else None,
            }

        students.append({
            "child": {
                "id": child_id, "enquiry_id": row[1],
                "first_name": row[2], "last_name": row[3],
                "dob": str(row[4]) if row[4] else None,
                "age_years": row[5], "school": row[6], "notes": row[7],
            },
            "parents": parent_map.get(child_id, []),
            "enrollment_count": enrollment_count,
            "is_renewal": enrollment_count > 1,
            "latest_enrollment_id": row[9],
            "latest_plan_type": row[10],
            "latest_status": row[11],
            "latest_start_date": str(row[12]) if row[12] else None,
            "latest_end_date": str(row[13]) if row[13] else None,
            "latest_visits_included": row[14],
            "latest_visits_used": row[15] or 0,
            "latest_batch": batch_info,
            "latest_enrolled_at": str(row[17]) if row[17] else None,
            "total_paid": float(row[25]) if row[25] else 0,
            "lead_source": row[26],
            "converted_at": str(row[27]) if row[27] else None,
        })

    import math
    return {
        "students": students,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.post("/fix-stale-leads")
def fix_stale_leads(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.CENTER_ADMIN))
):
    """One-time fix: Convert leads whose children already have enrollments but lead status was never updated."""
    from app.models.lead import Lead
    from app.utils.enums import LeadStatus

    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Find leads that are NOT converted but whose child has an enrollment
    # Match 1: Direct child_id match
    # Match 2: Parent phone match (handles duplicate child records from imports)
    stale_leads = db.execute(text('''
        SELECT combined.lead_id, combined.child_id, combined.status, combined.matched_enrollment_id
        FROM (
            -- Match by same child_id
            SELECT l.id as lead_id, l.child_id, l.status,
                   (SELECT e.id FROM enrollments e
                    WHERE e.child_id = l.child_id AND e.center_id = :cid AND e.is_archived = false
                    ORDER BY e.created_at DESC LIMIT 1) as matched_enrollment_id
            FROM leads l
            WHERE l.center_id = :cid
              AND l.is_archived = false
              AND l.status != :converted
              AND EXISTS (
                  SELECT 1 FROM enrollments e
                  WHERE e.child_id = l.child_id AND e.center_id = :cid AND e.is_archived = false
              )

            UNION

            -- Match by parent phone (handles duplicate children from imports)
            -- Uses RIGHT(digits, 10) to normalize phone numbers (strip country code/formatting)
            SELECT DISTINCT ON (l.id) l.id as lead_id, l.child_id, l.status,
                   (SELECT e.id FROM enrollments e
                    JOIN family_links fl2 ON fl2.child_id = e.child_id
                    JOIN parents p2 ON p2.id = fl2.parent_id
                    WHERE RIGHT(regexp_replace(p2.phone, '[^0-9]', '', 'g'), 10)
                        = RIGHT(regexp_replace(p.phone, '[^0-9]', '', 'g'), 10)
                      AND e.center_id = :cid AND e.is_archived = false
                    ORDER BY e.created_at DESC LIMIT 1) as matched_enrollment_id
            FROM leads l
            JOIN family_links fl ON fl.child_id = l.child_id
            JOIN parents p ON p.id = fl.parent_id AND p.phone IS NOT NULL AND p.phone != ''
            WHERE l.center_id = :cid
              AND l.is_archived = false
              AND l.status != :converted
              AND NOT EXISTS (
                  SELECT 1 FROM enrollments e
                  WHERE e.child_id = l.child_id AND e.center_id = :cid AND e.is_archived = false
              )
              AND EXISTS (
                  SELECT 1 FROM enrollments e
                  JOIN family_links fl2 ON fl2.child_id = e.child_id
                  JOIN parents p2 ON p2.id = fl2.parent_id
                  WHERE RIGHT(regexp_replace(p2.phone, '[^0-9]', '', 'g'), 10)
                      = RIGHT(regexp_replace(p.phone, '[^0-9]', '', 'g'), 10)
                    AND e.center_id = :cid AND e.is_archived = false
              )
        ) combined
        WHERE combined.matched_enrollment_id IS NOT NULL
    '''), {'cid': effective_center_id, 'converted': LeadStatus.CONVERTED.value}).fetchall()

    fixed = []
    for row in stale_leads:
        lead = db.query(Lead).filter(Lead.id == row[0]).first()
        if lead:
            old_status = lead.status.value if lead.status else None
            lead.status = LeadStatus.CONVERTED
            lead.enrollment_id = row[3]
            lead.converted_at = date_type.today()
            lead.updated_by_id = current_user.id
            fixed.append({
                "lead_id": row[0],
                "child_id": row[1],
                "old_status": old_status,
                "enrollment_id": row[3]
            })

    db.commit()
    return {"fixed_count": len(fixed), "fixed_leads": fixed}


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
    current_user: User = Depends(require_role(UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER))
):
    """Update enrollment information (admin/manager)"""
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


