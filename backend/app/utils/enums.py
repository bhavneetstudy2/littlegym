from enum import Enum


class UserRole(str, Enum):
    """User roles for role-based access control"""
    SUPER_ADMIN = "SUPER_ADMIN"
    CENTER_ADMIN = "CENTER_ADMIN"
    TRAINER = "TRAINER"
    COUNSELOR = "COUNSELOR"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class LeadStatus(str, Enum):
    """Lead progression status"""
    ENQUIRY_RECEIVED = "ENQUIRY_RECEIVED"
    DISCOVERY_COMPLETED = "DISCOVERY_COMPLETED"
    IV_SCHEDULED = "IV_SCHEDULED"
    IV_COMPLETED = "IV_COMPLETED"
    IV_NO_SHOW = "IV_NO_SHOW"
    FOLLOW_UP_PENDING = "FOLLOW_UP_PENDING"
    CONVERTED = "CONVERTED"
    CLOSED_LOST = "CLOSED_LOST"


class LeadSource(str, Enum):
    """Lead source channels"""
    WALK_IN = "WALK_IN"
    PHONE_CALL = "PHONE_CALL"
    ONLINE = "ONLINE"
    REFERRAL = "REFERRAL"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    GOOGLE = "GOOGLE"
    OTHER = "OTHER"


class IVOutcome(str, Enum):
    """Intro Visit outcome"""
    INTERESTED_ENROLL_NOW = "INTERESTED_ENROLL_NOW"
    INTERESTED_ENROLL_LATER = "INTERESTED_ENROLL_LATER"
    NOT_INTERESTED = "NOT_INTERESTED"
    NO_SHOW = "NO_SHOW"


class FollowUpStatus(str, Enum):
    """Follow-up status"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FollowUpOutcome(str, Enum):
    """Follow-up outcome"""
    ENROLLED = "ENROLLED"
    POSTPONED = "POSTPONED"
    LOST = "LOST"
    SCHEDULED_IV = "SCHEDULED_IV"


class PlanType(str, Enum):
    """Enrollment plan types"""
    PAY_PER_VISIT = "PAY_PER_VISIT"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class EnrollmentStatus(str, Enum):
    """Enrollment status"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class PaymentMethod(str, Enum):
    """Payment methods"""
    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    OTHER = "OTHER"


class AttendanceStatus(str, Enum):
    """Attendance status"""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    MAKEUP = "MAKEUP"
    TRIAL = "TRIAL"
    CANCELLED = "CANCELLED"


class SkillLevel(str, Enum):
    """Skill progress levels"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"
    MASTERED = "MASTERED"


class SessionStatus(str, Enum):
    """Class session status"""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DiscountType(str, Enum):
    """Discount types"""
    PERCENT = "PERCENT"
    FLAT = "FLAT"
