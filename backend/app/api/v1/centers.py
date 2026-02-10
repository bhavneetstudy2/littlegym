from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from datetime import date, timedelta

from sqlalchemy import text
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, Center, Lead, Enrollment, Batch, ClassSession
from app.schemas.center import CenterCreate, CenterUpdate, CenterResponse, CenterStatsResponse
from app.utils.enums import UserRole

router = APIRouter(prefix="/centers", tags=["centers"])


@router.get("", response_model=List[CenterResponse])
def get_centers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all centers (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can view all centers")

    query = db.query(Center)

    if active_only:
        query = query.filter(Center.active == True)

    centers = query.order_by(Center.name).offset(skip).limit(limit).all()
    return centers


@router.post("", response_model=CenterResponse)
def create_center(
    center_data: CenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new center (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can create centers")

    # Check if code already exists
    if center_data.code:
        existing = db.query(Center).filter(
            Center.code == center_data.code,
            Center.active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Center code already exists")

    center = Center(
        **center_data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(center)
    db.commit()
    db.refresh(center)

    return center


@router.get("/{center_id}", response_model=CenterResponse)
def get_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get center details"""
    center = db.query(Center).filter(
        Center.id == center_id,
        Center.active == True
    ).first()

    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    # Super admin can view any center, others only their own
    if current_user.role != UserRole.SUPER_ADMIN and current_user.center_id != center_id:
        raise HTTPException(status_code=403, detail="Access denied to this center")

    return center


@router.patch("/{center_id}", response_model=CenterResponse)
def update_center(
    center_id: int,
    center_data: CenterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update center (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can update centers")

    center = db.query(Center).filter(
        Center.id == center_id,
        Center.active == True
    ).first()

    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    # Update fields
    update_data = center_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(center, field, value)

    center.updated_by_id = current_user.id

    db.commit()
    db.refresh(center)

    return center


@router.get("/{center_id}/stats", response_model=CenterStatsResponse)
def get_center_stats(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get center statistics"""
    center = db.query(Center).filter(
        Center.id == center_id,
        Center.active == True
    ).first()

    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    # Permission check
    if current_user.role != UserRole.SUPER_ADMIN and current_user.center_id != center_id:
        raise HTTPException(status_code=403, detail="Access denied to this center")

    # Single query for all stats to minimize DB round trips
    today = date.today()
    cutoff = today + timedelta(days=30)

    stats_sql = text("""
        SELECT
            (SELECT COUNT(*) FROM leads WHERE center_id = :cid AND is_archived = false) as total_leads,
            (SELECT COUNT(*) FROM enrollments WHERE center_id = :cid AND status = 'ACTIVE' AND is_archived = false) as active_enrollments,
            (SELECT COUNT(*) FROM batches WHERE center_id = :cid AND active = true AND is_archived = false) as total_batches,
            (SELECT COUNT(*) FROM users WHERE center_id = :cid) as total_users,
            (SELECT COUNT(*) FROM class_sessions WHERE center_id = :cid AND session_date = :today) as todays_classes,
            (SELECT COUNT(*) FROM enrollments WHERE center_id = :cid AND status = 'ACTIVE' AND end_date IS NOT NULL AND end_date <= :cutoff AND is_archived = false) as pending_renewals,
            GREATEST(
                (SELECT MAX(created_at) FROM leads WHERE center_id = :cid),
                (SELECT MAX(created_at) FROM enrollments WHERE center_id = :cid)
            ) as last_activity
    """)

    row = db.execute(stats_sql, {"cid": center_id, "today": today, "cutoff": cutoff}).fetchone()

    return CenterStatsResponse(
        center_id=center.id,
        center_name=center.name,
        total_leads=row.total_leads or 0,
        active_enrollments=row.active_enrollments or 0,
        total_batches=row.total_batches or 0,
        total_users=row.total_users or 0,
        todays_classes=row.todays_classes or 0,
        pending_renewals=row.pending_renewals or 0,
        last_activity=row.last_activity
    )
