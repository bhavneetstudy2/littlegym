from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.report_card import (
    ReportCardCreate,
    ReportCardResponse,
)
from app.services.report_card_service import ReportCardService
from app.utils.enums import UserRole

router = APIRouter(prefix="/report-cards", tags=["report-cards"])


@router.post("", response_model=ReportCardResponse)
def generate_report_card(
    report_data: ReportCardCreate,
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN))
):
    """Generate a new report card for a child"""
    if current_user.role == UserRole.SUPER_ADMIN:
        if not center_id:
            raise HTTPException(status_code=400, detail="center_id required for super admin")
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    try:
        report_card = ReportCardService.generate_report_card(
            db=db,
            report_data=report_data,
            center_id=effective_center_id,
            generated_by_id=current_user.id
        )
        return report_card
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ReportCardResponse])
def get_report_cards(
    child_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report cards with optional filters"""
    if current_user.role == UserRole.SUPER_ADMIN:
        effective_center_id = center_id
    else:
        effective_center_id = current_user.center_id

    report_cards = ReportCardService.get_report_cards(
        db=db,
        center_id=effective_center_id,
        child_id=child_id,
        skip=skip,
        limit=limit
    )
    return report_cards


@router.get("/{report_card_id}", response_model=ReportCardResponse)
def get_report_card(
    report_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single report card by ID"""
    report_card = ReportCardService.get_report_card_by_id(db=db, report_card_id=report_card_id)
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")

    # Check tenant access
    if report_card.center_id != current_user.center_id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return report_card


@router.post("/{report_card_id}/regenerate", response_model=ReportCardResponse)
def regenerate_report_card(
    report_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER, UserRole.CENTER_ADMIN))
):
    """Regenerate a report card with current skill data"""
    report_card = ReportCardService.get_report_card_by_id(db=db, report_card_id=report_card_id)
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")

    # Check tenant access
    if current_user.role != UserRole.SUPER_ADMIN and report_card.center_id != current_user.center_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        new_report_card = ReportCardService.regenerate_report_card(
            db=db,
            report_card_id=report_card_id,
            updated_by_id=current_user.id
        )
        return new_report_card
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
