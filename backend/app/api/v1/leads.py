from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadMarkDead,
    LeadResponse,
    IntroVisitCreate,
    IntroVisitMarkAttended,
    IntroVisitResponse,
    ChildUpdate,
    ChildResponse,
    ParentUpdate,
    ParentResponse,
)
from app.schemas.lead_enhanced import (
    EnquiryFormCreate,
    DiscoveryFormUpdate,
    LeadStatusUpdate,
    LeadSummary,
    LeadDetail,
    IntroVisitUpdate,
    IntroVisitResponse as EnhancedIVResponse,
    FollowUpCreate,
    FollowUpUpdate,
    FollowUpResponse,
    LeadClose,
    LeadConvert,
    PaginatedLeadsResponse,
    LeadActivityResponse,
)
from app.core.dependencies import require_super_admin
from app.services.lead_service import LeadService
from app.models import Lead, IntroVisit, FollowUp, Child, FamilyLink, Parent
from app.utils.enums import UserRole, LeadStatus

router = APIRouter(prefix="/leads", tags=["leads"])


# ===== SPECIFIC ROUTES (MUST COME BEFORE PARAMETERIZED ROUTES) =====

# Paginated list endpoint - MUST be before /{lead_id}
@router.get("/list/paginated", response_model=PaginatedLeadsResponse)
def get_leads_paginated(
    status: Optional[LeadStatus] = Query(None),
    search: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated leads with filters.
    Returns leads for the specified page along with pagination metadata.
    Optimized for performance with proper indexing.
    """
    # Super admin can filter by center_id, regular users only see their center
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    # Calculate skip based on page
    skip = (page - 1) * page_size

    # Get paginated results
    leads, total_count = LeadService.get_leads_paginated(
        db=db,
        center_id=effective_center_id,
        status=status,
        search_query=search,
        assigned_to=assigned_to,
        skip=skip,
        limit=page_size
    )

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

    # Convert to LeadSummary format
    lead_summaries = []
    for lead in leads:
        lead_summaries.append(LeadSummary(
            id=lead.id,
            center_id=lead.center_id,
            child_id=lead.child_id,
            status=lead.status,
            source=lead.source,
            child_name=f"{lead.child.first_name} {lead.child.last_name or ''}".strip(),
            child_age=lead.child.dob.year if lead.child.dob else None,
            school=lead.child.school,
            enquiry_id=lead.child.enquiry_id,
            created_at=lead.created_at,
            updated_at=lead.updated_at
        ))

    return PaginatedLeadsResponse(
        leads=lead_summaries,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# Status counts endpoint - MUST be before /{lead_id}
@router.get("/stats/status-counts")
def get_status_counts(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of leads by status.
    Returns a dictionary with status as key and count as value.
    """
    # Super admin can filter by center_id, regular users only see their center
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    counts = LeadService.get_status_counts(db=db, center_id=effective_center_id)
    return counts


# Intro visits list endpoint - MUST be before /{lead_id}
@router.get("/intro-visits", response_model=List[IntroVisitResponse])
def get_intro_visits(
    date: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get intro visits with optional filters"""
    query = db.query(IntroVisit).filter(IntroVisit.center_id == current_user.center_id)

    if date:
        from datetime import datetime
        target_date = datetime.fromisoformat(date).date()
        query = query.filter(db.func.date(IntroVisit.scheduled_at) == target_date)

    if lead_id:
        query = query.filter(IntroVisit.lead_id == lead_id)

    return query.order_by(IntroVisit.scheduled_at).all()


# Create intro visit - MUST be before /{lead_id}
@router.post("/intro-visits", response_model=IntroVisitResponse)
def create_intro_visit(
    intro_visit_data: IntroVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Schedule an introductory visit"""
    # Verify lead exists and belongs to same center
    lead = LeadService.get_lead_by_id(db=db, lead_id=intro_visit_data.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Super admin can access all centers, others only their own
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    intro_visit = IntroVisit(
        center_id=lead.center_id,
        lead_id=intro_visit_data.lead_id,
        scheduled_at=intro_visit_data.scheduled_at,
        batch_id=intro_visit_data.batch_id,
        trainer_user_id=intro_visit_data.trainer_user_id,
        outcome_notes=intro_visit_data.outcome_notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(intro_visit)

    # Update lead status to INTRO_SCHEDULED
    lead.status = LeadStatus.INTRO_SCHEDULED
    lead.updated_by_id = current_user.id

    db.commit()
    db.refresh(intro_visit)

    return intro_visit


# Create enquiry - MUST be before /{lead_id}
@router.post("/enquiry", response_model=LeadResponse)
def create_enquiry(
    enquiry_data: EnquiryFormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Create a new enquiry from the discovery form.
    This is the entry point for new leads.
    """
    # For super admin, require center_id; for others use their center
    center_id = enquiry_data.center_id if current_user.role == UserRole.SUPER_ADMIN else current_user.center_id
    if not center_id:
        raise HTTPException(status_code=400, detail="Center ID is required")

    try:
        lead = LeadService.create_enquiry(
            db=db,
            enquiry_data=enquiry_data,
            center_id=center_id,
            created_by_id=current_user.id
        )
        return lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== BASE CRUD ENDPOINTS =====

@router.post("", response_model=LeadResponse)
def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Create a new lead with child and parent information"""
    # For super admin, require center_id in lead_data; for others use their center
    center_id = lead_data.center_id if current_user.role == UserRole.SUPER_ADMIN else current_user.center_id
    if not center_id:
        raise HTTPException(status_code=400, detail="Center ID is required")
    try:
        lead = LeadService.create_lead(
            db=db,
            lead_data=lead_data,
            center_id=center_id,
            created_by_id=current_user.id
        )
        return lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[LeadResponse])
def get_leads(
    status: Optional[LeadStatus] = Query(None),
    search: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leads with optional filters (old endpoint, use /list/paginated instead)"""
    # Super admin can filter by center_id, regular users only see their center
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id  # Use provided center_id or None for all
    else:
        effective_center_id = current_user.center_id

    leads = LeadService.get_leads(
        db=db,
        center_id=effective_center_id,
        status=status,
        search_query=search,
        assigned_to=assigned_to,
        skip=skip,
        limit=limit
    )
    return leads


# ===== PARAMETERIZED ROUTES (MUST COME AFTER SPECIFIC ROUTES) =====

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single lead by ID"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if lead.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return lead


@router.get("/{lead_id}/details")
def get_lead_details(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete lead details including parents, intro visits, and follow-ups"""
    # Use optimized method that eager loads all relationships in ONE query
    lead = LeadService.get_lead_with_details(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if lead.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get parents via family links (single query with eager loading)
    family_links = db.query(FamilyLink).options(
        joinedload(FamilyLink.parent)
    ).filter(
        FamilyLink.child_id == lead.child_id,
        FamilyLink.is_archived == False
    ).all()

    parents = []
    for link in family_links:
        parents.append({
            "id": link.parent.id,
            "name": link.parent.name,
            "phone": link.parent.phone,
            "email": link.parent.email,
            "relationship": link.relationship_type,
            "is_primary": link.is_primary_contact
        })

    # Intro visits already loaded via get_lead_with_details()
    visits = []
    for visit in lead.intro_visits:
        visits.append({
            "id": visit.id,
            "scheduled_at": visit.scheduled_at.isoformat() if visit.scheduled_at else None,
            "attended_at": visit.attended_at.isoformat() if visit.attended_at else None,
            "batch_id": visit.batch_id,
            "outcome": visit.outcome.value if visit.outcome else None,
            "outcome_notes": visit.outcome_notes
        })

    # Follow-ups already loaded via get_lead_with_details()
    follow_ups_list = []
    for follow_up in lead.follow_ups:
        follow_ups_list.append({
            "id": follow_up.id,
            "scheduled_date": follow_up.scheduled_date.isoformat() if follow_up.scheduled_date else None,
            "completed_at": follow_up.completed_at.isoformat() if follow_up.completed_at else None,
            "status": follow_up.status.value if follow_up.status else None,
            "outcome": follow_up.outcome.value if follow_up.outcome else None,
            "notes": follow_up.notes
        })

    return {
        "id": lead.id,
        "center_id": lead.center_id,
        "child_id": lead.child_id,
        "status": lead.status.value,
        "source": lead.source.value if lead.source else None,
        "school": lead.school,
        "preferred_schedule": lead.preferred_schedule,
        "parent_expectations": lead.parent_expectations,
        "discovery_notes": lead.discovery_notes,
        "discovery_completed_at": lead.discovery_completed_at.isoformat() if lead.discovery_completed_at else None,
        "closed_reason": lead.closed_reason,
        "closed_at": lead.closed_at.isoformat() if lead.closed_at else None,
        "enrollment_id": lead.enrollment_id,
        "converted_at": lead.converted_at.isoformat() if lead.converted_at else None,
        "assigned_to_user_id": lead.assigned_to_user_id,
        "created_at": lead.created_at.isoformat(),
        "updated_at": lead.updated_at.isoformat(),
        "child": {
            "id": lead.child.id,
            "enquiry_id": lead.child.enquiry_id,
            "first_name": lead.child.first_name,
            "last_name": lead.child.last_name,
            "dob": lead.child.dob.isoformat() if lead.child.dob else None,
            "school": lead.child.school,
            "interests": lead.child.interests,
            "notes": lead.child.notes
        },
        "parents": parents,
        "intro_visits": visits,
        "follow_ups": follow_ups_list
    }


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Delete a lead permanently. Super Admin only."""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        LeadService.delete_lead(db=db, lead_id=lead_id)
        return {"message": "Lead deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lead_id}/activities")
def get_lead_activities(
    lead_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity log for a lead with user names and timestamps"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return LeadService.get_lead_activities(db=db, lead_id=lead_id, skip=skip, limit=limit)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Update lead information"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access - Super admin can access all
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_lead = LeadService.update_lead(
            db=db,
            lead_id=lead_id,
            lead_data=lead_data,
            updated_by_id=current_user.id
        )
        return updated_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/mark-dead", response_model=LeadResponse)
def mark_lead_dead(
    lead_id: int,
    dead_data: LeadMarkDead,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Mark a lead as dead with reason"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access - Super admin can access all
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        dead_lead = LeadService.mark_dead(
            db=db,
            lead_id=lead_id,
            reason=dead_data.reason,
            updated_by_id=current_user.id
        )
        return dead_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Mark intro visit as attended (specific parameterized route)
@router.patch("/intro-visits/{visit_id}/mark-attended", response_model=IntroVisitResponse)
def mark_intro_visit_attended(
    visit_id: int,
    attendance_data: IntroVisitMarkAttended,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN))
):
    """Mark an intro visit as attended"""
    intro_visit = db.query(IntroVisit).filter(IntroVisit.id == visit_id).first()
    if not intro_visit:
        raise HTTPException(status_code=404, detail="Intro visit not found")

    if intro_visit.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    intro_visit.attended_at = attendance_data.attended_at
    if attendance_data.outcome_notes:
        intro_visit.outcome_notes = attendance_data.outcome_notes
    intro_visit.updated_by_id = current_user.id

    # Update lead status to INTRO_ATTENDED
    lead = db.query(Lead).filter(Lead.id == intro_visit.lead_id).first()
    if lead:
        lead.status = LeadStatus.INTRO_ATTENDED
        lead.updated_by_id = current_user.id

    db.commit()
    db.refresh(intro_visit)

    return intro_visit


# ===== ENHANCED LIFECYCLE ENDPOINTS (Specific parameterized routes) =====

@router.patch("/{lead_id}/discovery", response_model=LeadResponse)
def update_discovery_form(
    lead_id: int,
    discovery_data: DiscoveryFormUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Update discovery form details after initial enquiry"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_lead = LeadService.update_discovery_form(
            db=db,
            lead_id=lead_id,
            discovery_data=discovery_data,
            updated_by_id=current_user.id
        )
        return updated_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{lead_id}/status", response_model=LeadResponse)
def update_lead_status(
    lead_id: int,
    status_data: LeadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Manually update lead status"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        from app.schemas.lead import LeadUpdate
        updated_lead = LeadService.update_lead(
            db=db,
            lead_id=lead_id,
            lead_data=LeadUpdate(
                status=status_data.status,
                discovery_notes=(lead.discovery_notes or "") + f"\n{status_data.notes}" if status_data.notes else None
            ),
            updated_by_id=current_user.id
        )
        return updated_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Enhanced Intro Visit Endpoints
@router.post("/{lead_id}/intro-visit", response_model=EnhancedIVResponse)
def schedule_intro_visit_for_lead(
    lead_id: int,
    iv_data: IntroVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Schedule an intro visit for a specific lead"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Override lead_id from path parameter
        iv_data.lead_id = lead_id
        intro_visit = LeadService.schedule_intro_visit(
            db=db,
            iv_data=iv_data,
            center_id=lead.center_id,
            created_by_id=current_user.id
        )
        return intro_visit
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/intro-visits/{iv_id}", response_model=EnhancedIVResponse)
def update_intro_visit_with_outcome(
    iv_id: int,
    iv_data: IntroVisitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Update intro visit with attendance and outcome.
    Auto-updates lead status based on outcome.
    """
    intro_visit = db.query(IntroVisit).filter(IntroVisit.id == iv_id).first()
    if not intro_visit:
        raise HTTPException(status_code=404, detail="Intro visit not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and intro_visit.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_iv = LeadService.update_intro_visit(
            db=db,
            iv_id=iv_id,
            iv_data=iv_data,
            updated_by_id=current_user.id
        )
        return updated_iv
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/intro-visits/{iv_id}", response_model=EnhancedIVResponse)
def get_intro_visit_details(
    iv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get intro visit details"""
    intro_visit = db.query(IntroVisit).filter(IntroVisit.id == iv_id).first()
    if not intro_visit:
        raise HTTPException(status_code=404, detail="Intro visit not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and intro_visit.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return intro_visit


# Follow-up Endpoints
@router.post("/{lead_id}/follow-up", response_model=FollowUpResponse)
def create_follow_up_for_lead(
    lead_id: int,
    follow_up_data: FollowUpCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Create a follow-up task for a lead"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Override lead_id from path parameter
        follow_up_data.lead_id = lead_id
        follow_up = LeadService.create_follow_up(
            db=db,
            follow_up_data=follow_up_data,
            center_id=lead.center_id,
            created_by_id=current_user.id
        )
        return follow_up
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lead_id}/follow-ups", response_model=List[FollowUpResponse])
def get_follow_ups_for_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all follow-ups for a specific lead"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    follow_ups = db.query(FollowUp).filter(
        FollowUp.lead_id == lead_id,
        FollowUp.is_archived == False
    ).order_by(FollowUp.scheduled_date.desc()).all()

    return follow_ups


@router.patch("/follow-ups/{follow_up_id}", response_model=FollowUpResponse)
def update_follow_up_with_outcome(
    follow_up_id: int,
    follow_up_data: FollowUpUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Update follow-up with outcome"""
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and follow_up.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_follow_up = LeadService.update_follow_up(
            db=db,
            follow_up_id=follow_up_id,
            follow_up_data=follow_up_data,
            updated_by_id=current_user.id
        )
        return updated_follow_up
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/follow-ups/pending", response_model=List[FollowUpResponse])
def get_pending_follow_ups(
    assigned_to: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pending follow-ups"""
    # Super admin can filter by center_id, regular users only see their center
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    follow_ups = LeadService.get_pending_follow_ups(
        db=db,
        center_id=effective_center_id,
        assigned_to=assigned_to,
        skip=skip,
        limit=limit
    )
    return follow_ups


# Conversion & Closure Endpoints
@router.post("/{lead_id}/convert", response_model=LeadResponse)
def convert_lead_to_enrollment(
    lead_id: int,
    convert_data: LeadConvert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """
    Mark lead as converted and link to enrollment.
    Call this AFTER creating the enrollment.
    """
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        converted_lead = LeadService.convert_lead(
            db=db,
            lead_id=lead_id,
            convert_data=convert_data,
            updated_by_id=current_user.id
        )
        return converted_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/close", response_model=LeadResponse)
def close_lead_as_lost(
    lead_id: int,
    close_data: LeadClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Mark lead as closed/lost with reason"""
    lead = LeadService.get_lead_by_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and lead.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        closed_lead = LeadService.close_lead(
            db=db,
            lead_id=lead_id,
            close_data=close_data,
            updated_by_id=current_user.id
        )
        return closed_lead
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== CHILD MANAGEMENT =====

@router.patch("/child/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: int,
    child_data: ChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Update child information including enquiry ID, name, age, DOB, school"""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and child.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Update fields if provided
        update_data = child_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(child, field, value)

        child.updated_by_id = current_user.id

        db.commit()
        db.refresh(child)

        return child
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/parent/{parent_id}", response_model=ParentResponse)
def update_parent(
    parent_id: int,
    parent_data: ParentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COUNSELOR, UserRole.CENTER_ADMIN, UserRole.SUPER_ADMIN))
):
    """Update parent information including name, phone, email, notes"""
    parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and parent.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Update fields if provided
        update_data = parent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(parent, field, value)

        parent.updated_by_id = current_user.id

        db.commit()
        db.refresh(parent)

        return parent
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
