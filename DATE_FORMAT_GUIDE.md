# Date Format Implementation Guide

## Overview
The Little Gym CRM now uses **dd/mm/yyyy** format for all date inputs, following the Indian standard date format.

---

## Date Format Standards

### Input Format (User Entry)
- **Format**: `dd/mm/yyyy`
- **Example**: `21/02/2026`
- **Component**: `DateInput`

### API Format (Backend Communication)
- **Format**: `yyyy-mm-dd` (ISO 8601)
- **Example**: `2026-02-21`
- **Note**: All API calls use ISO format internally

### Display Format (UI)
Two formats available:
1. **Short format**: `dd/mm/yyyy` (e.g., `21/02/2026`)
2. **Medium format**: `dd MMM yyyy` (e.g., `21 Feb 2026`)

---

## Components & Utilities

### 1. DateInput Component
Location: `frontend/src/components/ui/DateInput.tsx`

**Features**:
- Accepts user input in dd/mm/yyyy format
- Auto-adds slashes while typing
- Validates date format
- Supports min/max date constraints
- Returns ISO format (yyyy-mm-dd) for API
- Shows helpful format hint

**Usage**:
```tsx
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';

<DateInput
  label="Date of Birth"
  value={dobISO}  // yyyy-mm-dd format
  onChange={setDob}  // Receives yyyy-mm-dd format
  max={getTodayISO()}  // Cannot select future dates
  required
/>
```

### 2. Date Utility Functions
Location: `frontend/src/lib/utils.ts`

#### formatDateDDMMYYYY(dateStr)
Formats any date string to dd/mm/yyyy format.
```tsx
import { formatDateDDMMYYYY } from '@/lib/utils';

const formatted = formatDateDDMMYYYY('2026-02-21');
// Returns: "21/02/2026"
```

#### convertDDMMYYYYtoISO(ddmmyyyy)
Converts user input (dd/mm/yyyy) to API format (yyyy-mm-dd).
```tsx
import { convertDDMMYYYYtoISO } from '@/lib/utils';

const isoDate = convertDDMMYYYYtoISO('21/02/2026');
// Returns: "2026-02-21"
```

#### convertISOtoDDMMYYYY(isoDate)
Converts API format (yyyy-mm-dd) to display format (dd/mm/yyyy).
```tsx
import { convertISOtoDDMMYYYY } from '@/lib/utils';

const displayDate = convertISOtoDDMMYYYY('2026-02-21');
// Returns: "21/02/2026"
```

#### getTodayDDMMYYYY()
Get today's date in dd/mm/yyyy format.
```tsx
import { getTodayDDMMYYYY } from '@/lib/utils';

const today = getTodayDDMMYYYY();
// Returns: "21/02/2026"
```

#### getTodayISO()
Get today's date in yyyy-mm-dd format (for API calls or min/max constraints).
```tsx
import { getTodayISO } from '@/lib/utils';

const today = getTodayISO();
// Returns: "2026-02-21"
```

#### formatDate(dateStr) - Existing
Formats date in medium format (dd MMM yyyy).
```tsx
import { formatDate } from '@/lib/utils';

const formatted = formatDate('2026-02-21');
// Returns: "21 Feb 2026"
```

---

## Implementation Examples

### Example 1: Enquiry Form
File: `frontend/src/components/leads/EnquiryFormModal.tsx`

```tsx
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';

// In component
const [dob, setDob] = useState('');  // Stores yyyy-mm-dd format

// In form
<DateInput
  label="Date of Birth"
  value={dob}
  onChange={setDob}  // Will receive yyyy-mm-dd
  max={getTodayISO()}  // Cannot be in future
  placeholder="dd/mm/yyyy"
/>

// When submitting to API
await api.post('/api/v1/leads/enquiry', {
  child_dob: dob  // Already in yyyy-mm-dd format
});
```

### Example 2: Enrollment Modal
File: `frontend/src/components/leads/ConvertToEnrollmentModal.tsx`

```tsx
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';

const [startDate, setStartDate] = useState('');
const [endDate, setEndDate] = useState('');

<DateInput
  label="Start Date"
  value={startDate}
  onChange={setStartDate}
  min={getTodayISO()}  // Cannot be in past
  required
/>

<DateInput
  label="End Date"
  value={endDate}
  onChange={setEndDate}
  min={startDate || getTodayISO()}  // Must be after start date
  required
/>
```

### Example 3: Displaying Dates in Tables
```tsx
import { formatDateDDMMYYYY, formatDate } from '@/lib/utils';

// Short format (dd/mm/yyyy)
<td>{formatDateDDMMYYYY(lead.created_at)}</td>
// Output: 21/02/2026

// Medium format (dd MMM yyyy)
<td>{formatDate(lead.created_at)}</td>
// Output: 21 Feb 2026
```

---

## Updated Forms

The following forms now use the DateInput component with dd/mm/yyyy format:

1. **Enquiry Form** (`EnquiryFormModal.tsx`)
   - Child Date of Birth

2. **Convert to Enrollment** (`ConvertToEnrollmentModal.tsx`)
   - Enrollment Start Date
   - Enrollment End Date

3. **Other Date Inputs** (recommended to update):
   - Schedule Intro Visit
   - Follow-up scheduling
   - Report Card date range
   - Attendance date selection

---

## Migration Guide

### For Developers: Adding Date Input to New Forms

1. **Import the component and utilities**:
```tsx
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';
```

2. **Use ISO format in state** (yyyy-mm-dd):
```tsx
const [selectedDate, setSelectedDate] = useState('');
```

3. **Render DateInput**:
```tsx
<DateInput
  label="Select Date"
  value={selectedDate}  // yyyy-mm-dd
  onChange={setSelectedDate}  // Receives yyyy-mm-dd
  min={getTodayISO()}  // Optional: min constraint
  max={getTodayISO()}  // Optional: max constraint
  required
/>
```

4. **Send to API** (already in correct format):
```tsx
await api.post('/endpoint', {
  date: selectedDate  // yyyy-mm-dd format
});
```

5. **Display dates** (choose format):
```tsx
import { formatDateDDMMYYYY, formatDate } from '@/lib/utils';

// Short: 21/02/2026
{formatDateDDMMYYYY(apiResponse.date)}

// Medium: 21 Feb 2026
{formatDate(apiResponse.date)}
```

---

## User Experience

### Input Features
- **Auto-formatting**: Slashes are automatically added as user types
- **Validation**: Real-time validation with helpful error messages
- **Format hint**: Shows "Format: dd/mm/yyyy (e.g., 21/02/2026)" below input
- **Min/Max constraints**: Prevents invalid date selection
- **Clear errors**: Shows specific error messages for invalid dates

### Example User Flow
1. User clicks on "Date of Birth" field
2. Types: `21` → automatically becomes `21/`
3. Types: `02` → automatically becomes `21/02/`
4. Types: `2026` → final: `21/02/2026`
5. On blur: validates and shows error if invalid
6. On submit: converts to `2026-02-21` for API

---

## Testing

### Manual Testing Checklist
- [ ] Enter valid date: `21/02/2026` → Should accept
- [ ] Enter invalid format: `2026-02-21` → Should show error
- [ ] Enter future date when max is today → Should show error
- [ ] Auto-slash insertion works while typing
- [ ] Tab through form - date validation on blur
- [ ] Submit form - date sent in yyyy-mm-dd format
- [ ] View saved data - date displays in dd/mm/yyyy

### Test Cases
```tsx
// Valid inputs
"21/02/2026" → "2026-02-21" ✓
"01/01/2020" → "2020-01-01" ✓
"31/12/2025" → "2025-12-31" ✓

// Invalid inputs
"32/01/2026" → Error: Invalid date ✗
"21/13/2026" → Error: Invalid month ✗
"2026/02/21" → Error: Invalid format ✗
"abc/de/fghi" → Error: Invalid format ✗
```

---

## Summary

✅ **Input Format**: dd/mm/yyyy (Indian standard)
✅ **API Format**: yyyy-mm-dd (ISO 8601)
✅ **Display Format**: dd/mm/yyyy or dd MMM yyyy
✅ **Auto-formatting**: Slashes added automatically
✅ **Validation**: Real-time with helpful errors
✅ **Constraints**: Min/max date support
✅ **Backward Compatible**: Existing APIs unchanged

All date handling is centralized in utility functions and the DateInput component for consistency across the application.
