from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from app.models import Child, Parent, FamilyLink, Lead, IntroVisit, FollowUp
from app.models.lead_activity import LeadActivity
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadUpdate, LeadMarkDead
from app.schemas.lead_enhanced import (
    EnquiryFormCreate, DiscoveryFormUpdate, LeadStatusUpdate,
    IntroVisitCreate, IntroVisitUpdate,
    FollowUpCreate, FollowUpUpdate,
    LeadClose, LeadConvert
)
from app.utils.enums import (
    LeadStatus, LeadSource, IVOutcome,
    FollowUpStatus, FollowUpOutcome
)


class LeadService:
    """Service for lead management business logic"""

    @staticmethod
    def _log_activity(
        db: Session,
        lead_id: int,
        center_id: int,
        activity_type: str,
        description: str,
        performed_by_id: int,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ):
        """Log an activity/interaction on a lead"""
        activity = LeadActivity(
            lead_id=lead_id,
            center_id=center_id,
            activity_type=activity_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
            performed_by_id=performed_by_id,
            performed_at=datetime.utcnow(),
            created_by_id=performed_by_id,
            updated_by_id=performed_by_id,
        )
        db.add(activity)

    @staticmethod
    def _generate_next_enquiry_id(db: Session) -> str:
        """Generate the next sequential TLGC enquiry ID."""
        from sqlalchemy import cast, Integer
        max_enquiry = db.query(func.max(Child.enquiry_id)).filter(
            Child.enquiry_id.op('~')(r'^TLGC\d+$')
        ).scalar()
        if max_enquiry:
            next_num = int(max_enquiry.replace('TLGC', '')) + 1
        else:
            next_num = 1
        return f"TLGC{next_num:04d}"

    @staticmethod
    def create_lead(
        db: Session,
        lead_data: LeadCreate,
        center_id: int,
        created_by_id: int
    ) -> Lead:
        """Create a lead with child and parent(s) atomically."""
        try:
            enquiry_id = LeadService._generate_next_enquiry_id(db)

            child = Child(
                center_id=center_id,
                enquiry_id=enquiry_id,
                first_name=lead_data.child_first_name,
                last_name=lead_data.child_last_name,
                dob=lead_data.child_dob,
                school=lead_data.child_school,
                interests=lead_data.child_interests,
                notes=lead_data.child_notes,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(child)
            db.flush()

            for idx, parent_data in enumerate(lead_data.parents):
                existing_parent = db.query(Parent).filter(
                    Parent.center_id == center_id,
                    Parent.phone == parent_data.phone,
                    Parent.is_archived == False
                ).first()

                if existing_parent:
                    parent = existing_parent
                else:
                    parent = Parent(
                        center_id=center_id,
                        name=parent_data.name,
                        phone=parent_data.phone,
                        email=parent_data.email,
                        notes=parent_data.notes,
                        created_by_id=created_by_id,
                        updated_by_id=created_by_id,
                    )
                    db.add(parent)
                    db.flush()

                family_link = FamilyLink(
                    center_id=center_id,
                    child_id=child.id,
                    parent_id=parent.id,
                    relationship_type="parent",
                    is_primary_contact=(idx == 0),
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                )
                db.add(family_link)

            lead = Lead(
                center_id=center_id,
                child_id=child.id,
                status=LeadStatus.ENQUIRY_RECEIVED,
                source=lead_data.source,
                discovery_notes=lead_data.discovery_notes,
                assigned_to_user_id=lead_data.assigned_to_user_id,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(lead)
            db.flush()

            LeadService._log_activity(
                db, lead.id, center_id,
                "LEAD_CREATED",
                f"New lead created for {child.first_name} {child.last_name or ''}".strip(),
                created_by_id,
                new_value=LeadStatus.ENQUIRY_RECEIVED.value,
            )

            db.commit()
            db.refresh(lead)
            return lead

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_lead(
        db: Session,
        lead_id: int,
        lead_data: LeadUpdate,
        updated_by_id: int
    ) -> Lead:
        """Update lead information"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        old_status = lead.status.value if lead.status else None

        if lead_data.status is not None:
            lead.status = lead_data.status
        if lead_data.discovery_notes is not None:
            lead.discovery_notes = lead_data.discovery_notes
        if lead_data.assigned_to_user_id is not None:
            lead.assigned_to_user_id = lead_data.assigned_to_user_id

        lead.updated_by_id = updated_by_id
        lead.updated_at = datetime.utcnow()

        if lead_data.status is not None and old_status != lead_data.status.value:
            LeadService._log_activity(
                db, lead_id, lead.center_id,
                "STATUS_CHANGED",
                f"Status changed from {old_status} to {lead_data.status.value}",
                updated_by_id,
                old_value=old_status,
                new_value=lead_data.status.value,
            )

        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def mark_dead(
        db: Session,
        lead_id: int,
        reason: str,
        updated_by_id: int
    ) -> Lead:
        """Mark a lead as dead with reason"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        old_status = lead.status.value if lead.status else None
        lead.status = LeadStatus.CLOSED_LOST
        lead.closed_reason = reason
        lead.closed_at = date.today()
        lead.updated_by_id = updated_by_id
        lead.updated_at = datetime.utcnow()

        LeadService._log_activity(
            db, lead_id, lead.center_id,
            "LEAD_CLOSED",
            f"Lead marked as dead/lost. Reason: {reason}",
            updated_by_id,
            old_value=old_status,
            new_value=LeadStatus.CLOSED_LOST.value,
        )

        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def get_leads(
        db: Session,
        center_id: Optional[int],
        status: Optional[LeadStatus] = None,
        search_query: Optional[str] = None,
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lead]:
        """Get leads with filters."""
        query = db.query(Lead).options(joinedload(Lead.child)).filter(
            Lead.is_archived == False
        )

        if center_id is not None:
            query = query.filter(Lead.center_id == center_id)

        if status:
            query = query.filter(Lead.status == status)

        if assigned_to:
            query = query.filter(Lead.assigned_to_user_id == assigned_to)

        if search_query:
            query = query.join(Child).join(FamilyLink).join(Parent).filter(
                or_(
                    Child.first_name.ilike(f"%{search_query}%"),
                    Child.last_name.ilike(f"%{search_query}%"),
                    Parent.phone.ilike(f"%{search_query}%"),
                    Parent.name.ilike(f"%{search_query}%")
                )
            )

        return query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_leads_paginated(
        db: Session,
        center_id: Optional[int],
        status: Optional[LeadStatus] = None,
        search_query: Optional[str] = None,
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        exclude_statuses: Optional[List[str]] = None
    ) -> tuple[List[Lead], int]:
        """Get leads with filters and return both results and total count."""
        query = db.query(Lead).options(joinedload(Lead.child)).filter(
            Lead.is_archived == False
        )

        if center_id is not None:
            query = query.filter(Lead.center_id == center_id)

        if status:
            query = query.filter(Lead.status == status)

        if exclude_statuses:
            query = query.filter(Lead.status.notin_(exclude_statuses))

        if assigned_to:
            query = query.filter(Lead.assigned_to_user_id == assigned_to)

        if search_query:
            query = query.join(Child).join(FamilyLink).join(Parent).filter(
                or_(
                    Child.first_name.ilike(f"%{search_query}%"),
                    Child.last_name.ilike(f"%{search_query}%"),
                    Parent.phone.ilike(f"%{search_query}%"),
                    Parent.name.ilike(f"%{search_query}%")
                )
            )

        total_count = query.count()
        leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

        return leads, total_count

    @staticmethod
    def get_lead_by_id(db: Session, lead_id: int) -> Optional[Lead]:
        """Get a single lead by ID"""
        return db.query(Lead).options(joinedload(Lead.child)).filter(
            Lead.id == lead_id,
            Lead.is_archived == False
        ).first()

    # ===== ENHANCED LIFECYCLE METHODS =====

    @staticmethod
    def create_enquiry(
        db: Session,
        enquiry_data: EnquiryFormCreate,
        center_id: int,
        created_by_id: int
    ) -> Lead:
        """Create a new enquiry from the discovery form."""
        try:
            enquiry_id = LeadService._generate_next_enquiry_id(db)

            child = Child(
                center_id=center_id,
                enquiry_id=enquiry_id,
                first_name=enquiry_data.child_first_name,
                last_name=enquiry_data.child_last_name,
                dob=enquiry_data.child_dob,
                school=enquiry_data.school,
                notes=enquiry_data.remarks,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(child)
            db.flush()

            # Create parent 1 (required)
            existing_parent = db.query(Parent).filter(
                Parent.center_id == center_id,
                Parent.phone == enquiry_data.contact_number,
                Parent.is_archived == False
            ).first()

            if existing_parent:
                parent = existing_parent
            else:
                parent = Parent(
                    center_id=center_id,
                    name=enquiry_data.parent_name,
                    phone=enquiry_data.contact_number,
                    email=enquiry_data.email,
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                )
                db.add(parent)
                db.flush()

            family_link = FamilyLink(
                center_id=center_id,
                child_id=child.id,
                parent_id=parent.id,
                relationship_type="parent",
                is_primary_contact=True,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(family_link)

            # Create parent 2 (optional)
            if enquiry_data.parent2_name and enquiry_data.parent2_contact_number:
                existing_parent2 = db.query(Parent).filter(
                    Parent.center_id == center_id,
                    Parent.phone == enquiry_data.parent2_contact_number,
                    Parent.is_archived == False
                ).first()

                if existing_parent2:
                    parent2 = existing_parent2
                else:
                    parent2 = Parent(
                        center_id=center_id,
                        name=enquiry_data.parent2_name,
                        phone=enquiry_data.parent2_contact_number,
                        email=enquiry_data.parent2_email,
                        created_by_id=created_by_id,
                        updated_by_id=created_by_id,
                    )
                    db.add(parent2)
                    db.flush()

                family_link2 = FamilyLink(
                    center_id=center_id,
                    child_id=child.id,
                    parent_id=parent2.id,
                    relationship_type="parent",
                    is_primary_contact=False,
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                )
                db.add(family_link2)

            lead = Lead(
                center_id=center_id,
                child_id=child.id,
                status=LeadStatus.ENQUIRY_RECEIVED,
                source=enquiry_data.source,
                school=enquiry_data.school,
                preferred_schedule=enquiry_data.preferred_schedule,
                parent_expectations=enquiry_data.parent_expectations,
                discovery_notes=enquiry_data.remarks,
                assigned_to_user_id=enquiry_data.assigned_to_user_id,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(lead)
            db.flush()

            LeadService._log_activity(
                db, lead.id, center_id,
                "LEAD_CREATED",
                f"New enquiry created for {child.first_name} {child.last_name or ''}".strip(),
                created_by_id,
                new_value=LeadStatus.ENQUIRY_RECEIVED.value,
            )

            db.commit()
            db.refresh(lead)
            return lead

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_discovery_form(
        db: Session,
        lead_id: int,
        discovery_data: DiscoveryFormUpdate,
        updated_by_id: int
    ) -> Lead:
        """Update discovery form details and mark as completed"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        old_status = lead.status.value if lead.status else None

        if discovery_data.school is not None:
            lead.school = discovery_data.school
        if discovery_data.preferred_schedule is not None:
            lead.preferred_schedule = discovery_data.preferred_schedule
        if discovery_data.parent_expectations is not None:
            lead.parent_expectations = discovery_data.parent_expectations
        if discovery_data.discovery_notes is not None:
            lead.discovery_notes = discovery_data.discovery_notes

        lead.discovery_completed_at = date.today()
        lead.status = LeadStatus.DISCOVERY_COMPLETED
        lead.updated_by_id = updated_by_id
        lead.updated_at = datetime.utcnow()

        LeadService._log_activity(
            db, lead_id, lead.center_id,
            "DISCOVERY_COMPLETED",
            "Discovery form completed",
            updated_by_id,
            old_value=old_status,
            new_value=LeadStatus.DISCOVERY_COMPLETED.value,
        )

        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def schedule_intro_visit(
        db: Session,
        iv_data: IntroVisitCreate,
        center_id: int,
        created_by_id: int
    ) -> IntroVisit:
        """Schedule an intro visit for a lead."""
        try:
            lead = db.query(Lead).filter(Lead.id == iv_data.lead_id).first()
            if not lead:
                raise ValueError("Lead not found")

            old_status = lead.status.value if lead.status else None

            intro_visit = IntroVisit(
                center_id=center_id,
                lead_id=iv_data.lead_id,
                scheduled_at=iv_data.scheduled_at,
                batch_id=iv_data.batch_id,
                trainer_user_id=iv_data.trainer_user_id,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(intro_visit)

            lead.status = LeadStatus.IV_SCHEDULED
            lead.updated_by_id = created_by_id
            lead.updated_at = datetime.utcnow()

            LeadService._log_activity(
                db, iv_data.lead_id, center_id,
                "IV_SCHEDULED",
                f"Intro visit scheduled for {iv_data.scheduled_at.strftime('%d %b %Y %H:%M')}",
                created_by_id,
                old_value=old_status,
                new_value=LeadStatus.IV_SCHEDULED.value,
            )

            db.commit()
            db.refresh(intro_visit)
            return intro_visit

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_intro_visit(
        db: Session,
        iv_id: int,
        iv_data: IntroVisitUpdate,
        updated_by_id: int
    ) -> IntroVisit:
        """Update intro visit and auto-update lead status based on outcome."""
        intro_visit = db.query(IntroVisit).filter(IntroVisit.id == iv_id).first()
        if not intro_visit:
            raise ValueError("Intro visit not found")

        lead = db.query(Lead).filter(Lead.id == intro_visit.lead_id).first()
        old_status = lead.status.value if lead and lead.status else None

        if iv_data.scheduled_at is not None:
            intro_visit.scheduled_at = iv_data.scheduled_at
        if iv_data.batch_id is not None:
            intro_visit.batch_id = iv_data.batch_id
        if iv_data.trainer_user_id is not None:
            intro_visit.trainer_user_id = iv_data.trainer_user_id
        if iv_data.attended_at is not None:
            intro_visit.attended_at = iv_data.attended_at
        if iv_data.outcome is not None:
            intro_visit.outcome = iv_data.outcome
        if iv_data.outcome_notes is not None:
            intro_visit.outcome_notes = iv_data.outcome_notes

        intro_visit.updated_by_id = updated_by_id
        intro_visit.updated_at = datetime.utcnow()

        if iv_data.outcome and lead:
            if iv_data.outcome == IVOutcome.INTERESTED_ENROLL_NOW:
                lead.status = LeadStatus.IV_COMPLETED
            elif iv_data.outcome in [IVOutcome.INTERESTED_ENROLL_LATER, IVOutcome.NOT_INTERESTED]:
                lead.status = LeadStatus.FOLLOW_UP_PENDING
            elif iv_data.outcome == IVOutcome.NO_SHOW:
                lead.status = LeadStatus.IV_NO_SHOW

            lead.updated_by_id = updated_by_id
            lead.updated_at = datetime.utcnow()

            outcome_label = iv_data.outcome.value.replace('_', ' ').title()
            LeadService._log_activity(
                db, intro_visit.lead_id, intro_visit.center_id,
                "IV_UPDATED",
                f"Intro visit updated. Outcome: {outcome_label}",
                updated_by_id,
                old_value=old_status,
                new_value=lead.status.value,
            )

        db.commit()
        db.refresh(intro_visit)
        return intro_visit

    @staticmethod
    def create_follow_up(
        db: Session,
        follow_up_data: FollowUpCreate,
        center_id: int,
        created_by_id: int
    ) -> FollowUp:
        """Create a follow-up for a lead"""
        try:
            lead = db.query(Lead).filter(Lead.id == follow_up_data.lead_id).first()
            if not lead:
                raise ValueError("Lead not found")

            old_status = lead.status.value if lead.status else None

            follow_up = FollowUp(
                center_id=center_id,
                lead_id=follow_up_data.lead_id,
                scheduled_date=follow_up_data.scheduled_date,
                status=FollowUpStatus.PENDING,
                notes=follow_up_data.notes,
                assigned_to_user_id=follow_up_data.assigned_to_user_id,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(follow_up)

            if lead.status not in [LeadStatus.FOLLOW_UP_PENDING, LeadStatus.CONVERTED, LeadStatus.CLOSED_LOST]:
                lead.status = LeadStatus.FOLLOW_UP_PENDING
                lead.updated_by_id = created_by_id
                lead.updated_at = datetime.utcnow()

            LeadService._log_activity(
                db, follow_up_data.lead_id, center_id,
                "FOLLOW_UP_CREATED",
                f"Follow-up scheduled for {follow_up_data.scheduled_date.strftime('%d %b %Y %H:%M')}"
                + (f". Notes: {follow_up_data.notes}" if follow_up_data.notes else ""),
                created_by_id,
                old_value=old_status,
                new_value=lead.status.value,
            )

            db.commit()
            db.refresh(follow_up)
            return follow_up

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_follow_up(
        db: Session,
        follow_up_id: int,
        follow_up_data: FollowUpUpdate,
        updated_by_id: int
    ) -> FollowUp:
        """Update follow-up with outcome."""
        follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
        if not follow_up:
            raise ValueError("Follow-up not found")

        if follow_up_data.scheduled_date is not None:
            follow_up.scheduled_date = follow_up_data.scheduled_date
        if follow_up_data.completed_at is not None:
            follow_up.completed_at = follow_up_data.completed_at
        if follow_up_data.status is not None:
            follow_up.status = follow_up_data.status
        if follow_up_data.outcome is not None:
            follow_up.outcome = follow_up_data.outcome
        if follow_up_data.notes is not None:
            follow_up.notes = follow_up_data.notes
        if follow_up_data.assigned_to_user_id is not None:
            follow_up.assigned_to_user_id = follow_up_data.assigned_to_user_id

        follow_up.updated_by_id = updated_by_id
        follow_up.updated_at = datetime.utcnow()

        if follow_up_data.outcome:
            outcome_label = follow_up_data.outcome.value.replace('_', ' ').title()
            LeadService._log_activity(
                db, follow_up.lead_id, follow_up.center_id,
                "FOLLOW_UP_UPDATED",
                f"Follow-up outcome: {outcome_label}"
                + (f". Notes: {follow_up_data.notes}" if follow_up_data.notes else ""),
                updated_by_id,
                new_value=follow_up_data.outcome.value,
            )

        db.commit()
        db.refresh(follow_up)
        return follow_up

    @staticmethod
    def convert_lead(
        db: Session,
        lead_id: int,
        convert_data: LeadConvert,
        updated_by_id: int
    ) -> Lead:
        """Mark lead as converted and link to enrollment."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        if lead.status == LeadStatus.CONVERTED:
            raise ValueError("Lead is already converted")

        old_status = lead.status.value
        lead.status = LeadStatus.CONVERTED
        lead.enrollment_id = convert_data.enrollment_id
        lead.converted_at = date.today()
        lead.updated_by_id = updated_by_id
        lead.updated_at = datetime.utcnow()

        LeadService._log_activity(
            db, lead_id, lead.center_id,
            "LEAD_CONVERTED",
            f"Lead converted to enrollment (Enrollment #{convert_data.enrollment_id})",
            updated_by_id,
            old_value=old_status,
            new_value=LeadStatus.CONVERTED.value,
        )

        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def close_lead(
        db: Session,
        lead_id: int,
        close_data: LeadClose,
        updated_by_id: int
    ) -> Lead:
        """Mark lead as closed/lost with reason."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        if lead.status in [LeadStatus.CONVERTED, LeadStatus.CLOSED_LOST]:
            raise ValueError(f"Lead is already {lead.status.value}")

        old_status = lead.status.value
        lead.status = LeadStatus.CLOSED_LOST
        lead.closed_reason = close_data.reason
        lead.closed_at = date.today()
        lead.updated_by_id = updated_by_id
        lead.updated_at = datetime.utcnow()

        LeadService._log_activity(
            db, lead_id, lead.center_id,
            "LEAD_CLOSED",
            f"Lead closed. Reason: {close_data.reason}",
            updated_by_id,
            old_value=old_status,
            new_value=LeadStatus.CLOSED_LOST.value,
        )

        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def delete_lead(
        db: Session,
        lead_id: int,
    ) -> bool:
        """Permanently delete a lead and its related records. Super admin only."""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        db.delete(lead)
        db.commit()
        return True

    @staticmethod
    def get_lead_activities(
        db: Session,
        lead_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[dict]:
        """Get activity log for a lead with performer names"""
        activities = db.query(LeadActivity, User.name).join(
            User, LeadActivity.performed_by_id == User.id
        ).filter(
            LeadActivity.lead_id == lead_id
        ).order_by(
            LeadActivity.performed_at.desc()
        ).offset(skip).limit(limit).all()

        result = []
        for activity, user_name in activities:
            result.append({
                "id": activity.id,
                "lead_id": activity.lead_id,
                "activity_type": activity.activity_type,
                "description": activity.description,
                "old_value": activity.old_value,
                "new_value": activity.new_value,
                "performed_by_id": activity.performed_by_id,
                "performed_by_name": user_name,
                "performed_at": activity.performed_at.isoformat(),
                "created_at": activity.created_at.isoformat(),
            })
        return result

    @staticmethod
    def get_pending_follow_ups(
        db: Session,
        center_id: Optional[int],
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FollowUp]:
        """Get all pending follow-ups, optionally filtered by assignee"""
        query = db.query(FollowUp).filter(
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.is_archived == False
        )

        if center_id is not None:
            query = query.filter(FollowUp.center_id == center_id)

        if assigned_to:
            query = query.filter(FollowUp.assigned_to_user_id == assigned_to)

        return query.order_by(FollowUp.scheduled_date).offset(skip).limit(limit).all()

    @staticmethod
    def get_status_counts(db: Session, center_id: Optional[int], exclude_statuses: Optional[List[str]] = None) -> dict:
        """Get count of leads by status"""
        query = db.query(
            Lead.status,
            func.count(Lead.id).label('count')
        ).filter(
            Lead.is_archived == False
        )

        if center_id is not None:
            query = query.filter(Lead.center_id == center_id)

        if exclude_statuses:
            query = query.filter(Lead.status.notin_(exclude_statuses))

        query = query.group_by(Lead.status)
        results = query.all()

        # Convert to dict with status as key
        counts = {status.value: count for status, count in results}

        # Add zero counts for statuses with no leads (excluding excluded ones)
        for status in LeadStatus:
            if exclude_statuses and status.value in exclude_statuses:
                continue
            if status.value not in counts:
                counts[status.value] = 0

        return counts

    @staticmethod
    def get_lead_with_details(db: Session, lead_id: int) -> Optional[Lead]:
        """Get lead with all related data"""
        return db.query(Lead).options(
            joinedload(Lead.child),
            joinedload(Lead.intro_visits),
            joinedload(Lead.follow_ups),
            joinedload(Lead.enrollment)
        ).filter(
            Lead.id == lead_id,
            Lead.is_archived == False
        ).first()
