from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel as PydanticModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models import Camp, CampEnrollment, Child, Parent, FamilyLink, Lead
from app.models.camp_enrollment import CampEnrollmentStatus, PaymentStatus
from app.utils.enums import UserRole, LeadStatus, LeadSource
from app.services.lead_service import LeadService

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
    # Payment
    payment_status: Optional[str] = "PENDING"
    payment_amount: Optional[float] = None   # total fee
    amount_paid: Optional[float] = None      # amount collected so far
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[date] = None


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


def _enrollment_out(e: CampEnrollment, lead_created: bool = False) -> dict:
    child_name = e.child_name
    # For both existing and new students (new students now have child_id set)
    if e.child:
        child_name = f"{e.child.first_name or ''} {e.child.last_name or ''}".strip() or e.child_name
    return {
        "id": e.id,
        "camp_id": e.camp_id,
        "is_existing_student": e.is_existing_student,
        "child_id": e.child_id,
        "child_name": child_name,
        "child_dob": str(e.child_dob) if e.child_dob else None,
        "parent_name": e.parent_name,
        "parent_phone": e.parent_phone,
        "parent_email": e.parent_email,
        "notes": e.notes,
        "status": e.status,
        "payment_status": e.payment_status,
        "payment_amount": float(e.payment_amount) if e.payment_amount is not None else None,
        "amount_paid": float(e.amount_paid) if e.amount_paid is not None else None,
        "payment_method": e.payment_method,
        "payment_reference": e.payment_reference,
        "payment_date": str(e.payment_date) if e.payment_date else None,
        "lead_created": lead_created,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# ── Children search (for enroll modal) ──────────────────────────────────────

@router.get("/children-search")
def search_children(
    search: str = Query(..., min_length=2),
    center_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search all children by name (for camp enrollment). Returns any child, not just enrolled ones."""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    if not effective_center_id:
        raise HTTPException(status_code=400, detail="center_id required")

    rows = db.execute(text("""
        SELECT
            c.id AS child_id,
            c.first_name,
            c.last_name,
            c.enquiry_id,
            b.name AS batch_name
        FROM children c
        LEFT JOIN enrollments e ON e.child_id = c.id
            AND e.status = 'ACTIVE'
            AND e.is_archived = false
            AND e.center_id = :cid
        LEFT JOIN batches b ON e.batch_id = b.id
        WHERE c.center_id = :cid
          AND c.is_archived = false
          AND (
              c.first_name ILIKE :q
              OR c.last_name ILIKE :q
              OR CONCAT(c.first_name, ' ', c.last_name) ILIKE :q
              OR c.enquiry_id ILIKE :q
          )
        ORDER BY c.first_name, c.last_name
        LIMIT :lim
    """), {"cid": effective_center_id, "q": f"%{search.strip()}%", "lim": limit}).fetchall()

    seen = set()
    result = []
    for r in rows:
        if r.child_id not in seen:
            seen.add(r.child_id)
            name = " ".join(filter(None, [r.first_name, r.last_name]))
            result.append({
                "child_id": r.child_id,
                "child_name": name,
                "enrollment_id": None,
                "batch_name": r.batch_name,
                "enquiry_id": r.enquiry_id,
            })
    return result


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
        UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN
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
        UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN
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

    new_child_id: Optional[int] = None

    if data.is_existing_student:
        if not data.child_id:
            raise HTTPException(status_code=400, detail="child_id required for existing student")
        # Check not already enrolled
        already = db.query(CampEnrollment).filter(
            CampEnrollment.camp_id == camp_id,
            CampEnrollment.child_id == data.child_id,
            CampEnrollment.status == CampEnrollmentStatus.ENROLLED,
            CampEnrollment.is_archived == False,
        ).first()
        if already:
            raise HTTPException(status_code=400, detail="Student already enrolled in this camp")
    else:
        if not data.child_name:
            raise HTTPException(status_code=400, detail="child_name required for new student")

        # ── Auto-create Child + Parent + Lead for new student ──────────────
        name_parts = data.child_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else None

        enquiry_id = LeadService._generate_next_enquiry_id(db)
        child = Child(
            center_id=effective_center_id,
            enquiry_id=enquiry_id,
            first_name=first_name,
            last_name=last_name,
            dob=data.child_dob,
            is_archived=False,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(child)
        db.flush()  # get child.id

        if data.parent_name or data.parent_phone:
            parent = Parent(
                center_id=effective_center_id,
                name=data.parent_name or "Unknown",
                phone=data.parent_phone or "",
                email=data.parent_email,
                is_archived=False,
                created_by_id=current_user.id,
                updated_by_id=current_user.id,
            )
            db.add(parent)
            db.flush()

            family_link = FamilyLink(
                center_id=effective_center_id,
                child_id=child.id,
                parent_id=parent.id,
                relationship_type="parent",
                is_primary_contact=True,
                is_archived=False,
                created_by_id=current_user.id,
                updated_by_id=current_user.id,
            )
            db.add(family_link)

        lead = Lead(
            center_id=effective_center_id,
            child_id=child.id,
            status=LeadStatus.ENQUIRY_RECEIVED,
            source=LeadSource.CAMP,
            discovery_notes=f"Enrolled in {camp.name} camp ({camp.start_date} – {camp.end_date})",
            is_archived=False,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(lead)
        new_child_id = child.id

    enrollment = CampEnrollment(
        center_id=effective_center_id,
        camp_id=camp_id,
        is_existing_student=data.is_existing_student,
        child_id=data.child_id if data.is_existing_student else new_child_id,
        child_name=data.child_name if not data.is_existing_student else None,
        child_dob=data.child_dob,
        parent_name=data.parent_name if not data.is_existing_student else None,
        parent_phone=data.parent_phone if not data.is_existing_student else None,
        parent_email=data.parent_email if not data.is_existing_student else None,
        notes=data.notes,
        status=CampEnrollmentStatus.ENROLLED,
        payment_status=PaymentStatus(data.payment_status) if data.payment_status else PaymentStatus.PENDING,
        payment_amount=data.payment_amount,
        amount_paid=data.amount_paid,
        payment_method=data.payment_method,
        payment_reference=data.payment_reference,
        payment_date=data.payment_date,
        is_archived=False,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    if enrollment.child_id:
        enrollment.child  # trigger load
    return _enrollment_out(enrollment, lead_created=not data.is_existing_student)


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
