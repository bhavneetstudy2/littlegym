from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Enrollment, Payment, Discount, Lead
from app.models.lead_activity import LeadActivity
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.utils.enums import EnrollmentStatus, LeadStatus


class EnrollmentService:
    """Service for enrollment management business logic"""

    @staticmethod
    def create_enrollment(
        db: Session,
        enrollment_data: EnrollmentCreate,
        center_id: int,
        created_by_id: int,
        lead_id: Optional[int] = None
    ) -> Enrollment:
        """
        Create an enrollment with payment and optional discount atomically.

        This creates:
        1. Enrollment record
        2. Payment record
        3. Discount record (if provided)
        4. Updates lead status to ENROLLED (if lead_id provided)
        """
        try:
            # Calculate net amount
            amount = enrollment_data.payment.amount
            discount_total = Decimal(0)

            if enrollment_data.discount:
                if enrollment_data.discount.type.value == "PERCENT":
                    discount_total = amount * (enrollment_data.discount.value / Decimal(100))
                else:  # FLAT
                    discount_total = enrollment_data.discount.value

            net_amount = amount - discount_total

            # Check for carry-forward from expired enrollment in the same batch
            carry_forward_visits = 0
            if enrollment_data.batch_id and enrollment_data.visits_included:
                previous_enrollment = db.query(Enrollment).filter(
                    Enrollment.child_id == enrollment_data.child_id,
                    Enrollment.batch_id == enrollment_data.batch_id,
                    Enrollment.status == EnrollmentStatus.EXPIRED,
                    Enrollment.visits_included.isnot(None),
                    Enrollment.is_archived == False,
                ).order_by(Enrollment.updated_at.desc()).first()

                if previous_enrollment and previous_enrollment.visits_used > previous_enrollment.visits_included:
                    carry_forward_visits = previous_enrollment.visits_used - previous_enrollment.visits_included

            # Create enrollment
            enrollment = Enrollment(
                center_id=center_id,
                child_id=enrollment_data.child_id,
                batch_id=enrollment_data.batch_id,
                plan_type=enrollment_data.plan_type,
                start_date=enrollment_data.start_date,
                end_date=enrollment_data.end_date,
                visits_included=enrollment_data.visits_included,
                visits_used=carry_forward_visits,
                days_selected=enrollment_data.days_selected,
                status=EnrollmentStatus.ACTIVE,
                notes=enrollment_data.notes if not carry_forward_visits else
                    f"{enrollment_data.notes or ''} [Carry-forward: {carry_forward_visits} visits from previous enrollment]".strip(),
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(enrollment)
            db.flush()  # Get enrollment.id

            # Create payment
            payment = Payment(
                center_id=center_id,
                enrollment_id=enrollment.id,
                amount=amount,
                currency="INR",
                method=enrollment_data.payment.method,
                reference=enrollment_data.payment.reference,
                paid_at=enrollment_data.payment.paid_at,
                discount_total=discount_total,
                net_amount=net_amount,
                created_by_id=created_by_id,
                updated_by_id=created_by_id,
            )
            db.add(payment)

            # Create discount if provided
            if enrollment_data.discount:
                discount = Discount(
                    center_id=center_id,
                    enrollment_id=enrollment.id,
                    type=enrollment_data.discount.type,
                    value=enrollment_data.discount.value,
                    reason=enrollment_data.discount.reason,
                    approved_by_user_id=created_by_id,  # Approver is the creator (admin)
                    applied_at=datetime.utcnow(),
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                )
                db.add(discount)

            # Update lead status to CONVERTED
            # If lead_id provided, use it; otherwise auto-find unconverted lead for this child
            lead = None
            if lead_id:
                lead = db.query(Lead).filter(Lead.id == lead_id).first()
            else:
                # Auto-find any unconverted lead for this child in the same center
                lead = db.query(Lead).filter(
                    Lead.child_id == enrollment.child_id,
                    Lead.center_id == center_id,
                    Lead.status != LeadStatus.CONVERTED,
                    Lead.is_archived == False,
                ).order_by(Lead.created_at.desc()).first()

            if lead:
                old_status = lead.status.value if lead.status else None
                lead.status = LeadStatus.CONVERTED
                lead.enrollment_id = enrollment.id
                lead.converted_at = date.today()
                lead.updated_by_id = created_by_id
                lead.updated_at = datetime.utcnow()

                # Log activity
                activity = LeadActivity(
                    lead_id=lead.id,
                    center_id=lead.center_id,
                    activity_type="LEAD_CONVERTED",
                    description=f"Lead converted to enrollment (Enrollment #{enrollment.id})",
                    old_value=old_status,
                    new_value=LeadStatus.CONVERTED.value,
                    performed_by_id=created_by_id,
                    performed_at=datetime.utcnow(),
                    created_by_id=created_by_id,
                    updated_by_id=created_by_id,
                )
                db.add(activity)

            db.commit()
            db.refresh(enrollment)

            return enrollment

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_enrollment(
        db: Session,
        enrollment_id: int,
        enrollment_data: EnrollmentUpdate,
        updated_by_id: int
    ) -> Enrollment:
        """Update enrollment information"""
        enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        if not enrollment:
            raise ValueError("Enrollment not found")

        if enrollment_data.batch_id is not None:
            enrollment.batch_id = enrollment_data.batch_id
        if enrollment_data.status is not None:
            enrollment.status = enrollment_data.status
        if enrollment_data.start_date is not None:
            enrollment.start_date = enrollment_data.start_date
        if enrollment_data.end_date is not None:
            enrollment.end_date = enrollment_data.end_date
        if enrollment_data.visits_included is not None:
            enrollment.visits_included = enrollment_data.visits_included
        if enrollment_data.days_selected is not None:
            enrollment.days_selected = enrollment_data.days_selected
        if enrollment_data.notes is not None:
            enrollment.notes = enrollment_data.notes

        enrollment.updated_by_id = updated_by_id
        enrollment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def check_enrollment_validity(enrollment: Enrollment) -> dict:
        """
        Check if enrollment is valid based on plan type.

        All plan types can have visits_included (e.g. Quarterly = 24 classes).
        Exhaustion is checked first, then date range.

        Returns:
            dict with 'is_valid' and 'reason' keys
        """
        today = date.today()

        # Check visit exhaustion for ANY plan type that has visits_included
        if enrollment.visits_included and enrollment.visits_used >= enrollment.visits_included:
            return {"is_valid": False, "reason": "All visits used"}

        # Date-based plans: also check date range
        if enrollment.plan_type.value in ["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", "CUSTOM"]:
            if enrollment.start_date and enrollment.end_date:
                if today < enrollment.start_date:
                    return {"is_valid": False, "reason": "Enrollment has not started yet"}
                if today > enrollment.end_date:
                    return {"is_valid": False, "reason": "Enrollment has expired"}
            return {"is_valid": True, "reason": None}

        # PAY_PER_VISIT (visit exhaustion already checked above)
        if enrollment.plan_type.value == "PAY_PER_VISIT":
            return {"is_valid": True, "reason": None}

        return {"is_valid": True, "reason": None}

    @staticmethod
    def get_enrollments(
        db: Session,
        center_id: int,
        status: Optional[EnrollmentStatus] = None,
        child_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Enrollment]:
        """Get enrollments with filters"""
        query = db.query(Enrollment).filter(
            Enrollment.center_id == center_id,
            Enrollment.is_archived == False
        )

        if status:
            query = query.filter(Enrollment.status == status)

        if child_id:
            query = query.filter(Enrollment.child_id == child_id)

        return query.order_by(Enrollment.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_enrollment_by_id(db: Session, enrollment_id: int) -> Optional[Enrollment]:
        """Get a single enrollment by ID"""
        return db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.is_archived == False
        ).first()

    @staticmethod
    def get_expiring_enrollments(
        db: Session,
        center_id: int,
        days: int = 30
    ) -> List[Enrollment]:
        """Get enrollments expiring within specified days"""
        from datetime import timedelta

        end_date = date.today() + timedelta(days=days)

        return db.query(Enrollment).filter(
            Enrollment.center_id == center_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Enrollment.end_date <= end_date,
            Enrollment.end_date >= date.today(),
            Enrollment.is_archived == False
        ).order_by(Enrollment.end_date).all()
