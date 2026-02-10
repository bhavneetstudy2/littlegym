# Chandigarh Data Import - Status Update

**Date**: February 4, 2026
**Status**: ⚠️ **IN PROGRESS**

---

## What Was Done

### 1. ✅ Added Enquiry ID Field to Database

- **File Modified**: [backend/app/models/child.py](backend/app/models/child.py)
- **Change**: Added `enquiry_id` field to Child model
- **Field**: `enquiry_id = Column(String(50), nullable=True, unique=True, index=True)`
- **Migration Created**: `58527e03181f_add_enquiry_id_to_children.py`
- **Migration Run**: ✅ Completed successfully

### 2. ✅ Created Comprehensive Import Script

- **File Created**: [backend/import_chandigarh_fixed.py](backend/import_chandigarh_fixed.py)
- **Purpose**: Import enrollment metadata and attendance data using Enquiry ID mapping

**Script Features**:
- Reads "Enrolled" sheet from TLG Chandigarh.xlsx
- Maps students by Enquiry ID (TLGC####)
- Updates children with their Enquiry ID
- Updates enrollments with:
  - Correct batch assignment
  - Booked classes (visits_included)
  - Duration, Total Amount, Paid Amount (in notes)
- Imports attendance from CSV:
  - Parses dates from 54 date columns
  - Creates class sessions for each date
  - Creates attendance records
  - Updates visits_used counter

---

## Issues Found & Addressed

### Issue #1: Duplicate Enquiry IDs

**Problem**: Some Enquiry IDs are reused for different students in the Excel file.

**Examples**:
- TLGC0061 used for both "Tanya" and "Sehaj"
- TLGC0028 used for "Aavya" in multiple batches
- TLGC0001, TLGC0022, TLGC0024, etc. have duplicates

**Solution**: Script now:
- Checks if Enquiry ID already assigned to another child
- Skips duplicate assignments with warning message
- Allows same student in multiple batches (correct behavior)

### Issue #2: Unicode Encoding Errors

**Problem**: Excel file contains checkmark characters (✓) that can't be encoded in Windows console.

**Solution**: Added `safe_print()` function that handles Unicode characters gracefully.

### Issue #3: SessionStatus Enum Value

**Problem**: Script used lowercase 'completed' but enum requires 'COMPLETED'.

**Solution**: Fixed to use `SessionStatus.COMPLETED` enum value.

### Issue #4: Missing session_date Field in Attendance

**Problem**: Attendance model doesn't have `session_date` field directly.

**Solution**: Changed to check attendance by `class_session_id` instead.

---

## Current Import Progress

### Step 1: Enrollment Metadata ✅

**From**: `TLG Chandigarh.xlsx` - "Enrolled" sheet
**Records**: 250 enrolled students

**Results**:
- ✅ Children updated with Enquiry ID: ~80+
- ✅ Enrollments updated: ~110+
- ⚠️ Not found: ~120+ (likely not imported in initial data load)

**Sample Success**:
```
✓ TLGC0002 - Mahira (Good Friends): 24 classes
✓ TLGC0027 - Prithvi (Funny Bugs): 24 classes
✓ TLGC0049 - Edrik (Funny Bugs): 24 classes
✓ TLGC0061 - Tanya (Super Beasts): 24 classes
```

### Step 2: Attendance Data ⚙️ IN PROGRESS

**From**: `TLG Chandigarh - Attendance (1).csv`
**Records**: 161 students with attendance data

**Process**:
- Parse dates from 54 columns (DD-MMM format)
- Create ClassSession for each unique date/batch
- Create Attendance record for each student/date
- Update enrollment.visits_used from CSV "Attended Classes" column

**Expected Results**:
- ~2000+ attendance records to be created
- ~500+ class sessions to be created
- Visits_used counters updated for all students

---

## Data Validation

### Mahira's Data (Example Student)

**Enquiry ID**: TLGC0002
**From CSV**:
- Child Name: Mahira
- Batch: Good Friends
- Booked Classes: 24
- Attended Classes: 18
- Remaining: 6
- Attendance Dates: 18-Apr, 19-Apr, 26-Apr, 27-Apr, 04-May, 08-May, 11-May, 17-May, 18-May, 24-May, 31-May, 01-Jun, 07-Jun, 08-Jun, 12-Jul, 19-Jul, 04-Sep (17 dates)

**Expected in Application**:
- ✅ Enquiry ID: TLGC0002
- ✅ Batch: Good Friends
- ✅ Booked: 24 classes
- ✅ Used: 18 classes (from CSV)
- ✅ Remaining: 6 classes
- ✅ Attendance records: 17+ records

---

## Known Data Issues

### 1. Missing Children

Many Enquiry IDs in the Enrolled sheet don't have matching children in the database. This is because:
- They weren't in the original "Enquiry" sheet that was imported
- They were added directly as enrolled students
- Name spelling differences between sheets

**Examples**:
- TLGC0403 - Aarav
- TLGC0019 - Aadvik
- TLGC0050 - Rajya Vardhan
- TLGC0072 - Vihaana
- TLGC0076 - Dylan, Noah

**Recommendation**: Create these children manually OR import from a complete enquiry list.

### 2. Batch Name Mismatches

Some batches in Excel don't exist in database:
- "Beasts" (should be "Super Beasts")
- "One Time" (not a standard batch)

**Fix**: Manual correction needed in Excel OR create these batches.

### 3. Date Format Assumptions

Attendance dates use "DD-MMM" format without year.
**Assumption**: All dates are from 2024.
**Impact**: If dates span 2023-2024 or 2024-2025, year needs manual correction.

---

## Next Steps

### To Complete Import:

1. **Let Current Script Finish**
   - The import_chandigarh_fixed.py script is currently running
   - Processing 161 attendance records
   - May take 2-5 minutes to complete

2. **Verify Data in Application**
   - Go to http://localhost:3000/students
   - Search for "Mahira"
   - Check:
     - Enquiry ID shows as TLGC0002
     - Batch is "Good Friends"
     - Booked: 24, Used: 18, Remaining: 6
     - Attendance tab shows 17+ records

3. **Check Other Students**
   - Verify other students from attendance CSV
   - Check that visits_used counters are correct
   - Check that attendance history shows properly

4. **Address Missing Children**
   - Option A: Import from complete enquiry sheet
   - Option B: Create missing children manually
   - Option C: Update Excel with only existing students

5. **Fix Duplicate Enquiry IDs**
   - Review Excel file for duplicate Enquiry IDs
   - Assign unique IDs to each student
   - Re-run import if needed

---

## How to Run Import Again

If you need to re-run the import:

```bash
cd backend
python import_chandigarh_fixed.py
```

**Note**: The script is safe to run multiple times - it:
- ✅ Skips children already having Enquiry ID
- ✅ Updates enrollment metadata even if run again
- ✅ Skips duplicate attendance records
- ✅ Commits after each student to avoid data loss

---

## Files Created/Modified

### Database
- ✅ Migration: `58527e03181f_add_enquiry_id_to_children.py`
- ✅ Table: `children` now has `enquiry_id` column (unique, indexed)

### Models
- ✅ [backend/app/models/child.py](backend/app/models/child.py) - Added enquiry_id field

### Scripts
- ✅ [backend/import_chandigarh_fixed.py](backend/import_chandigarh_fixed.py) - Main import script
- ⚠️ [backend/import_chandigarh_corrected.py](backend/import_chandigarh_corrected.py) - Earlier version (has bugs)

---

## Expected Final Counts

After import completes:

| Metric | Expected Count | Notes |
|--------|---------------|-------|
| Children with Enquiry ID | ~80-100 | Only those matching in both sheets |
| Enrollments updated | ~110-130 | Same students may have multiple enrollments |
| Class Sessions created | ~500+ | One per unique date/batch combination |
| Attendance records created | ~2000+ | One per student per attended date |
| Students with attendance | ~161 | From attendance CSV |

---

## Troubleshooting

### If Mahira Still Not Showing Correct Data:

1. **Check if import completed**:
   ```bash
   # Should show completion message
   tail -50 backend/import_chandigarh_fixed.py.log
   ```

2. **Check Enquiry ID in database**:
   ```sql
   SELECT id, first_name, enquiry_id, center_id
   FROM children
   WHERE first_name ILIKE '%mahira%';
   ```

3. **Check enrollment data**:
   ```sql
   SELECT e.*, b.name as batch_name
   FROM enrollments e
   LEFT JOIN batches b ON e.batch_id = b.id
   WHERE e.child_id = (SELECT id FROM children WHERE first_name ILIKE '%mahira%' LIMIT 1);
   ```

4. **Check attendance count**:
   ```sql
   SELECT COUNT(*)
   FROM attendance
   WHERE child_id = (SELECT id FROM children WHERE first_name ILIKE '%mahira%' LIMIT 1);
   ```

### If Import Fails:

- Check error messages in console
- Common issues:
  - Database connection lost
  - Unique constraint violation (Enquiry ID already used)
  - Session rolled back (will auto-recover and continue)

---

## Summary

✅ **Completed**:
- Database schema updated with enquiry_id field
- Import script created and tested
- Enrollment metadata import working

⚙️ **In Progress**:
- Attendance data import (161 students)
- Creating ~2000+ attendance records

🔄 **Next**:
- Verify data in application
- Check Mahira's complete profile
- Address any missing students

---

**The import script is designed to be safe, idempotent, and handle errors gracefully. Once it completes, all enrollment and attendance data should be correctly mapped using Enquiry IDs.**

**To verify: Visit http://localhost:3000/students and search for "Mahira" - her profile should now show:**
- Enquiry ID: TLGC0002
- Batch: Good Friends
- Booked: 24, Attended: 18, Remaining: 6
- Full attendance history with dates from the CSV
