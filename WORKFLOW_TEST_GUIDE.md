# Complete Workflow Test Guide

## Server Status
- **Backend API**: http://127.0.0.1:8000
- **Frontend App**: http://localhost:3002
- **API Docs**: http://127.0.0.1:8000/docs

## Test Credentials

### Super Admin
- **Email**: admin@thelittlegym.in
- **Password**: admin123
- **Access**: All centers, all features

### Chandigarh Center Admin
- **Email**: admin.chd@thelittlegym.in
- **Password**: password123
- **Access**: Chandigarh center only

## Test Workflow: Super Admin Journey

### Step 1: Login as Super Admin
1. Open http://localhost:3002/login
2. Enter credentials:
   - Email: `admin@thelittlegym.in`
   - Password: `admin123`
3. Click "Login"
4. **Expected**: Redirect to `/dashboard`

### Step 2: View Centers List
1. Click "Centers" in the sidebar (first menu item, building icon)
2. **Expected**: See centers grid with:
   - The Little Gym Mumbai Central (MUM)
   - The Little Gym Chandigarh (CHD)
   - The Little Gym Pune (PUN) - if exists
3. Hover over "The Little Gym Chandigarh" card
4. **Expected**: Stats should load showing:
   - Total Leads: 5
   - Active Enrollments: 0
   - Batches: 5
   - Users: 1

### Step 3: Click and View Chandigarh Center
1. Click on "The Little Gym Chandigarh" card
2. **Expected**: Navigate to `/centers/3` (center detail page)
3. **Expected**: See:
   - Center name: "The Little Gym Chandigarh"
   - Code: CHD
   - Status: Active (green badge)
   - Location: Chandigarh, Punjab
   - Address: SCO 123, Sector 17, Chandigarh
   - Phone: +91-172-1234567
   - Email: chandigarh@thelittlegym.in
4. **Expected**: Stats cards showing:
   - Total Leads: 5
   - Active Enrollments: 0 of 0 total
   - Batches: 5
   - Users: 1

### Step 4: Enter Center Context
1. Click "Enter Center" button (top right, blue button)
2. **Expected**: Redirect to `/dashboard`
3. **Expected**: Blue context bar appears at top showing:
   - "📍 Viewing: The Little Gym Chandigarh (Chandigarh)"
   - Dropdown to switch centers
   - "Exit" button

### Step 5: View Chandigarh Leads
1. Click "Leads" in sidebar
2. **Expected**: See 5 demo leads:
   - **Aarav Sharma** - Status: DISCOVERY
   - **Ananya Patel** - Status: INTRO_SCHEDULED
   - **Arjun Singh** - Status: FOLLOW_UP
   - **Diya Kapoor** - Status: DISCOVERY
   - **Ishaan Mehta** - Status: INTRO_ATTENDED
3. **Expected**: Each lead should show:
   - Child name
   - Parent name and phone
   - Source (Walk-in, Instagram, Referral, Facebook, Google)
   - Current status
   - Action buttons

### Step 6: View Master Data - Class Types
1. Click "Master Data" in sidebar
2. **Expected**: See MDM landing page with two sections:
   - **Global Master Data** (Super Admin Only) - purple badge
     - Class Types card
     - Curricula card
     - Skills card
   - **Center Master Data** (The Little Gym Chandigarh)
     - Batches card
     - Users card
3. Click "Class Types" card
4. **Expected**: See 8 global class types:
   - Giggle Worms (0-1 years, 45 mins)
   - Funny Bugs (1-2 years, 45 mins)
   - Birds (2-3 years, 45 mins)
   - Bugs (3-4 years, 45 mins)
   - Beasts (4-6 years, 60 mins)
   - Super Beasts (6-9 years, 60 mins)
   - Good Friends (3-5 years, 45 mins)
   - Grade School (6-12 years, 60 mins)
5. Try clicking "+ Add Class Type" button
6. **Expected**: Drawer opens from right with form fields:
   - Class Type Name
   - Description
   - Min Age / Max Age
   - Duration (minutes)
   - Active checkbox
7. Close drawer (ESC or Cancel button)

### Step 7: Test Lead Lifecycle
1. Go back to Leads page (click "Leads" in sidebar)
2. Click on "Aarav Sharma" (DISCOVERY status)
3. **Expected**: Lead detail view opens
4. Click "Schedule Intro Visit" button
5. **Expected**: Drawer opens with form:
   - Batch selector (should show 5 Chandigarh batches)
   - Date/Time picker
6. Try selecting a past date
7. **Expected**: Form validation error: "Cannot schedule a visit in the past"
8. Select future date (e.g., tomorrow)
9. Select batch: "Giggle Worms Morning" (appropriate for age 0-1)
10. Click "Schedule"
11. **Expected**: Lead status changes to INTRO_SCHEDULED
12. **Expected**: Success message appears

### Step 8: View Chandigarh Batches
1. Navigate to Master Data → Batches (or Enrollments page)
2. **Expected**: See 5 batches created for Chandigarh:
   - **Giggle Worms Morning** - Mon/Wed, 10:00-10:45, Age 0-1, Capacity 8
   - **Birds MWF Batch** - Mon/Wed/Fri, 11:00-11:45, Age 2-3, Capacity 12
   - **Bugs Afternoon** - Mon/Wed/Fri, 15:00-15:45, Age 3-4, Capacity 12
   - **Beasts Evening** - Tue/Thu/Sat, 16:00-17:00, Age 4-6, Capacity 12
   - **Super Beasts Advanced** - Tue/Thu/Sat, 17:15-18:15, Age 6-9, Capacity 12

### Step 9: Switch Centers
1. In the blue context bar at top, click the dropdown
2. **Expected**: See all centers in dropdown
3. Select "The Little Gym Mumbai Central"
4. **Expected**:
   - Context bar updates to show Mumbai Central
   - Leads page now shows Mumbai Central's leads (518 imported leads)
   - Batches show Mumbai Central's batches (8 batches)
5. Switch back to Chandigarh

### Step 10: Exit Center Context
1. Click "Exit" button in context bar
2. **Expected**: Navigate back to `/centers` page
3. **Expected**: Context bar disappears
4. **Expected**: Can select a different center or logout

## Test Workflow: Center Admin Journey

### Step 1: Logout and Login as Chandigarh Admin
1. Click "Logout" button in sidebar
2. Login with Chandigarh admin credentials:
   - Email: `admin.chd@thelittlegym.in`
   - Password: `password123`
3. **Expected**: Redirect to `/dashboard`
4. **Expected**: Context bar shows:
   - "📍 Your Center: The Little Gym Chandigarh"
   - NO dropdown (locked to Chandigarh only)
   - NO exit button (can't change centers)

### Step 2: Verify Permissions
1. Check sidebar menu
2. **Expected**: See:
   - Master Data (can access)
   - Dashboard
   - Leads
   - Enrollments
   - Attendance
   - Progress
   - Report Cards
   - Renewals
   - Admin
3. **Expected**: NOT see:
   - Centers (Super Admin only)

### Step 3: Verify Data Isolation
1. Click "Leads"
2. **Expected**: See only Chandigarh's 5 leads
3. **Expected**: Cannot see Mumbai Central's 518 leads
4. Try accessing `/centers` directly in browser
5. **Expected**: Either redirect or 403 Forbidden

### Step 4: Test Master Data Access
1. Click "Master Data" in sidebar
2. **Expected**: See:
   - Global Master Data section (read-only or hidden create buttons)
   - Center Master Data section (full access)
3. Click "Class Types"
4. **Expected**: Can view class types
5. Try clicking "+ Add Class Type"
6. **Expected**: Either:
   - Button hidden, OR
   - API returns 403 Forbidden error

## Expected Demo Data Summary

### The Little Gym Chandigarh (Center ID: 3)

#### Batches (5)
1. Giggle Worms Morning - Mon/Wed, 10:00-10:45
2. Birds MWF Batch - Mon/Wed/Fri, 11:00-11:45
3. Bugs Afternoon - Mon/Wed/Fri, 15:00-15:45
4. Beasts Evening - Tue/Thu/Sat, 16:00-17:00
5. Super Beasts Advanced - Tue/Thu/Sat, 17:15-18:15

#### Leads (5)
1. **Aarav Sharma** (Age ~4, M)
   - Parent: Rajesh Sharma (+91-98765-43210)
   - Source: Walk-in
   - Status: DISCOVERY
   - School: Little Buds Preschool

2. **Ananya Patel** (Age ~5, F)
   - Parent: Priya Patel (+91-98765-43211)
   - Source: Instagram
   - Status: INTRO_SCHEDULED
   - School: Sunshine Academy

3. **Arjun Singh** (Age ~6, M)
   - Parent: Amit Singh (+91-98765-43212)
   - Source: Referral
   - Status: FOLLOW_UP
   - School: Green Valley School

4. **Diya Kapoor** (Age ~4, F)
   - Parent: Neha Kapoor (+91-98765-43213)
   - Source: Facebook
   - Status: DISCOVERY
   - School: None

5. **Ishaan Mehta** (Age ~5, M)
   - Parent: Vikram Mehta (+91-98765-43214)
   - Source: Google
   - Status: INTRO_ATTENDED
   - School: Rainbow Kids

#### Users (1)
- **Chandigarh Admin**
  - Email: admin.chd@thelittlegym.in
  - Password: password123
  - Role: CENTER_ADMIN

### Global Master Data

#### Class Types (8)
1. Giggle Worms - Age 0-1, 45 min
2. Funny Bugs - Age 1-2, 45 min
3. Birds - Age 2-3, 45 min
4. Bugs - Age 3-4, 45 min
5. Beasts - Age 4-6, 60 min
6. Super Beasts - Age 6-9, 60 min
7. Good Friends - Age 3-5, 45 min
8. Grade School - Age 6-12, 60 min

#### Curricula (3)
1. **Gymnastics Foundation Level 1** (Age 3-6) - 7 skills
2. **Gymnastics Foundation Level 2** (Age 6-9) - 7 skills
3. **Basic Movements** (Age 0-3) - 7 skills

## Verification Checklist

- [ ] Super Admin can login successfully
- [ ] Centers list page loads with all centers
- [ ] Center stats load on hover
- [ ] Center detail page displays all information
- [ ] "Enter Center" button sets center context
- [ ] Context bar appears and shows correct center
- [ ] Leads page shows Chandigarh's 5 demo leads
- [ ] Master Data landing page displays both sections
- [ ] Class Types page shows all 8 types
- [ ] Can add/edit class types (Super Admin only)
- [ ] Lead detail opens and shows info
- [ ] Schedule Intro Visit form validates past dates
- [ ] Can schedule intro visit for future date
- [ ] Batch list shows all 5 Chandigarh batches
- [ ] Can switch between centers using dropdown
- [ ] Exit button returns to centers list
- [ ] Center Admin login works
- [ ] Center Admin sees only their center
- [ ] Center Admin cannot access /centers
- [ ] Data isolation works (can't see other centers' data)
- [ ] RBAC enforced (Super Admin features hidden for Center Admin)

## Known Issues / Future Enhancements

1. **Enrollment Creation**: Not yet implemented in UI (backend ready)
2. **Attendance Marking**: Page exists but needs integration
3. **Progress Tracking**: Skeleton pages created
4. **Report Cards**: Backend ready, UI pending
5. **Renewals Dashboard**: Backend ready, UI pending
6. **Search Functionality**: Needs to be added to Leads page
7. **Pagination**: Large datasets need pagination
8. **Filters**: Advanced filtering on leads/enrollments
9. **WhatsApp Integration**: Future phase
10. **Parent Portal**: Future phase

## Success Criteria

✅ **Multi-Center Support**: Super Admin can view and switch between centers
✅ **Center Context**: Blue bar shows selected center, persists across pages
✅ **RBAC**: Super Admin sees all features, Center Admin restricted to their center
✅ **Data Isolation**: Center Admin sees only their center's data
✅ **Master Data Management**: Global and center-specific data separated
✅ **Lead Management**: Can view leads, schedule intro visits with validation
✅ **Demo Data**: Chandigarh center has complete demo data for testing

## Next Steps

1. Test enrollment creation workflow
2. Implement attendance marking UI
3. Build progress tracking interface
4. Create report cards generator
5. Design renewals dashboard
6. Add search and filters
7. Implement pagination for large lists
8. Add data export functionality
9. Create user management interface
10. Build admin settings pages
