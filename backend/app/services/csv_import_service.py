"""
CSV Import Service - Business logic for importing data from CSV files.

Supports four import types:
  1. Leads (child + parent + lead status)
  2. Enrollments (child + enrollment)
  3. Attendance (child + session attendance)
  4. Skill progress (child + skill level)

Each importer handles:
  - Encoding detection (utf-8 with latin-1 fallback)
  - Per-row error handling (one bad row does not abort the batch)
  - Deduplication by phone+name (leads) or enquiry_id (enrollments)
  - Auto-generation of enquiry IDs for new children
"""

import csv
import io
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Child, Parent, FamilyLink, Lead, Batch,
    ClassSession, Enrollment, Attendance, Skill, SkillProgress,
)
from app.utils.enums import (
    LeadStatus, LeadSource, PlanType, EnrollmentStatus,
    AttendanceStatus, SkillLevel, SessionStatus,
)
from app.schemas.csv_import import ImportResult, ImportError as ImportErrorSchema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_csv(file_bytes: bytes) -> str:
    """Decode CSV bytes with utf-8 and latin-1 fallback."""
    try:
        return file_bytes.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _parse_csv(text: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Return (headers, rows) from a CSV string."""
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows


def _get_mapped_value(row: Dict[str, str], csv_column: Optional[str]) -> Optional[str]:
    """Get a stripped value from a row using the mapped CSV column name."""
    if not csv_column:
        return None
    val = row.get(csv_column, "")
    if val is None:
        return None
    val = str(val).strip()
    return val if val else None


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse a date string supporting YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY."""
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _normalise_phone(phone: Optional[str]) -> Optional[str]:
    """Strip spaces, dashes, and leading + from phone numbers for dedup."""
    if not phone:
        return None
    cleaned = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return cleaned


def _generate_next_enquiry_id(db: Session) -> str:
    """Generate the next sequential TLGC enquiry ID (mirrors LeadService)."""
    max_enquiry = db.query(func.max(Child.enquiry_id)).filter(
        Child.enquiry_id.op("~")(r"^TLGC\d+$")
    ).scalar()
    if max_enquiry:
        next_num = int(max_enquiry.replace("TLGC", "")) + 1
    else:
        next_num = 1
    return f"TLGC{next_num:04d}"


def _find_child_by_enquiry_id(
    db: Session, enquiry_id: str, center_id: int
) -> Optional[Child]:
    """Lookup child by enquiry_id scoped to a center."""
    return db.query(Child).filter(
        Child.enquiry_id == enquiry_id.strip().upper(),
        Child.center_id == center_id,
        Child.is_archived == False,
    ).first()


def _find_child_by_name(
    db: Session, child_name: str, center_id: int
) -> Optional[Child]:
    """Lookup child by full name (first + last) scoped to a center."""
    parts = child_name.strip().split(None, 1)
    first_name = parts[0] if parts else child_name.strip()
    last_name = parts[1] if len(parts) > 1 else None

    query = db.query(Child).filter(
        func.lower(Child.first_name) == first_name.lower(),
        Child.center_id == center_id,
        Child.is_archived == False,
    )
    if last_name:
        query = query.filter(func.lower(Child.last_name) == last_name.lower())

    return query.first()


def _resolve_child(
    db: Session, row: Dict[str, str], mapping: Dict[str, Optional[str]],
    center_id: int
) -> Optional[Child]:
    """Resolve a child from a row using enquiry_id or child_name mapping."""
    enquiry_id = _get_mapped_value(row, mapping.get("enquiry_id"))
    child_name = _get_mapped_value(row, mapping.get("child_name"))

    if enquiry_id:
        child = _find_child_by_enquiry_id(db, enquiry_id, center_id)
        if child:
            return child

    if child_name:
        child = _find_child_by_name(db, child_name, center_id)
        if child:
            return child

    return None


def _find_batch_by_name(
    db: Session, batch_name: str, center_id: int
) -> Optional[Batch]:
    """Lookup batch by name scoped to a center."""
    return db.query(Batch).filter(
        func.lower(Batch.name) == batch_name.strip().lower(),
        Batch.center_id == center_id,
        Batch.is_archived == False,
    ).first()


def _parse_lead_source(value: Optional[str]) -> Optional[LeadSource]:
    """Map a free-text source string to a LeadSource enum value."""
    if not value:
        return None
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return LeadSource(normalised)
    except ValueError:
        # Fuzzy matching for common variants
        mapping = {
            "WALKIN": LeadSource.WALK_IN,
            "WALK_IN": LeadSource.WALK_IN,
            "PHONE": LeadSource.PHONE_CALL,
            "PHONECALL": LeadSource.PHONE_CALL,
            "PHONE_CALL": LeadSource.PHONE_CALL,
            "WEB": LeadSource.ONLINE,
            "WEBSITE": LeadSource.ONLINE,
            "ONLINE": LeadSource.ONLINE,
            "REFERRAL": LeadSource.REFERRAL,
            "INSTAGRAM": LeadSource.INSTAGRAM,
            "INSTA": LeadSource.INSTAGRAM,
            "FACEBOOK": LeadSource.FACEBOOK,
            "FB": LeadSource.FACEBOOK,
            "GOOGLE": LeadSource.GOOGLE,
        }
        return mapping.get(normalised, LeadSource.OTHER)


def _parse_lead_status(value: Optional[str]) -> LeadStatus:
    """Map a free-text status string to a LeadStatus enum value."""
    if not value:
        return LeadStatus.ENQUIRY_RECEIVED
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return LeadStatus(normalised)
    except ValueError:
        mapping = {
            "DISCOVERY": LeadStatus.ENQUIRY_RECEIVED,
            "ENQUIRY": LeadStatus.ENQUIRY_RECEIVED,
            "ENQUIRY_RECEIVED": LeadStatus.ENQUIRY_RECEIVED,
            "INTRO_SCHEDULED": LeadStatus.IV_SCHEDULED,
            "IV_SCHEDULED": LeadStatus.IV_SCHEDULED,
            "INTRO_ATTENDED": LeadStatus.IV_COMPLETED,
            "IV_COMPLETED": LeadStatus.IV_COMPLETED,
            "NO_SHOW": LeadStatus.IV_NO_SHOW,
            "IV_NO_SHOW": LeadStatus.IV_NO_SHOW,
            "FOLLOW_UP": LeadStatus.FOLLOW_UP_PENDING,
            "FOLLOW_UP_PENDING": LeadStatus.FOLLOW_UP_PENDING,
            "ENROLLED": LeadStatus.CONVERTED,
            "CONVERTED": LeadStatus.CONVERTED,
            "DEAD_LEAD": LeadStatus.CLOSED_LOST,
            "DEAD": LeadStatus.CLOSED_LOST,
            "CLOSED": LeadStatus.CLOSED_LOST,
            "CLOSED_LOST": LeadStatus.CLOSED_LOST,
            "LOST": LeadStatus.CLOSED_LOST,
        }
        return mapping.get(normalised, LeadStatus.ENQUIRY_RECEIVED)


def _parse_plan_type(value: Optional[str]) -> Optional[PlanType]:
    """Map a free-text plan type to PlanType enum."""
    if not value:
        return None
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return PlanType(normalised)
    except ValueError:
        mapping = {
            "MONTHLY": PlanType.MONTHLY,
            "QUARTERLY": PlanType.QUARTERLY,
            "YEARLY": PlanType.YEARLY,
            "ANNUAL": PlanType.YEARLY,
            "WEEKLY": PlanType.WEEKLY,
            "PAY_PER_VISIT": PlanType.PAY_PER_VISIT,
            "PER_VISIT": PlanType.PAY_PER_VISIT,
            "CUSTOM": PlanType.CUSTOM,
        }
        return mapping.get(normalised)


def _parse_enrollment_status(value: Optional[str]) -> EnrollmentStatus:
    """Map a free-text enrollment status to EnrollmentStatus enum."""
    if not value:
        return EnrollmentStatus.ACTIVE
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return EnrollmentStatus(normalised)
    except ValueError:
        return EnrollmentStatus.ACTIVE


def _parse_attendance_status(value: Optional[str]) -> Optional[AttendanceStatus]:
    """Map a free-text attendance status to AttendanceStatus enum."""
    if not value:
        return None
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return AttendanceStatus(normalised)
    except ValueError:
        mapping = {
            "P": AttendanceStatus.PRESENT,
            "A": AttendanceStatus.ABSENT,
            "YES": AttendanceStatus.PRESENT,
            "NO": AttendanceStatus.ABSENT,
            "PRESENT": AttendanceStatus.PRESENT,
            "ABSENT": AttendanceStatus.ABSENT,
            "MAKEUP": AttendanceStatus.MAKEUP,
            "TRIAL": AttendanceStatus.TRIAL,
            "CANCELLED": AttendanceStatus.CANCELLED,
        }
        return mapping.get(normalised)


def _parse_skill_level(value: Optional[str]) -> Optional[SkillLevel]:
    """Map a free-text skill level to SkillLevel enum."""
    if not value:
        return None
    normalised = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return SkillLevel(normalised)
    except ValueError:
        mapping = {
            "NOT_STARTED": SkillLevel.NOT_STARTED,
            "NOTSTARTED": SkillLevel.NOT_STARTED,
            "IN_PROGRESS": SkillLevel.IN_PROGRESS,
            "INPROGRESS": SkillLevel.IN_PROGRESS,
            "WORKING": SkillLevel.IN_PROGRESS,
            "ACHIEVED": SkillLevel.ACHIEVED,
            "DONE": SkillLevel.ACHIEVED,
            "MASTERED": SkillLevel.MASTERED,
        }
        return mapping.get(normalised)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def preview_csv(file_bytes: bytes) -> Dict[str, Any]:
    """Parse CSV and return headers + first 5 rows for mapping preview."""
    text = _decode_csv(file_bytes)
    headers, rows = _parse_csv(text)
    return {
        "headers": headers,
        "sample_rows": rows[:5],
        "total_rows": len(rows),
    }


# ---------------------------------------------------------------------------
# Leads Import
# ---------------------------------------------------------------------------

def import_leads(
    db: Session,
    file_bytes: bytes,
    column_mapping: Dict[str, Optional[str]],
    center_id: int,
    user_id: int,
) -> ImportResult:
    """
    Import leads from CSV.

    Deduplication strategy: parent_phone + child_first_name.
    If a match is found the row is marked as updated (notes appended).
    Otherwise a new Child + Parent + FamilyLink + Lead is created.
    """
    text = _decode_csv(file_bytes)
    _headers, rows = _parse_csv(text)
    result = ImportResult()

    for idx, row in enumerate(rows, start=2):  # row 1 = header
        try:
            first_name = _get_mapped_value(row, column_mapping.get("child_first_name"))
            parent_name = _get_mapped_value(row, column_mapping.get("parent_name"))
            parent_phone = _get_mapped_value(row, column_mapping.get("parent_phone"))

            if not first_name:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="child_first_name is required"))
                result.skipped += 1
                continue
            if not parent_name:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="parent_name is required"))
                result.skipped += 1
                continue
            if not parent_phone:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="parent_phone is required"))
                result.skipped += 1
                continue

            last_name = _get_mapped_value(row, column_mapping.get("child_last_name"))
            dob = _parse_date(_get_mapped_value(row, column_mapping.get("child_dob")))
            school = _get_mapped_value(row, column_mapping.get("child_school"))
            email = _get_mapped_value(row, column_mapping.get("parent_email"))
            source = _parse_lead_source(_get_mapped_value(row, column_mapping.get("source")))
            status = _parse_lead_status(_get_mapped_value(row, column_mapping.get("status")))
            notes = _get_mapped_value(row, column_mapping.get("notes"))

            phone_norm = _normalise_phone(parent_phone)

            # --- Deduplication: look for existing parent by phone in this center ---
            existing_parent = db.query(Parent).filter(
                Parent.center_id == center_id,
                Parent.phone == parent_phone,
                Parent.is_archived == False,
            ).first()
            # Also try normalised comparison if direct match fails
            if not existing_parent and phone_norm:
                all_parents = db.query(Parent).filter(
                    Parent.center_id == center_id,
                    Parent.is_archived == False,
                ).all()
                for p in all_parents:
                    if _normalise_phone(p.phone) == phone_norm:
                        existing_parent = p
                        break

            existing_child = None
            if existing_parent:
                # Check if this parent already has a child with same first_name
                links = db.query(FamilyLink).filter(
                    FamilyLink.parent_id == existing_parent.id,
                    FamilyLink.is_archived == False,
                ).all()
                for link in links:
                    child = db.query(Child).filter(
                        Child.id == link.child_id,
                        Child.center_id == center_id,
                        func.lower(Child.first_name) == first_name.lower(),
                        Child.is_archived == False,
                    ).first()
                    if child:
                        existing_child = child
                        break

            if existing_child:
                # Update existing lead if present
                existing_lead = db.query(Lead).filter(
                    Lead.child_id == existing_child.id,
                    Lead.center_id == center_id,
                    Lead.is_archived == False,
                ).first()
                if existing_lead:
                    if notes:
                        existing_lead.discovery_notes = (
                            (existing_lead.discovery_notes or "") + f"\n[CSV Import] {notes}"
                        ).strip()
                    existing_lead.updated_by_id = user_id
                    result.updated += 1
                else:
                    # Child exists but no lead - create one
                    lead = Lead(
                        center_id=center_id,
                        child_id=existing_child.id,
                        status=status,
                        source=source,
                        discovery_notes=notes,
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                    db.add(lead)
                    result.created += 1
            else:
                # Create new child
                enquiry_id = _generate_next_enquiry_id(db)
                child = Child(
                    center_id=center_id,
                    enquiry_id=enquiry_id,
                    first_name=first_name,
                    last_name=last_name,
                    dob=dob,
                    school=school,
                    notes=notes,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(child)
                db.flush()  # need child.id

                # Create or reuse parent
                if existing_parent:
                    parent = existing_parent
                else:
                    parent = Parent(
                        center_id=center_id,
                        name=parent_name,
                        phone=parent_phone,
                        email=email,
                        created_by_id=user_id,
                        updated_by_id=user_id,
                    )
                    db.add(parent)
                    db.flush()

                # Family link
                family_link = FamilyLink(
                    center_id=center_id,
                    child_id=child.id,
                    parent_id=parent.id,
                    relationship_type="parent",
                    is_primary_contact=True,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(family_link)

                # Lead
                lead = Lead(
                    center_id=center_id,
                    child_id=child.id,
                    status=status,
                    source=source,
                    discovery_notes=notes,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(lead)
                result.created += 1

        except Exception as e:
            logger.warning(f"Leads import row {idx} error: {e}")
            result.errors.append(ImportErrorSchema(row=idx, message=str(e)))
            result.skipped += 1

    db.commit()
    return result


# ---------------------------------------------------------------------------
# Enrollments Import
# ---------------------------------------------------------------------------

def import_enrollments(
    db: Session,
    file_bytes: bytes,
    column_mapping: Dict[str, Optional[str]],
    center_id: int,
    user_id: int,
) -> ImportResult:
    """
    Import enrollments from CSV.

    Requires matching an existing child by enquiry_id or child_name.
    Creates an Enrollment record (and optionally links to a Batch).
    Deduplication: if the child already has an active enrollment in the
    same batch with the same plan_type, the row is skipped.
    """
    text = _decode_csv(file_bytes)
    _headers, rows = _parse_csv(text)
    result = ImportResult()

    for idx, row in enumerate(rows, start=2):
        try:
            child = _resolve_child(db, row, column_mapping, center_id)
            if not child:
                enquiry_val = _get_mapped_value(row, column_mapping.get("enquiry_id"))
                name_val = _get_mapped_value(row, column_mapping.get("child_name"))
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message=f"Child not found (enquiry_id={enquiry_val}, name={name_val})"
                ))
                result.skipped += 1
                continue

            plan_type = _parse_plan_type(
                _get_mapped_value(row, column_mapping.get("plan_type"))
            )
            if not plan_type:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="plan_type is required and must be valid"))
                result.skipped += 1
                continue

            start_date = _parse_date(_get_mapped_value(row, column_mapping.get("start_date")))
            end_date = _parse_date(_get_mapped_value(row, column_mapping.get("end_date")))
            status = _parse_enrollment_status(
                _get_mapped_value(row, column_mapping.get("status"))
            )
            notes = _get_mapped_value(row, column_mapping.get("notes"))
            batch_name = _get_mapped_value(row, column_mapping.get("batch_name"))

            batch = None
            if batch_name:
                batch = _find_batch_by_name(db, batch_name, center_id)

            # Dedup: same child + plan_type + batch + active
            dedup_query = db.query(Enrollment).filter(
                Enrollment.child_id == child.id,
                Enrollment.center_id == center_id,
                Enrollment.plan_type == plan_type,
                Enrollment.is_archived == False,
            )
            if batch:
                dedup_query = dedup_query.filter(Enrollment.batch_id == batch.id)
            if start_date:
                dedup_query = dedup_query.filter(Enrollment.start_date == start_date)

            existing_enrollment = dedup_query.first()
            if existing_enrollment:
                # Update existing enrollment
                if end_date:
                    existing_enrollment.end_date = end_date
                if notes:
                    existing_enrollment.notes = (
                        (existing_enrollment.notes or "") + f"\n[CSV Import] {notes}"
                    ).strip()
                existing_enrollment.status = status
                existing_enrollment.updated_by_id = user_id
                result.updated += 1
            else:
                enrollment = Enrollment(
                    center_id=center_id,
                    child_id=child.id,
                    batch_id=batch.id if batch else None,
                    plan_type=plan_type,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    notes=notes,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(enrollment)
                result.created += 1

        except Exception as e:
            logger.warning(f"Enrollments import row {idx} error: {e}")
            result.errors.append(ImportErrorSchema(row=idx, message=str(e)))
            result.skipped += 1

    db.commit()
    return result


# ---------------------------------------------------------------------------
# Attendance Import
# ---------------------------------------------------------------------------

def import_attendance(
    db: Session,
    file_bytes: bytes,
    column_mapping: Dict[str, Optional[str]],
    center_id: int,
    user_id: int,
) -> ImportResult:
    """
    Import attendance records from CSV.

    Resolves child by enquiry_id / child_name, then finds or creates
    a ClassSession for the batch + date, and creates an Attendance record.
    Deduplication: child + session = unique.
    """
    text = _decode_csv(file_bytes)
    _headers, rows = _parse_csv(text)
    result = ImportResult()

    for idx, row in enumerate(rows, start=2):
        try:
            child = _resolve_child(db, row, column_mapping, center_id)
            if not child:
                enquiry_val = _get_mapped_value(row, column_mapping.get("enquiry_id"))
                name_val = _get_mapped_value(row, column_mapping.get("child_name"))
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message=f"Child not found (enquiry_id={enquiry_val}, name={name_val})"
                ))
                result.skipped += 1
                continue

            session_date_str = _get_mapped_value(row, column_mapping.get("session_date"))
            session_date = _parse_date(session_date_str)
            if not session_date:
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message=f"Invalid or missing session_date: {session_date_str}"
                ))
                result.skipped += 1
                continue

            att_status = _parse_attendance_status(
                _get_mapped_value(row, column_mapping.get("status"))
            )
            if not att_status:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="status is required and must be valid"))
                result.skipped += 1
                continue

            batch_name = _get_mapped_value(row, column_mapping.get("batch_name"))
            batch = None
            if batch_name:
                batch = _find_batch_by_name(db, batch_name, center_id)

            # If no batch provided or found, try to derive from child's enrollment
            if not batch:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.child_id == child.id,
                    Enrollment.center_id == center_id,
                    Enrollment.is_archived == False,
                ).first()
                if enrollment and enrollment.batch_id:
                    batch = db.query(Batch).get(enrollment.batch_id)

            if not batch:
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message="Could not determine batch for attendance record"
                ))
                result.skipped += 1
                continue

            # Find or create class session
            class_session = db.query(ClassSession).filter(
                ClassSession.batch_id == batch.id,
                ClassSession.session_date == session_date,
                ClassSession.center_id == center_id,
                ClassSession.is_archived == False,
            ).first()

            if not class_session:
                class_session = ClassSession(
                    center_id=center_id,
                    batch_id=batch.id,
                    session_date=session_date,
                    start_time=batch.start_time,
                    end_time=batch.end_time,
                    status=SessionStatus.COMPLETED,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(class_session)
                db.flush()

            # Dedup: child + session
            existing = db.query(Attendance).filter(
                Attendance.class_session_id == class_session.id,
                Attendance.child_id == child.id,
                Attendance.center_id == center_id,
                Attendance.is_archived == False,
            ).first()

            if existing:
                existing.status = att_status
                existing.marked_by_user_id = user_id
                existing.marked_at = datetime.utcnow()
                existing.updated_by_id = user_id
                result.updated += 1
            else:
                # Try to find enrollment for this child
                enrollment = db.query(Enrollment).filter(
                    Enrollment.child_id == child.id,
                    Enrollment.center_id == center_id,
                    Enrollment.is_archived == False,
                ).first()

                attendance = Attendance(
                    center_id=center_id,
                    class_session_id=class_session.id,
                    child_id=child.id,
                    enrollment_id=enrollment.id if enrollment else None,
                    status=att_status,
                    marked_by_user_id=user_id,
                    marked_at=datetime.utcnow(),
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(attendance)
                result.created += 1

        except Exception as e:
            logger.warning(f"Attendance import row {idx} error: {e}")
            result.errors.append(ImportErrorSchema(row=idx, message=str(e)))
            result.skipped += 1

    db.commit()
    return result


# ---------------------------------------------------------------------------
# Skill Progress Import
# ---------------------------------------------------------------------------

def import_progress(
    db: Session,
    file_bytes: bytes,
    column_mapping: Dict[str, Optional[str]],
    center_id: int,
    user_id: int,
) -> ImportResult:
    """
    Import skill progress records from CSV.

    Resolves child by enquiry_id / child_name and skill by name.
    Deduplication: child + skill = unique (upsert).
    """
    text = _decode_csv(file_bytes)
    _headers, rows = _parse_csv(text)
    result = ImportResult()

    # Build a lookup cache for skills by name (case-insensitive)
    all_skills = db.query(Skill).all()
    skill_lookup: Dict[str, Skill] = {}
    for s in all_skills:
        skill_lookup[s.name.strip().lower()] = s

    for idx, row in enumerate(rows, start=2):
        try:
            child = _resolve_child(db, row, column_mapping, center_id)
            if not child:
                enquiry_val = _get_mapped_value(row, column_mapping.get("enquiry_id"))
                name_val = _get_mapped_value(row, column_mapping.get("child_name"))
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message=f"Child not found (enquiry_id={enquiry_val}, name={name_val})"
                ))
                result.skipped += 1
                continue

            skill_name = _get_mapped_value(row, column_mapping.get("skill_name"))
            if not skill_name:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="skill_name is required"))
                result.skipped += 1
                continue

            skill = skill_lookup.get(skill_name.strip().lower())
            if not skill:
                result.errors.append(ImportErrorSchema(
                    row=idx,
                    message=f"Skill not found: {skill_name}"
                ))
                result.skipped += 1
                continue

            level = _parse_skill_level(
                _get_mapped_value(row, column_mapping.get("level"))
            )
            if not level:
                result.errors.append(ImportErrorSchema(
                    row=idx, message="level is required and must be valid"))
                result.skipped += 1
                continue

            notes = _get_mapped_value(row, column_mapping.get("notes"))

            # Upsert: child + skill
            existing = db.query(SkillProgress).filter(
                SkillProgress.child_id == child.id,
                SkillProgress.skill_id == skill.id,
                SkillProgress.center_id == center_id,
                SkillProgress.is_archived == False,
            ).first()

            if existing:
                existing.level = level
                existing.last_updated_at = datetime.utcnow()
                existing.updated_by_user_id = user_id
                existing.updated_by_id = user_id
                if notes:
                    existing.notes = (
                        (existing.notes or "") + f"\n[CSV Import] {notes}"
                    ).strip()
                result.updated += 1
            else:
                progress = SkillProgress(
                    center_id=center_id,
                    child_id=child.id,
                    skill_id=skill.id,
                    level=level,
                    last_updated_at=datetime.utcnow(),
                    updated_by_user_id=user_id,
                    notes=notes,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                )
                db.add(progress)
                result.created += 1

        except Exception as e:
            logger.warning(f"Progress import row {idx} error: {e}")
            result.errors.append(ImportErrorSchema(row=idx, message=str(e)))
            result.skipped += 1

    db.commit()
    return result
