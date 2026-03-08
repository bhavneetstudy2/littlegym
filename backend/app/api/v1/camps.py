from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel as PydanticModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models import Camp, CampEnrollment, Child
from app.models.camp_enrollment import CampEnrollmentStatus
from app.utils.enums import UserRole

router = APIRouter(prefix="/camps", tags=["camps"])


# ── Pydantic schemas ────────────────────────────────────────────────────────

class CampCreate(PydanticModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    capacity: Optional[int] = None
    price: Optional[float] = None


class CampUpdate(PydanticModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    capacity: Optional[int] = None
    price: Optional[float] = None
    active: Optional[bool] = None


class CampEnrollCreate(PydanticModel):
    is_existing_student: bool
    child_id: Optional[int] = None          # if existing student
    child_name: Optional[str] = None        # if new student
    child_dob: Optional[date] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    notes: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_method: Optional[str] = None


def _camp_status(camp: Camp) -> str:
    today = date.today()
    if today < camp.start_date:
        return "UPCOMING"
    if today > camp.end_date:
        return "COMPLETED"
    return "ACTIVE"


def _camp_out(camp: Camp, db: Session) -> dict:
    enrolled = db.query(CampEnrollment).filter(
        CampEnrollment.camp_id == camp.id,
        CampEnrollment.status == CampEnrollmentStatus.ENROLLED,
        CampEnrollment.is_archived == False,
    ).count()
    return {
        "id": camp.id,
        "center_id": camp.center_id,
        "name": camp.name,
        "description": camp.description,
        "start_date": str(camp.start_date),
        "end_date": str(camp.end_date),
        "capacity": camp.capacity,
        "price": float(camp.price) if camp.price is not None else None,
        "active": camp.active,
        "status": _camp_status(camp),
        "enrolled_count": enrolled,
    }


def _enrollment_out(e: CampEnrollment) -> dict:
    child_name = e.child_name
    if e.is_existing_student and e.child:
        child_name = f"{e.child.first_name or ''} {e.child.last_name or ''}".strip()
    return {
        "id": e.id,
        "camp_id": e.camp_id,
        "is_existing_student": e.is_existing_student,
        "child_id": e.child_id,
        "child_name": child_name,
        "child_dob": str(e.child_dob) if e.child_dob else None,
        "parent_name": e.parent_name if not e.is_existing_student else None,
        "parent_phone": e.parent_phone if not e.is_existing_student else None,
        "parent_email": e.parent_email if not e.is_existing_student else None,
        "notes": e.notes,
        "status": e.status,
        "payment_amount": float(e.payment_amount) if e.payment_amount is not None else None,
        "payment_method": e.payment_method,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# ── Camp CRUD ───────────────────────────────────────────────────────────────

@router.get("")
def list_camps(
    center_id: Optional[int] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    q = db.query(Camp)
    if effective_center_id:
        q = q.filter(Camp.center_id == effective_center_id)
    if not include_inactive:
        q = q.filter(Camp.active == True)
    q = q.filter(Camp.is_archived == False).order_by(Camp.start_date.desc())
    camps = q.all()
    return [_camp_out(c, db) for c in camps]


@router.post("")
def create_camp(
    data: CampCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id required")

    if data.end_date < data.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    camp = Camp(
        center_id=effective_center_id,
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        capacity=data.capacity,
        price=data.price,
        active=True,
        is_archived=False,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)
    return _camp_out(camp, db)


@router.patch("/{camp_id}")
def update_camp(
    camp_id: int,
    data: CampUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    camp = db.query(Camp).filter(Camp.id == camp_id, Camp.is_archived == False).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    for field in ("name", "description", "start_date", "end_date", "capacity", "price", "active"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(camp, field, val)

    camp.updated_by_id = current_user.id
    db.commit()
    db.refresh(camp)
    return _camp_out(camp, db)


@router.delete("/{camp_id}")
def delete_camp(
    camp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN
    )),
):
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")
    camp.is_archived = True
    camp.updated_by_id = current_user.id
    db.commit()
    return {"ok": True}


# ── Camp Enrollments ────────────────────────────────────────────────────────

@router.get("/{camp_id}/enrollments")
def list_camp_enrollments(
    camp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollments = (
        db.query(CampEnrollment)
        .options(joinedload(CampEnrollment.child))
        .filter(
            CampEnrollment.camp_id == camp_id,
            CampEnrollment.is_archived == False,
        )
        .order_by(CampEnrollment.created_at)
        .all()
    )
    return [_enrollment_out(e) for e in enrollments]


@router.post("/{camp_id}/enrollments")
def enroll_in_camp(
    camp_id: int,
    data: CampEnrollCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id required")

    camp = db.query(Camp).filter(Camp.id == camp_id, Camp.is_archived == False).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Camp not found")

    if data.is_existing_student:
        if not data.child_id:
            raise HTTPException(status_code=400, detail="child_id required for existing student")
        # Check not already enrolled
        existing = db.query(CampEnrollment).filter(
            CampEnrollment.camp_id == camp_id,
            CampEnrollment.child_id == data.child_id,
            CampEnrollment.status == CampEnrollmentStatus.ENROLLED,
            CampEnrollment.is_archived == False,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student already enrolled in this camp")
    else:
        if not data.child_name:
            raise HTTPException(status_code=400, detail="child_name required for new student")

    enrollment = CampEnrollment(
        center_id=effective_center_id,
        camp_id=camp_id,
        is_existing_student=data.is_existing_student,
        child_id=data.child_id if data.is_existing_student else None,
        child_name=data.child_name if not data.is_existing_student else None,
        child_dob=data.child_dob,
        parent_name=data.parent_name if not data.is_existing_student else None,
        parent_phone=data.parent_phone if not data.is_existing_student else None,
        parent_email=data.parent_email if not data.is_existing_student else None,
        notes=data.notes,
        status=CampEnrollmentStatus.ENROLLED,
        payment_amount=data.payment_amount,
        payment_method=data.payment_method,
        is_archived=False,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    # reload child relationship
    if enrollment.child_id:
        db.refresh(enrollment)
        enrollment.child  # trigger load
    return _enrollment_out(enrollment)


@router.patch("/{camp_id}/enrollments/{enrollment_id}/cancel")
def cancel_camp_enrollment(
    camp_id: int,
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.CENTER_ADMIN, UserRole.CENTER_MANAGER, UserRole.SUPER_ADMIN
    )),
):
    e = db.query(CampEnrollment).filter(
        CampEnrollment.id == enrollment_id,
        CampEnrollment.camp_id == camp_id,
        CampEnrollment.is_archived == False,
    ).first()
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    e.status = CampEnrollmentStatus.CANCELLED
    e.updated_by_id = current_user.id
    db.commit()
    return {"ok": True}
