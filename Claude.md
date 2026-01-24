The Little Gym – Central CRM + Student Progress Platform (PRD + Architecture Spec)
1) Problem Statement
Little Gym centers currently manage leads, onboarding, enrollment, attendance, and student progress using Excel sheets. Each center uses its own format, leading to:

inconsistent data structures and definitions

manual follow-ups and missed renewals

no unified report cards / progress tracking

difficult cross-center analytics and support

weak authorization controls (trainers vs admins)

2) Goals
Build a central multi-center application that standardizes:

Lead capture + discovery

Introductory visit scheduling + attendance

Follow-up pipeline (dead lead vs enrolled)

Enrollment + payments + discounts

Attendance tracking

Curriculum skill progress tracking + report cards

Renewals + expiry alerts

Role-based access control (trainer/admin/super-admin)

3) Non-Goals (for MVP)
Full accounting/ledger replacement (keep payments as operational tracking)

Marketing automation engine (only basic follow-up tasks/notes)

Payroll/HR

Parent-facing app (optional Phase 2)

4) Users & Roles
Roles
Super Admin (HQ)

Create/manage centers

Manage global curriculum templates & skills

View cross-center dashboards

Manage pricing/enrollment plan templates (optional)

Manage user roles/permissions

Center Admin

Full access within their center

Manage leads, schedules, enrollment, payments, discounts

Create batches/classes

View reports, renewals, and progress

Trainer

Can view assigned batches/classes

Mark attendance for sessions they teach

Update skill progress for students in their classes

Cannot see financial details (configurable)

Cannot edit enrollments, discounts, or delete records

Front Desk / Counselor (Optional role)

Manage leads and follow-ups

Schedule intro visits

Cannot edit curriculum progress (optional restriction)

Authorization Model
Multi-tenant by Center: every record belongs to a center.

Users have role + center_id (except super admin).

Enforce permission checks at API layer + DB row filtering.

5) Core Workflow (Lifecycle)
Stage A: Discovery / Lead Capture
Parent comes in / calls / DM / walk-in.

Capture:

Child: name, DOB/age, school, interests, notes

Parent(s): name(s), phone numbers, email (optional)

Source: walk-in, referral, Instagram, etc.

Preferred days/timings (optional)

Status: DISCOVERY

Outcome: Create a Lead record + Discovery form details.

Stage B: Introductory Visit (Trial Class)
Once Discovery is done, plan intro visit:

schedule date & time

assign batch/class

assign trainer (optional)

capture when kid attended + attended batch

Data:

Intro visit record: lead_id, batch_id, scheduled_at, attended_at, outcome_notes

Lead status moves to:

INTRO_SCHEDULED → INTRO_ATTENDED (if attended)

NO_SHOW (if not attended)

Then to FOLLOW_UP

Stage C: Follow-Up
After intro:

follow-up tasks created (call/WhatsApp)

lead can become:

DEAD_LEAD (reason: not interested, cost, timing, moved away, etc.)

ENROLLED

Stage D: Enrollment
On enrollment, capture:

Child + parent info (link to existing)

Enrollment plan type:

Pay-per-visit / Weekly / Monthly / Quarterly / Yearly / Custom

Start date, end date (or visits count)

Days selected (Mon/Wed/Fri etc.)

Batch assignment(s)

Payment info:

amount, method (cash/UPI/card/bank), reference id

discounts (type + value + reason + approver)

invoice/receipt number (optional)

Record goes into “Active Students” and is visible in attendance.

Stage E: Attendance + Progress
For each class session:

trainer marks attendance

trainer updates curriculum skills progress:

skills like cartwheel, monkey kick etc.

progress measured by levels (e.g., Not Started / In Progress / Achieved / Mastered)

system can generate report cards per term/month.

Stage F: Renewal
enrollment nearing end triggers alert

renewal can be created as:

new enrollment linked to student

carry-forward batch/day preferences

renewal tracking & history retained

6) Entities & Data Model (Relational)
Multi-tenant base fields
Every center-scoped table includes:

center_id (FK)

created_at, updated_at

created_by, updated_by (FK User)

is_archived (soft delete preferred)

Tables (Core)
centers
id, name, city, timezone, address, phone

users
id, center_id (nullable for super admin), name, email, phone

role enum: SUPER_ADMIN | CENTER_ADMIN | TRAINER | COUNSELOR

password_hash or SSO fields

status active/inactive

parents
id, center_id

name, phone, email (optional)

notes

children
id, center_id

first_name, last_name (or single name)

dob (nullable if only age known)

school (text)

interests (text or json array)

notes

family_links
Supports multiple parents per child:

id, center_id, child_id, parent_id

relationship (mother/father/guardian/other)

is_primary_contact boolean

leads
One lead per child entry (or allow multiple lead attempts):

id, center_id

child_id

status enum:

DISCOVERY | INTRO_SCHEDULED | INTRO_ATTENDED | NO_SHOW | FOLLOW_UP | DEAD_LEAD | ENROLLED

source enum/text

discovery_notes

dead_lead_reason (nullable)

assigned_to_user_id (counselor/admin)

intro_visits
id, center_id, lead_id

scheduled_at, attended_at nullable

batch_id nullable until assigned

trainer_user_id nullable

outcome_notes

batches
id, center_id

name (e.g., “Pre-K Gym 4–6”)

age_min, age_max

days_of_week (json: ["Mon","Wed"])

start_time, end_time

capacity

active boolean

class_sessions
You can generate sessions for each batch/day OR create as needed:

id, center_id, batch_id

session_date

start_time, end_time

trainer_user_id

status scheduled/completed/cancelled

enrollments
id, center_id, child_id

plan_type enum: PAY_PER_VISIT | WEEKLY | MONTHLY | QUARTERLY | YEARLY | CUSTOM

start_date, end_date (nullable for visit-based)

visits_included (nullable)

visits_used (default 0)

days_selected json

batch_id (primary batch)

status enum: ACTIVE | EXPIRED | CANCELLED | PAUSED

notes

payments
id, center_id, enrollment_id

amount, currency (INR)

method enum: CASH | UPI | CARD | BANK_TRANSFER | OTHER

reference (txn id)

paid_at

discount_total (computed) optional

net_amount

discounts
id, center_id, enrollment_id

type enum: PERCENT | FLAT

value

reason

approved_by_user_id

applied_at

attendance
Per session per child:

id, center_id

class_session_id

child_id

status enum: PRESENT | ABSENT | MAKEUP | TRIAL | CANCELLED

marked_by_user_id

marked_at

notes

Curriculum / Progress Tracking
curricula
id, name (e.g., “Gymnastics Foundation Level 1”)

global or center-specific

skills
id, curriculum_id

name (cartwheel, monkey kick, etc.)

category (optional)

display_order

skill_progress
id, center_id

child_id, skill_id

level enum: NOT_STARTED | IN_PROGRESS | ACHIEVED | MASTERED

last_updated_at

updated_by_user_id

notes

report_cards
id, center_id

child_id

period_start, period_end

generated_at

generated_by_user_id

summary_notes

Optionally snapshot skill results in JSON for historical freeze

7) Key Screens (MVP)
1) Lead Intake / Discovery Form
Create child + parent(s)

Capture interest, school, DOB/age, notes

Save as lead

2) Intro Visit Scheduling
Lead list with statuses

Schedule intro visit, assign batch, auto-create follow-up task

3) Follow-Up Pipeline (Kanban style optional)
Columns: Discovery → Intro Scheduled → Intro Attended → Follow-Up → Enrolled / Dead

Add notes + next follow-up date

Quick action: Mark Dead Lead (with reason)

Quick action: Convert to Enrollment

4) Enrollment Creation
Plan type + dates/visits

Days selected + batch

Payment + discount + approval

Auto status = Active

Auto move lead status to Enrolled

5) Attendance
By batch → by session date

Trainer sees “today’s sessions”

Mark present/absent quickly

Auto-increment visits_used for visit-based plans

Flag expired enrollment

6) Progress / Skills
Child profile → skills checklist with levels

Batch view: quickly update multiple kids for a skill (optional)

Report card generator (by date range)

7) Renewals Dashboard
“Expiring in 7/14/30 days”

WhatsApp/call notes

Renew button that copies last plan details

8) Business Rules (Important)
Lead → Enrollment conversion
Enrollment requires a child profile + at least one parent contact.

A lead can have multiple intro visits; latest attended visit considered for conversion context.

Enrollment validity
Date-based plan: active if today between start_date and end_date

Visit-based plan: active if visits_used < visits_included and not expired (optional expiry rule)

If inactive/expired: attendance marking should warn and optionally block (configurable per center)

Attendance rules
Trainers can only mark attendance for sessions they are assigned to OR batches they are assigned to.

Admin can override attendance.

Discount approval
Discounts above a threshold require Center Admin approval (configurable).

Discount log must keep approver and reason.

Progress tracking
Skill progress updates should be auditable (track who updated + when).

Report cards should freeze results for the period (snapshot) so later edits don’t rewrite history.

9) Integrations (Phase 2)
WhatsApp template message integration for follow-ups/renewals

Payment gateway reconciliation (optional)

Parent portal (view attendance + report card)

10) Architecture Proposal
High-Level
A multi-tenant SaaS-style app with:

Web app for center staff (admin/counselor/trainer)

Backend API with role-based authorization

Relational database (PostgreSQL recommended)

Optional background jobs for reminders, renewal alerts, report generation

Recommended Stack (suggestion; can be adjusted)
Frontend: React/Next.js

Backend: Node (NestJS/Express) or Python (Django/FastAPI)

DB: PostgreSQL

Auth: JWT sessions + refresh tokens (or hosted auth later)

Hosting: any cloud (AWS/GCP/Azure) + managed Postgres

Multi-tenancy approach
Single DB, shared schema.

Every row includes center_id.

Enforce center_id filtering in queries + middleware guard.

Super Admin bypasses center restriction.

Services/Modules (Backend)
Auth & Users

Centers

Leads & Discovery

Scheduling (Batches & Sessions)

Enrollment & Payments

Attendance

Curriculum & Skill Progress

Renewals & Notifications

Background Jobs
nightly job to:

compute “expiring soon”

mark enrollments expired (date-based)

create renewal reminders

11) API Design (MVP Endpoints)
Auth
POST /auth/login

POST /auth/logout

GET /auth/me

Centers (Super Admin)
POST /centers

GET /centers

PATCH /centers/:id

Users
POST /users (admin/super)

GET /users (center scoped)

PATCH /users/:id

PATCH /users/:id/status

Leads & Discovery
POST /leads (creates child+parent+lead)

GET /leads?status=&q=&from=&to=

GET /leads/:id

PATCH /leads/:id (notes/status/assign)

POST /leads/:id/mark-dead (reason)

Intro Visits
POST /intro-visits (schedule)

PATCH /intro-visits/:id/mark-attended

GET /intro-visits?date=

Batches & Sessions
POST /batches

GET /batches

POST /class-sessions (or auto-generate)

GET /class-sessions?date=&batch_id=

Enrollment & Payments
POST /enrollments

GET /enrollments?status=&child_id=

PATCH /enrollments/:id (admin)

POST /payments

POST /discounts (admin/approval)

GET /children/:id/enrollments

Attendance
POST /attendance/mark (bulk marking)

GET /attendance?session_id=

GET /children/:id/attendance?from=&to=

Curriculum & Skills
GET /curricula

POST /curricula (super admin)

POST /skills (super admin)

GET /children/:id/skills

POST /skill-progress (trainer/admin; bulk supported)

Report Cards
POST /report-cards/generate

GET /report-cards?child_id=

GET /report-cards/:id

Renewals
GET /renewals/expiring?days=7|14|30

POST /renewals/:child_id (creates new enrollment based on latest)

12) UI/UX Notes (Key Productivity Principles)
Fast data entry (minimal clicks)

Bulk attendance marking

“Today’s sessions” for trainers

Prominent warnings: expired plan / unpaid / missing contact info

Search across child/parent phone numbers

13) Data Migration from Excel
Import Strategy (MVP)
Provide CSV import tools per module:

Leads import (child + parent + status)

Students/enrollments import (child + enrollment)

Attendance import (optional later)

Skills progress import (optional later)

Approach
Map Excel columns to canonical fields.

Validate duplicates by:

parent phone + child name + DOB (if present)

Provide import summary:

created / updated / skipped rows with reasons

14) Audit, Logging, and Safety
Every update stores updated_by and timestamp

Track sensitive changes:

discount approvals

payment edits

enrollment cancellations

Soft delete for children/leads (archive)

Privacy:

No public profiles

Avoid exposing full financial details to trainers

Parent phone numbers visible only if role allows (configurable)

15) MVP Milestones (Build Order)
Auth + Centers + Users + RBAC

Leads + Discovery + Intro visit scheduling

Follow-up pipeline + notes

Enrollment + payments + discounts

Batches + sessions + attendance

Curriculum + skills + progress updates

Report cards

Renewals dashboard + reminders

CSV import

16) Acceptance Criteria (Examples)
Trainer cannot view/edit payments or discounts.

Center Admin sees only their center’s records.

Lead can be converted to Enrollment in < 60 seconds.

Attendance marking works in bulk for a session.

Report card shows skill levels for a chosen period and can be regenerated.

Renewals list correctly shows enrollments expiring within selected window.

17) Open Decisions (Safe Defaults to Start Coding)
If not specified, implement these defaults:

Skill levels: Not Started / In Progress / Achieved / Mastered

Report card period: selectable date range (default last 30 days)

Enrollment:

date-based plans require start_date and end_date

visit-based plan uses visits_included

Discount approval:

any discount requires admin role (can loosen later)

Attendance:

marking is allowed but warns if enrollment expired (block can be toggle later)

18) Suggested Folder/Module Layout (Backend)
/modules/auth

/modules/users

/modules/centers

/modules/leads

/modules/intro-visits

/modules/batches

/modules/sessions

/modules/enrollments

/modules/payments

/modules/attendance

/modules/curriculum

/modules/progress

/modules/report-cards

/modules/renewals

/common/rbac

/common/validators

/common/db

