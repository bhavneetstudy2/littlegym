# Little Gym CRM - Application Testing Guide

## System Status

### Backend
- **Status**: Running ✅
- **URL**: http://localhost:8000
- **Database**: Supabase PostgreSQL (Connected)
- **Health Check**: http://localhost:8000/health

### Frontend
- **Status**: Running ✅
- **URL**: http://localhost:3000
- **Framework**: Next.js 14

### Data Status (Chandigarh Center)
- Children: 300
- Parents: 300
- Leads: 300
- Enrollments: 115
- Intro Visits: 71
- Batches: 10
- Skills: 16

---

## Login Credentials

### Super Admin
- **Email**: `admin@thelittlegym.in`
- **Password**: `admin123`
- **Permissions**: Full access to all centers

### Center Admin (Chandigarh)
- **Email**: `admin.chd@thelittlegym.in`
- **Password**: `admin123`
- **Permissions**: Full access to Chandigarh center only

---

## Testing Flow

### 1. Login as Super Admin

1. Navigate to http://localhost:3000
2. You'll see the login page
3. Enter credentials:
   - Email: `admin@thelittlegym.in`
   - Password: `admin123`
4. Click "Sign In"

**Expected Result**:
- Successful login
- Redirect to dashboard
- See "Select a Center" screen with 3 centers:
  - The Little Gym - Chandigarh
  - The Little Gym - Delhi North
  - The Little Gym - Mumbai Central

---

### 2. Center Selection

1. On the dashboard, you'll see center selection cards
2. Click on **"The Little Gym - Chandigarh"** card

**Expected Result**:
- Center selected
- Dashboard updates to show Chandigarh-specific data
- Quick stats display:
  - Leads: 300
  - Enrolled: 115
  - Today's Classes: (varies)
  - Renewals Due: (varies)
- Two main module cards visible:
  - **Lead Lifecycle** (Blue)
  - **Enrolled Students** (Green)

---

### 3. Test Leads Module

#### 3.1 View All Leads
1. Click on "Lead Lifecycle" card or navigate to `/leads`
2. View the leads list

**Expected Result**:
- See list of 300 leads
- Each lead shows:
  - Child name
  - Parent name
  - Contact number
  - Status badge (Discovery/Intro Scheduled/etc.)
  - Created date
- Status filter buttons at top:
  - All (300)
  - Discovery (236)
  - Intro Scheduled (64)
  - Follow Up
  - Enrolled
  - Dead Lead

#### 3.2 Filter Leads by Status
1. Click on "Discovery" filter button
2. Click on "Intro Scheduled" filter button

**Expected Result**:
- List updates to show only leads with selected status
- Count updates accordingly

#### 3.3 View Lead Details
1. Click on any lead from the list
2. View lead details modal/page

**Expected Result**:
- See complete lead information:
  - Child details (name, DOB, school, interests)
  - Parent details (name, phone, email)
  - Lead status and source
  - Discovery notes
  - Intro visit history (if any)

#### 3.4 Create New Lead
1. Click "New Lead" or "+ Add Lead" button
2. Fill in the form:
   - Child Name (required)
   - Parent Name (required)
   - Contact Number (required)
   - Email (optional)
   - DOB
   - School
   - Source (walk-in/google/instagram/etc.)
   - Expectations/Notes
3. Click "Save" or "Create Lead"

**Expected Result**:
- Lead created successfully
- Added to leads list
- Status set to "Discovery"

#### 3.5 Schedule Intro Visit (IV)
1. Select a lead with "Discovery" status
2. Click "Schedule IV" or "Book Intro Visit"
3. Fill in:
   - IV Date (required)
   - Batch/Class (select from dropdown)
   - Notes
4. Save

**Expected Result**:
- Intro visit scheduled
- Lead status changes to "Intro Scheduled"
- IV appears in lead's history

#### 3.6 Mark IV Attended
1. Select a lead with "Intro Scheduled" status
2. Find the scheduled IV
3. Click "Mark Attended"
4. Add outcome notes (optional)
5. Save

**Expected Result**:
- IV marked as attended
- Lead status changes to "Intro Attended"
- Lead moves to follow-up stage

---

### 4. Test Enrollments Module

#### 4.1 View All Enrolled Students
1. Click on "Enrolled Students" card or navigate to `/students` or `/enrollments`
2. View the enrollments list

**Expected Result**:
- See list of 115 enrolled students
- Each enrollment shows:
  - Student name
  - Batch name
  - Plan type (Custom/Monthly/etc.)
  - Status (Active/Expired)
  - Visits: X used / Y included
  - Total paid amount
  - Parent contact
- Filter options:
  - By Status (Active/Expired/Cancelled)
  - By Batch
  - Search by name

#### 4.2 Filter by Batch
1. Look for batch filter dropdown at top
2. Select a batch (e.g., "Good Friends" or "Funny Bugs")

**Expected Result**:
- List updates to show only students in selected batch
- Count updates

#### 4.3 Filter by Status
1. Toggle between status filters:
   - Active
   - Expired
   - All

**Expected Result**:
- List updates accordingly
- Currently all 115 are marked as "Expired" (can be updated)

#### 4.4 View Student Profile
1. Click on any enrolled student from the list
2. Navigate to student detail page

**Expected Result**:
- Student profile page opens at `/students/[id]`
- See comprehensive student information:

**Profile Tab**:
- Child Details:
  - Full name
  - Age (calculated from DOB)
  - Date of birth
  - School
  - Interests
- Parent Details:
  - Parent name(s)
  - Phone number(s)
  - Email(s)
  - Relationship type

**Enrollment Tab**:
- Enrollment Details:
  - Plan type
  - Start date / End date
  - Batch assignment
  - Days selected
  - Visits: Used / Included / Remaining
  - Status badge
- Payment Details:
  - Total amount
  - Paid amount
  - Discount (if any)
  - Balance
  - Payment method

**Attendance Tab**:
- Attendance history
- Total classes attended
- Attendance percentage
- Recent attendance records with dates

**Progress Tab**:
- Skill progress tracking
- 16 Gymnastics skills:
  - Cartwheel
  - Handstand
  - Forward Roll
  - Backward Roll
  - Beam Mounts
  - Locomotor Skills
  - Balance on Beam
  - Jumps on Beam
  - Turns on Beam
  - High Beams
  - Beam Dismounts
  - Bar Mounts
  - Hangs on Bar
  - Bar Skills
  - Bar Dismounts
  - Vaulting
- Each skill shows level:
  - Not Started (gray)
  - In Progress (yellow)
  - Achieved (green)
  - Mastered (blue)

#### 4.5 Add New Enrollment
1. From enrollments page, click "+ New Enrollment" or "Enroll Student"
2. Fill in enrollment form:

**Step 1: Student Selection**
- Option A: Select existing child from dropdown
- Option B: Create new child:
  - First Name (required)
  - Last Name
  - Date of Birth
  - School
  - Interests

**Step 2: Parent Information**
- If new child:
  - Parent Name (required)
  - Phone (required)
  - Email (optional)
  - Relationship (mother/father/guardian)
- If existing child: Parents auto-populated

**Step 3: Enrollment Details**
- Batch: Select from dropdown (10 batches available)
- Plan Type: Select (Custom/Monthly/Quarterly/etc.)
- Start Date (required)
- End Date (for date-based plans)
- Visits Included (for visit-based plans)
- Days Selected: Check boxes (Mon/Tue/Wed/etc.)
- Status: Active/Paused
- Notes (optional)

**Step 4: Payment**
- Amount (required)
- Payment Method: Cash/UPI/Card/Bank Transfer
- Payment Date
- Discount: Type (% or Flat) and Amount
- Discount Reason
- Reference/Transaction ID

3. Click "Create Enrollment"

**Expected Result**:
- Enrollment created successfully
- Student appears in enrollments list
- Payment recorded
- If from lead: Lead status changes to "Enrolled"

#### 4.6 Mark Attendance

**Option A: From Student Profile**
1. Go to student detail page
2. Click "Attendance" tab
3. Click "Mark Attendance" button
4. Select date
5. Select status: Present/Absent/Makeup
6. Add notes (optional)
7. Save

**Expected Result**:
- Attendance marked
- Visits_used incremented (if present)
- Attendance appears in history
- Remaining visits decrements

**Option B: Batch Attendance**
1. From students/enrollments page
2. Click "Mark Attendance" at top
3. Select date
4. Select batch
5. See list of all students in that batch
6. Quick toggle Present/Absent for each
7. Click "Save Attendance"

**Expected Result**:
- Bulk attendance marked for entire batch
- All students updated
- Progress saved

---

### 5. Navigation Testing

#### 5.1 Dashboard Navigation
1. Click "Dashboard" in header/sidebar
2. Should return to main dashboard

#### 5.2 Center Switching (Super Admin Only)
1. Look for center dropdown in header (if Super Admin)
2. Select different center
3. Or click back arrow to return to center selection

**Expected Result**:
- Context switches to new center
- All data updates to show new center's information

#### 5.3 Module Links
Test all main navigation links:
- Dashboard
- Leads
- Students/Enrollments
- Attendance
- Progress/Report Cards
- Renewals
- Admin (if admin/super admin)
- MDM (Master Data Management - if super admin)

---

### 6. Batches (Class Groups)

Available Batches in Chandigarh:
1. **Giggle Worms** (Ages 1-2) - Tue/Thu, 10:00-11:00
2. **Funny Bugs** (Ages 2-3) - Mon/Wed/Fri, 10:00-11:00
3. **Good Friends** (Ages 3-4) - Mon/Wed/Fri, 11:00-12:00
4. **Super Beasts** (Ages 4-6) - Mon/Wed/Fri, 14:00-15:00
5. **Grade School** (Ages 6-12) - Sat/Sun, 09:00-10:00

---

### 7. Sample Test Data

**Lead with IV Scheduled**:
- Look for leads with "Intro Scheduled" status (64 available)
- These have intro visits with dates

**Enrolled Students**:
- All 115 enrollments currently marked as "Expired"
- Can update status to "Active" through edit function

**Students with Attendance**:
- 63 enrollments have attendance data (visits_used > 0)

---

## API Endpoints for Testing

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@thelittlegym.in", "password": "admin123"}'

# Get current user
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### Centers
```bash
# Get all centers
curl http://localhost:8000/api/v1/centers \
  -H "Authorization: Bearer <token>"

# Get Chandigarh center
curl http://localhost:8000/api/v1/centers/3 \
  -H "Authorization: Bearer <token>"
```

### Leads
```bash
# Get all Chandigarh leads
curl "http://localhost:8000/api/v1/leads?center_id=3" \
  -H "Authorization: Bearer <token>"

# Get leads by status
curl "http://localhost:8000/api/v1/leads?center_id=3&status=DISCOVERY" \
  -H "Authorization: Bearer <token>"
```

### Enrollments
```bash
# Get all enrolled students
curl "http://localhost:8000/api/v1/enrollments/students?center_id=3&status=ACTIVE" \
  -H "Authorization: Bearer <token>"

# Get batches
curl "http://localhost:8000/api/v1/enrollments/batches?center_id=3" \
  -H "Authorization: Bearer <token>"
```

---

## Known Issues / Notes

1. **Enrollment Status**: All 115 enrollments are currently marked as "EXPIRED" (from Excel import). You can update them to "ACTIVE" through the UI.

2. **Skill Progress**: Skill progress data structure is set up but may need to be re-imported or added manually through UI.

3. **Attendance Sessions**: Create class sessions first before marking batch attendance for specific dates.

4. **Center Admin Access**: Center admins can only see their assigned center, Super Admins see all.

---

## Success Criteria

✅ Login successful with super admin credentials
✅ Can view and select from 3 centers
✅ Chandigarh center shows correct data counts
✅ Lead Lifecycle module accessible
✅ Can view, filter, and search 300 leads
✅ Can create new leads
✅ Can schedule and mark intro visits
✅ Enrollments module accessible
✅ Can view 115 enrolled students
✅ Can filter by batch and status
✅ Student profile page loads with all tabs
✅ Shows enrollment, payment, and parent details
✅ Can mark attendance
✅ Can add new enrollments
✅ Navigation works between all modules

---

## Troubleshooting

### Frontend not loading
```bash
cd frontend
npm install
npm run dev
```

### Backend not responding
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Database connection issues
- Check .env file has correct Supabase URL
- Verify Supabase database is accessible

### Authentication failing
- Clear browser localStorage
- Re-login with credentials
- Check backend logs for errors

---

## Next Steps After Testing

1. Update expired enrollments to active status
2. Create class sessions for attendance marking
3. Add more skills progress data
4. Test report card generation
5. Test renewal notifications
6. Add more users (trainers, counselors)
7. Test role-based permissions

---

**Happy Testing!** 🎉

For issues or questions, check the backend logs at `backend/server.log` or frontend console.
