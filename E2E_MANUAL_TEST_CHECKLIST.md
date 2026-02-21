# Little Gym CRM - Complete E2E Manual Testing Checklist

## Pre-requisites
- ✅ Backend running on http://localhost:8001
- ✅ Frontend running on http://localhost:3001
- ✅ Logged in as Center Admin or Super Admin
- ✅ At least one center exists
- ✅ At least one batch exists
- ✅ At least one curriculum with activities exists

---

## Complete Workflow Test: Enquiry → Enrollment → Attendance → Progress

### Test Scenario
**Goal**: Create a new lead, convert to enrollment, mark attendance, and track progress

**Test Data**:
- Child Name: Aarav Sharma
- Age/DOB: 5 years / 2021-02-15
- Parent: Rahul Sharma
- Phone: 9876543210
- Source: Walk-in

---

## STEP 1: Create Enquiry (Discovery Form)

**Page**: `/leads`

1. Click **"+ New Enquiry"** button
2. Fill in the discovery form:
   - **Child First Name**: Aarav
   - **Child Last Name**: Sharma
   - **Date of Birth**: 2021-02-15
   - **Age**: 5 years
   - **Gender**: Boy
   - **School**: Little Flowers School
   - **Parent Name**: Rahul Sharma
   - **Contact Number**: 9876543210
   - **Email**: rahul.sharma@example.com
   - **Source**: Walk-in
   - **Parent Expectations**: Select 2-3 options
   - **Preferred Schedule**: "Mon/Wed/Fri evenings"
   - **Remarks**: "Interested in gymnastics program"
3. Click **"Submit"**

**Expected Results**:
- ✅ Success message appears
- ✅ New lead appears in the leads list
- ✅ Lead status = "ENQUIRY_RECEIVED"
- ✅ Lead has an Enquiry ID (e.g., TLGC0001)
- ✅ Status count updates in filter cards

**Verify**:
- [ ] Lead created successfully
- [ ] All entered data is visible
- [ ] Enquiry ID is generated
- [ ] Status counts are correct and don't go to zero when filtering

---

## STEP 2: Schedule Intro Visit

**Page**: `/leads` (click on the lead you just created)

1. In the lead detail modal, click **"Schedule Intro Visit"**
2. Fill in the intro visit form:
   - **Scheduled Date & Time**: Tomorrow at 4:00 PM
   - **Batch**: Select an available batch (e.g., "Birds - Age 3-6")
   - **Trainer** (optional): Select if available
   - **Notes**: "Trial class scheduled"
3. Click **"Schedule"**

**Expected Results**:
- ✅ Success message appears
- ✅ Lead status changes to "IV_SCHEDULED"
- ✅ Intro visit appears in lead details
- ✅ Status counts update

**Verify**:
- [ ] Intro visit scheduled successfully
- [ ] Lead status updated to IV_SCHEDULED
- [ ] Date and batch saved correctly
- [ ] Can see intro visit in lead timeline/activity

---

## STEP 3: Mark Intro Visit as Attended

**Page**: `/leads` → Lead Details Modal

1. Open the lead you created
2. Find the scheduled intro visit
3. Click **"Update IV"** or **"Mark Attended"**
4. Fill in:
   - **Attended At**: Today's date/time
   - **Outcome**: "Interested - Enroll Now"
   - **Notes**: "Child loved the class! Parents ready to enroll."
5. Click **"Submit"**

**Expected Results**:
- ✅ Lead status changes to "IV_COMPLETED"
- ✅ Intro visit shows "Attended" status
- ✅ Outcome is saved
- ✅ Status counts update

**Verify**:
- [ ] IV marked as attended
- [ ] Lead status updated to IV_COMPLETED
- [ ] Outcome saved correctly
- [ ] Timeline shows IV completion

---

## STEP 4: Create Follow-up (Optional)

**Page**: `/leads` → Lead Details Modal

1. In lead details, click **"Create Follow-up"**
2. Fill in:
   - **Scheduled Date**: Tomorrow
   - **Notes**: "Call to discuss payment options and enrollment details"
   - **Assigned To** (optional): Select user
3. Click **"Create"**

**Expected Results**:
- ✅ Follow-up created
- ✅ Lead status may change to "FOLLOW_UP_PENDING"
- ✅ Follow-up visible in lead details

**Verify**:
- [ ] Follow-up created
- [ ] Scheduled date correct
- [ ] Shows in lead activity log

---

## STEP 5: Convert to Enrollment

**Page**: `/leads` → Lead Details Modal OR Quick Action

### Method 1: From Lead Details
1. Click **"Convert to Enrollment"** button
2. Fill in enrollment form:
   - **Child**: Auto-selected (Aarav Sharma)
   - **Plan Type**: Monthly
   - **Start Date**: Today
   - **End Date**: 3 months from today
   - **Batch**: Select batch
   - **Days Selected**: Mon, Wed, Fri
   - **Payment Amount**: 5000
   - **Payment Method**: UPI
   - **Payment Reference**: UPI20260221001
   - **Discount Type**: Percent
   - **Discount Value**: 10
   - **Discount Reason**: Early bird discount
   - **Notes**: "Enrolled after successful IV"
3. Click **"Enroll"**

### Method 2: Quick Action
1. In leads list, click **"Enrolled"** quick action button on the lead
2. Fill in the same form as above

**Expected Results**:
- ✅ Enrollment created
- ✅ Lead status changes to "CONVERTED"
- ✅ Lead links to enrollment_id
- ✅ Enrollment appears in `/enrollments` page
- ✅ Payment record created
- ✅ Discount applied correctly
- ✅ Net amount = 4500 (5000 - 10%)
- ✅ Status counts update

**Verify**:
- [ ] Enrollment created successfully
- [ ] Lead status = CONVERTED
- [ ] Payment amount correct (₹4500 after discount)
- [ ] Enrollment shows in enrollments page
- [ ] All enrollment details saved
- [ ] Child now appears in students list

---

## STEP 6: Mark Attendance

**Page**: `/attendance`

1. Select the batch where child is enrolled
2. Ensure today's date is selected
3. Find "Aarav Sharma" in the student list
4. Click **"Present"** button or toggle attendance
5. Add optional notes: "First class - did great!"
6. Click **"Save"** or **"Quick Save"**

**Expected Results**:
- ✅ Attendance marked successfully
- ✅ Shows "Present" status for Aarav
- ✅ Attendance count updates
- ✅ For visit-based plans: visits_used increments

**Verify**:
- [ ] Attendance saved successfully
- [ ] Status shows as "Present"
- [ ] Date is correct
- [ ] Notes saved (if entered)
- [ ] Visit count updated (for pay-per-visit plans)
- [ ] Attendance visible in child's profile

---

## STEP 7: Update Progress Tracker

**Page**: `/progress`

1. Select center (if super admin)
2. Select or search for "Aarav Sharma"
3. Select **Week 1** (or current week)
4. For each activity/skill:
   - **For LEVEL-based skills** (e.g., Cartwheel):
     - Select level: "In Progress" or "Achieved"
     - Add notes: "Showing good form, needs practice"
   - **For COUNT-based skills** (e.g., Push-ups):
     - Enter number: 5 reps
     - Add notes: "Good effort for first week"
   - **For TIME-based skills** (e.g., Plank):
     - Enter time: 15 seconds
     - Add notes: "Improving stability"
5. Add **Trainer Notes** (optional):
   - Parent expectations: "Want child to build strength"
   - Progress check: "Great first week!"
6. Click **"Save Progress"**

**Expected Results**:
- ✅ All progress data saved
- ✅ Success message appears
- ✅ Can view saved progress by switching weeks
- ✅ Trainer notes saved
- ✅ Progress visible in child's profile

**Verify**:
- [ ] All activity values saved correctly
- [ ] Notes saved for each activity
- [ ] Trainer notes saved
- [ ] Can navigate between weeks
- [ ] Progress data persists after page refresh
- [ ] Different measurement types work (LEVEL, COUNT, TIME)

---

## STEP 8: Generate Report Card

**Page**: `/report-cards`

1. Click **"+ Generate Report Card"**
2. Select **Child**: Aarav Sharma
3. Select **Period**:
   - Start Date: 30 days ago
   - End Date: Today
4. Add **Summary Notes**: "Excellent first month! Aarav has shown great progress in basic gymnastics skills and has a very positive attitude in class."
5. Click **"Generate"**

**Expected Results**:
- ✅ Report card generated successfully
- ✅ Shows in report cards list
- ✅ Contains all skill progress from the period
- ✅ Summary notes included
- ✅ Can view/download the report card
- ✅ Shows child's progress across different skills
- ✅ Includes both weekly progress and skill-based data

**Verify**:
- [ ] Report card generated
- [ ] Child name and period correct
- [ ] All skills with progress shown
- [ ] Summary notes included
- [ ] Can view report card details
- [ ] Skills grouped by curriculum
- [ ] Shows both old SkillProgress and new WeeklyProgress data

---

## STEP 9: Verify Complete Workflow

### Check Lead Details
**Page**: `/leads` → Click on Aarav's lead

**Verify**:
- [ ] Status = "CONVERTED"
- [ ] Shows complete timeline:
  - [x] Enquiry created
  - [x] Intro visit scheduled
  - [x] Intro visit attended
  - [x] Follow-up created (if you created one)
  - [x] Converted to enrollment
- [ ] Linked to enrollment (can click to view)
- [ ] All activity logs present

### Check Enrollment
**Page**: `/enrollments` → Find Aarav

**Verify**:
- [ ] Status = "ACTIVE"
- [ ] Plan type correct (Monthly)
- [ ] Start and end dates correct
- [ ] Batch assignment correct
- [ ] Days selected correct (Mon, Wed, Fri)
- [ ] Payment amount: ₹4500 (after 10% discount)
- [ ] Payment method: UPI
- [ ] Can see payment history
- [ ] Can see discount details

### Check Attendance History
**Page**: `/attendance` or Child Profile

**Verify**:
- [ ] Today's attendance marked as "Present"
- [ ] Notes visible
- [ ] Attendance count correct
- [ ] History shows all attendance records

### Check Progress History
**Page**: `/progress` → Select Aarav → View different weeks

**Verify**:
- [ ] Week 1 progress saved
- [ ] All activity values correct
- [ ] Trainer notes present
- [ ] Can navigate between weeks
- [ ] Progress chart/summary shows (if implemented)

### Check Report Card
**Page**: `/report-cards` → View Aarav's report

**Verify**:
- [ ] Report card accessible
- [ ] Shows progress for the period
- [ ] Skills organized by curriculum
- [ ] Summary notes displayed
- [ ] Contains both WeeklyProgress and SkillProgress data
- [ ] Can print/export (if implemented)

---

## STEP 10: Test Table Sorting & Filtering

### Test Leads Table
**Page**: `/leads`

1. Click on **column headers** to sort:
   - Click "Child Name" → should sort alphabetically
   - Click again → should reverse sort
   - Click "Created" date → should sort by date
   - Verify sort indicators (up/down arrows)

2. Test **search functionality**:
   - Search for "Aarav" → should show only matching leads
   - Search for phone "9876543210" → should find the lead
   - Clear search → all leads show again

3. Test **status filters**:
   - Click on different status cards
   - Verify leads filter by status
   - **IMPORTANT**: Check that status counts **don't go to zero**
   - Counts should show total for each status, not filtered counts

**Verify**:
- [ ] Column sorting works on all sortable columns
- [ ] Sort direction indicators visible
- [ ] Search filters correctly
- [ ] Status filter works
- [ ] **Status counts remain visible when filtering (key fix!)**
- [ ] Pagination works (if you have > 50 leads)

---

## STEP 11: Test Data Integrity

### Cross-page Verification

1. **From Leads** → Open Aarav's lead
   - Click on enrollment link
   - Should navigate to enrollment details
   - All data should match

2. **From Enrollments** → Find Aarav
   - Click to view details
   - Check that child, parent, batch info matches
   - Payment details should match what you entered

3. **From Attendance** → View Aarav's attendance history
   - Should show today's "Present" entry
   - Notes should match

4. **From Progress** → View Aarav's progress
   - Should show Week 1 data
   - All values should match what you entered

5. **From Report Cards** → Open Aarav's report
   - Should include progress from Week 1
   - Summary should match

**Verify**:
- [ ] Data consistent across all pages
- [ ] No data loss when navigating
- [ ] Updates reflect immediately everywhere
- [ ] Relationships maintained (lead → enrollment → attendance → progress)

---

## STEP 12: Test Error Handling

### Test Validation

1. **Try creating invalid enquiry**:
   - Missing required fields
   - Invalid phone format
   - Should show validation errors

2. **Try creating duplicate enrollment**:
   - For same child/period
   - Should handle gracefully

3. **Try marking attendance without enrollment**:
   - Should warn or prevent

4. **Try updating progress without enrollment**:
   - Should warn or prevent

**Verify**:
- [ ] Validation errors shown clearly
- [ ] No crashes or silent failures
- [ ] Error messages helpful
- [ ] Can recover from errors

---

## Test Results Summary

### ✅ Passed Tests (check all that work):
- [ ] Create Enquiry with Discovery Form
- [ ] Schedule Intro Visit
- [ ] Mark Intro Visit Attended
- [ ] Create Follow-up (optional)
- [ ] Convert to Enrollment
- [ ] Mark Attendance
- [ ] Update Progress Tracker
- [ ] Generate Report Card
- [ ] Table Sorting Works
- [ ] Table Searching Works
- [ ] **Status Counts Don't Go to Zero**
- [ ] Data Integrity Across Pages
- [ ] Validation & Error Handling

### ❌ Issues Found:
_List any issues you encounter here_

1.
2.
3.

---

## Quick Checklist Version

**5-Minute Smoke Test**:
1. [ ] Create enquiry → Success
2. [ ] Schedule IV → Status updates
3. [ ] Mark IV attended → Status updates
4. [ ] Convert to enrollment → Lead becomes CONVERTED
5. [ ] Mark attendance → Shows Present
6. [ ] Update progress → Saves correctly
7. [ ] Generate report → Shows data
8. [ ] Sort tables → Works with indicators
9. [ ] **Filter leads → Counts stay visible** ← KEY TEST!
10. [ ] Search leads → Filters correctly

**If all 10 pass → System is working correctly!** ✅

---

## Notes

- **Most Important Test**: Verify that when you click a status filter on the leads page, the count numbers on other status cards **do not go to zero**. They should always show the total count for each status.

- **Sorting Test**: Click column headers and verify the up/down arrow indicators appear and data sorts correctly.

- **Search Test**: Type in the search box and verify it filters across child name, parent name, and phone number.

- **Data Flow**: The complete flow is:
  ```
  Enquiry → Intro Visit → Follow-up → Enrollment → Attendance → Progress → Report Card
  ```

- All steps should maintain data integrity and relationships throughout.
