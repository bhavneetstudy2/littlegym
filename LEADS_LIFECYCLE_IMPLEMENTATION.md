# Leads Lifecycle Implementation - Progress Summary

## ✅ Completed

### 1. Database Schema Enhancements

**Updated Enums:**
- `LeadStatus`: Now includes complete lifecycle states
  - ENQUIRY_RECEIVED
  - DISCOVERY_COMPLETED
  - IV_SCHEDULED
  - IV_COMPLETED
  - IV_NO_SHOW
  - FOLLOW_UP_PENDING
  - CONVERTED
  - CLOSED_LOST

- `LeadSource`: Added PHONE_CALL and ONLINE

- **New Enums:**
  - `IVOutcome`: INTERESTED_ENROLL_NOW, INTERESTED_ENROLL_LATER, NOT_INTERESTED, NO_SHOW
  - `FollowUpStatus`: PENDING, COMPLETED, CANCELLED
  - `FollowUpOutcome`: ENROLLED, POSTPONED, LOST, SCHEDULED_IV

**Enhanced Models:**

1. **Lead Model** (`app/models/lead.py`):
   - Discovery form fields: school, preferred_schedule, parent_expectations (JSON)
   - Discovery tracking: discovery_completed_at
   - Closure tracking: closed_reason, closed_at
   - Conversion tracking: enrollment_id, converted_at
   - Relationships: intro_visits, follow_ups, enrollment

2. **IntroVisit Model** (`app/models/intro_visit.py`):
   - Added: outcome (IVOutcome enum)

3. **New FollowUp Model** (`app/models/follow_up.py`):
   - lead_id, scheduled_date, completed_at
   - status (FollowUpStatus), outcome (FollowUpOutcome)
   - notes, assigned_to_user_id
   - Cascade delete with lead

**Migration Created:**
- File: `alembic/versions/enhance_leads_lifecycle.py`
- Updates all enum types
- Adds new columns to leads table
- Creates follow_ups table
- Preserves data during migration

### 2. Pydantic Schemas

**Created:** `app/schemas/lead_enhanced.py`

**Key Schemas:**
- `EnquiryFormCreate`: Complete discovery form matching your UI
  - Child: first_name, last_name, dob, age, gender
  - Parent: name, contact_number, email
  - Discovery: school, source, parent_expectations, preferred_schedule, remarks

- `DiscoveryFormUpdate`: Update discovery details post-enquiry

- `LeadSummary`: For list views with essential info
- `LeadDetail`: Complete lead with all related data

- `IntroVisitCreate/Update/Response`: Full IV lifecycle
- `FollowUpCreate/Update/Response`: Follow-up management

- `LeadClose`: Mark lead as lost
- `LeadConvert`: Convert to enrollment
- `LeadFilter`: Advanced filtering for dashboard

## ✅ Completed - Backend Implementation

### 3. Service Layer - Business Logic

**File:** [`app/services/lead_service.py`](backend/app/services/lead_service.py:220)

**Enhanced Methods:**

1. **`create_enquiry()`** - Creates lead from enquiry form
   - Auto-generates Enquiry ID (TLGC0001, TLGC0002, ...)
   - Creates child, parent (reuses if phone exists), family link
   - Sets status to ENQUIRY_RECEIVED
   - Stores discovery form fields

2. **`update_discovery_form()`** - Updates discovery details
   - Updates school, schedule, expectations, notes
   - Marks discovery as completed with timestamp
   - Changes status to DISCOVERY_COMPLETED

3. **`schedule_intro_visit()`** - Schedules IV
   - Creates IntroVisit record
   - Auto-updates lead status to IV_SCHEDULED

4. **`update_intro_visit()`** - Updates IV with outcome
   - Handles attendance and outcome recording
   - Auto-updates lead status based on outcome:
     - INTERESTED_ENROLL_NOW → IV_COMPLETED
     - INTERESTED_ENROLL_LATER → FOLLOW_UP_PENDING
     - NOT_INTERESTED → FOLLOW_UP_PENDING
     - NO_SHOW → IV_NO_SHOW

5. **`create_follow_up()`** - Creates follow-up task
   - Sets status to PENDING
   - Updates lead status to FOLLOW_UP_PENDING

6. **`update_follow_up()`** - Updates follow-up with outcome
   - Records completion and outcome (ENROLLED, LOST, POSTPONED, SCHEDULED_IV)

7. **`convert_lead()`** - Marks lead as converted
   - Links to enrollment_id
   - Sets status to CONVERTED
   - Preserves lead for history

8. **`close_lead()`** - Marks lead as lost
   - Records closure reason
   - Sets status to CLOSED_LOST
   - Preserves lead for history

9. **`get_pending_follow_ups()`** - Gets all pending follow-ups
10. **`get_lead_with_details()`** - Gets complete lead with all relationships

### 4. API Endpoints

**File:** [`app/api/v1/leads.py`](backend/app/api/v1/leads.py:316)

**Implemented Routes:**

```python
# Enquiry & Discovery
POST   /api/v1/leads/enquiry          # ✅ Submit new enquiry form
GET    /api/v1/leads                  # ✅ List leads with filters
GET    /api/v1/leads/{id}             # ✅ Get lead details
GET    /api/v1/leads/{id}/details     # ✅ Get complete lead with parents/IVs
PATCH  /api/v1/leads/{id}/discovery   # ✅ Update discovery form
PATCH  /api/v1/leads/{id}/status      # ✅ Update lead status

# Intro Visits
POST   /api/v1/leads/{id}/intro-visit        # ✅ Schedule IV for lead
PATCH  /api/v1/intro-visits/{id}             # ✅ Update IV with outcome
GET    /api/v1/intro-visits/{id}             # ✅ Get IV details
GET    /api/v1/intro-visits                  # ✅ List IVs with filters

# Follow-ups
POST   /api/v1/leads/{id}/follow-up          # ✅ Create follow-up
GET    /api/v1/leads/{id}/follow-ups         # ✅ List follow-ups for lead
PATCH  /api/v1/follow-ups/{id}               # ✅ Update follow-up with outcome
GET    /api/v1/follow-ups/pending            # ✅ Get all pending follow-ups

# Conversion & Closure
POST   /api/v1/leads/{id}/convert            # ✅ Mark as converted (link enrollment)
POST   /api/v1/leads/{id}/close              # ✅ Mark as lost

# Legacy endpoints (still functional)
POST   /api/v1/leads                         # Old lead creation
PATCH  /api/v1/leads/{id}                    # Old lead update
POST   /api/v1/leads/{id}/mark-dead          # Old mark dead
```

**RBAC Enforcement:**
- All endpoints enforce role-based access (COUNSELOR, CENTER_ADMIN, SUPER_ADMIN)
- Trainers can update intro visits with outcomes
- Tenant isolation enforced (center_id filtering)
- Super admin can access all centers

## 📋 TODO (Remaining)

- [x] Implement API endpoints ✅
- [x] Create leads service layer with business logic ✅
- [x] Add RBAC permissions for lead management ✅
- [ ] Build frontend enquiry form (React component)
- [ ] Build leads dashboard with pipeline view
- [ ] Add follow-up reminders/notifications (Phase 2)
- [ ] **Run database migration** (IMPORTANT - Must run before testing)
- [ ] Test complete lifecycle flow

## Key Features Implemented

### ✅ Single Source of Truth
- Lead status field tracks complete lifecycle
- No deletion - leads marked as CONVERTED or CLOSED_LOST

### ✅ Complete Discovery Form
- Matches your UI design
- Captures parent expectations as JSON array
- Flexible schedule preferences

### ✅ IV Outcome Tracking
- Clear outcomes: enroll now, enroll later, not interested, no-show
- Auto-status updates based on outcome

### ✅ Follow-up Management
- Multiple follow-ups per lead
- Status and outcome tracking
- Assignment to staff members

### ✅ Edge Case Handling
- IV no-shows tracked separately
- Multiple follow-ups supported
- Delayed enrollment via follow-up outcomes
- Conversion preserves lead history

### ✅ Scalable Design
- Normalized database structure
- Efficient indexes on status, lead_id
- JSON for flexible parent_expectations
- Cascade relationships for data integrity

## API Usage Examples

### 1. Create New Enquiry
```bash
POST /api/v1/leads/enquiry
Authorization: Bearer <token>

{
  "center_id": 1,  # Required for super admin, optional for others
  "child_first_name": "Mehr",
  "child_last_name": "Goyal",
  "child_dob": "2020-06-15",
  "age": 5,
  "gender": "Girl",
  "parent_name": "Anshu Goyal",
  "contact_number": "+91-9876543210",
  "email": "anshu@example.com",
  "school": "Delhi Public School",
  "source": "WALK_IN",
  "parent_expectations": ["child_development", "physical_activity", "socialization_skills"],
  "preferred_schedule": "Mon/Wed/Fri - 4:00 PM to 5:00 PM",
  "remarks": "Interested in Pre-K Gym program",
  "assigned_to_user_id": 5
}
```

### 2. Update Discovery Form
```bash
PATCH /api/v1/leads/123/discovery
Authorization: Bearer <token>

{
  "school": "Modern School",
  "preferred_schedule": "Tue/Thu - 5:00 PM",
  "parent_expectations": ["physical_activity", "confidence_building"],
  "discovery_notes": "Spoke with father, very interested in gymnastics"
}
```

### 3. Schedule Intro Visit
```bash
POST /api/v1/leads/123/intro-visit
Authorization: Bearer <token>

{
  "lead_id": 123,
  "scheduled_at": "2026-02-15T16:00:00",
  "batch_id": 5,
  "trainer_user_id": 8
}
```

### 4. Mark IV Attended with Outcome
```bash
PATCH /api/v1/intro-visits/45
Authorization: Bearer <token>

{
  "attended_at": "2026-02-15T16:10:00",
  "outcome": "INTERESTED_ENROLL_NOW",
  "outcome_notes": "Child enjoyed the session, parent ready to enroll"
}
```

### 5. Create Follow-up
```bash
POST /api/v1/leads/123/follow-up
Authorization: Bearer <token>

{
  "lead_id": 123,
  "scheduled_date": "2026-02-20T10:00:00",
  "notes": "Call parent to discuss enrollment plans",
  "assigned_to_user_id": 5
}
```

### 6. Update Follow-up with Outcome
```bash
PATCH /api/v1/follow-ups/67
Authorization: Bearer <token>

{
  "completed_at": "2026-02-20T10:30:00",
  "status": "COMPLETED",
  "outcome": "ENROLLED",
  "notes": "Parent enrolled child in weekly plan"
}
```

### 7. Convert Lead (After Enrollment Created)
```bash
POST /api/v1/leads/123/convert
Authorization: Bearer <token>

{
  "enrollment_id": 456
}
```

### 8. Close Lead as Lost
```bash
POST /api/v1/leads/123/close
Authorization: Bearer <token>

{
  "reason": "Parent found program too expensive, joined another gym"
}
```

### 9. Get Pending Follow-ups
```bash
GET /api/v1/leads/follow-ups/pending?assigned_to=5
Authorization: Bearer <token>
```

## Database Migration Instructions

**IMPORTANT:** Run this migration before using the new lifecycle features.

```bash
cd backend

# Review migration
alembic history

# Run migration
alembic upgrade head

# Verify migration
alembic current
```

## Next Steps

1. ✅ **Backend Complete** - Service layer and API endpoints implemented
2. 🔄 **Run Migration** - Execute `enhance_leads_lifecycle` migration
3. 🔄 **Build Frontend** - Create enquiry form and leads dashboard
4. 🔄 **Test System** - End-to-end testing of complete lifecycle
5. 📅 **Phase 2** - Follow-up reminders, dashboard stats, pipeline view

## Workflow Summary

```
1. ENQUIRY_RECEIVED (POST /enquiry)
   ↓
2. DISCOVERY_COMPLETED (PATCH /{id}/discovery)
   ↓
3. IV_SCHEDULED (POST /{id}/intro-visit)
   ↓
4. IV_COMPLETED / IV_NO_SHOW (PATCH /intro-visits/{id})
   ↓
5. FOLLOW_UP_PENDING (POST /{id}/follow-up)
   ↓
6. Either:
   - CONVERTED (POST /{id}/convert) → Enrollment
   - CLOSED_LOST (POST /{id}/close) → End

Lead record is NEVER deleted - preserved for history
```
