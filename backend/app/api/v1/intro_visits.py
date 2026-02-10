from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, IntroVisit, Lead
from app.schemas.lead import IntroVisitCreate, IntroVisitMarkAttended, IntroVisitResponse
from app.utils.enums import LeadStatus, UserRole

router = APIRouter(prefix="/intro-visits", tags=["intro-visits"])


@router.post("", response_model=IntroVisitResponse)
def create_intro_visit(
    visit_data: IntroVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new intro visit"""

    # Get the lead
    lead = db.query(Lead).filter(
        Lead.id == visit_data.lead_id,
        Lead.is_archived == False
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check user has access to this lead's center
    if current_user.center_id and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this lead")

    # Create intro visit
    intro_visit = IntroVisit(
        center_id=lead.center_id,
        lead_id=visit_data.lead_id,
        scheduled_at=visit_data.scheduled_at,
        batch_id=visit_data.batch_id,
        trainer_user_id=visit_data.trainer_user_id,
        outcome_notes=visit_data.outcome_notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(intro_visit)

    # Update lead status to INTRO_SCHEDULED
    if lead.status in (LeadStatus.DISCOVERY, LeadStatus.NO_SHOW, LeadStatus.FOLLOW_UP):
        lead.status = LeadStatus.INTRO_SCHEDULED
        lead.updated_by_id = current_user.id

    db.commit()
    db.refresh(intro_visit)

    return intro_visit


@router.patch("/{visit_id}/mark-attended", response_model=IntroVisitResponse)
def mark_intro_visit_attended(
    visit_id: int,
    visit_data: IntroVisitMarkAttended,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an intro visit as attended"""

    intro_visit = db.query(IntroVisit).filter(
        IntroVisit.id == visit_id,
        IntroVisit.is_archived == False
    ).first()

    if not intro_visit:
        raise HTTPException(status_code=404, detail="Intro visit not found")

    # Check user has access to this visit's center
    if current_user.center_id and intro_visit.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this intro visit")

    # Mark as attended
    intro_visit.attended_at = visit_data.attended_at
    if visit_data.outcome_notes:
        intro_visit.outcome_notes = visit_data.outcome_notes

    # Update lead status to INTRO_ATTENDED
    lead = db.query(Lead).filter(Lead.id == intro_visit.lead_id).first()
    if lead and lead.status in (LeadStatus.INTRO_SCHEDULED, LeadStatus.DISCOVERY):
        lead.status = LeadStatus.INTRO_ATTENDED
        lead.updated_by_id = current_user.id

    intro_visit.updated_by_id = current_user.id

    db.commit()
    db.refresh(intro_visit)

    return intro_visit


@router.get("", response_model=List[IntroVisitResponse])
def get_intro_visits(
    lead_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get intro visits with optional filters"""

    query = db.query(IntroVisit).filter(IntroVisit.is_archived == False)

    # Filter by center
    if current_user.role == UserRole.SUPER_ADMIN:
        if center_id:
            query = query.filter(IntroVisit.center_id == center_id)
    else:
        query = query.filter(IntroVisit.center_id == current_user.center_id)

    if lead_id:
        query = query.filter(IntroVisit.lead_id == lead_id)

    if date:
        # Filter by date (scheduled_at date)
        from datetime import datetime
        try:
            date_obj = datetime.fromisoformat(date)
            query = query.filter(
                db.func.date(IntroVisit.scheduled_at) == date_obj.date()
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    return query.order_by(IntroVisit.scheduled_at.desc()).offset(skip).limit(limit).all()


@router.get("/{visit_id}", response_model=IntroVisitResponse)
def get_intro_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single intro visit by ID"""

    intro_visit = db.query(IntroVisit).filter(
        IntroVisit.id == visit_id,
        IntroVisit.is_archived == False
    ).first()

    if not intro_visit:
        raise HTTPException(status_code=404, detail="Intro visit not found")

    # Check user has access to this visit's center
    if current_user.center_id and intro_visit.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this intro visit")

    return intro_visit
