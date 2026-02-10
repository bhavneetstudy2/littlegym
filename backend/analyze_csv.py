import pandas as pd
import csv

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'

print("="*70)
print("EXCEL FILE - ENROLLED SHEET")
print("="*70)
df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
print(f"Columns: {list(df.columns)}")
print(f"Total rows: {len(df)}")
print("\nSample rows:")
for i, row in df.head(5).iterrows():
    print(f"\n  Row {i}:")
    for col in df.columns:
        val = row[col]
        if pd.notna(val):
            print(f"    {col}: {val}")

# Check for Abeer
print("\n" + "="*70)
print("ABEER entries in Enrolled sheet:")
print("="*70)
abeer_rows = df[df['Child Name'].str.contains('Abeer', case=False, na=False)]
for i, row in abeer_rows.iterrows():
    print(f"\n  Enquiry ID: {row.get('Enquiry ID')}")
    print(f"  Child Name: {row.get('Child Name')}")
    print(f"  Batch: {row.get('Batch')}")
    print(f"  Booked Classes: {row.get('Booked Classes')}")
    print(f"  Total Amount: {row.get('Total Amount')}")
    print(f"  Paid Amount: {row.get('Paid Amount')}")

print("\n" + "="*70)
print("ATTENDANCE CSV")
print("="*70)
with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f"Columns: {reader.fieldnames[:10]}...")  # First 10 columns
    print(f"Total rows: {len(rows)}")

# Check Abeer in attendance
print("\nABEER entries in Attendance CSV:")
for row in rows:
    if 'abeer' in row.get('Child Name', '').lower():
        enquiry_id = row.get('Enquiry ID', '')
        child_name = row.get('Child Name', '')
        batch = row.get('Batch', '')
        attended = row.get('Attended Classes', '')
        # Count date columns
        dates = []
        for i in range(1, 55):
            d = row.get(str(i), '').strip()
            if d:
                dates.append(d)
        print(f"\n  Enquiry ID: {enquiry_id}")
        print(f"  Child Name: {child_name}")
        print(f"  Batch: {batch}")
        print(f"  Attended Classes: {attended}")
        print(f"  Dates found: {len(dates)} -> {dates[:5]}{'...' if len(dates) > 5 else ''}")
