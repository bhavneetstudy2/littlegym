"""
Verify Shahbaz data in CSV files
"""
import pandas as pd
import csv

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'
ATTENDANCE_CSV = r'C:\Users\Administrator\Downloads\TLG Chandigarh - Attendance (1).csv'

# Check Excel Enrolled sheet for Shahbaz
print('Excel Enrolled - Shahbaz records:')
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
shahbaz_rows = enrolled_df[enrolled_df['Child Name'].str.lower().str.contains('shahbaz', na=False)]
for _, row in shahbaz_rows.iterrows():
    print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')} | Booked: {row.get('Booked Classes')} | Paid: {row.get('Paid Amount')}")

# Check Attendance CSV for Shahbaz
print('\nAttendance CSV - Shahbaz records:')
with open(ATTENDANCE_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('Child Name', '').strip().lower()
        if 'shahbaz' in name:
            dates = []
            for i in range(1, 55):
                d = row.get(str(i), '').strip()
                if d:
                    dates.append(d)
            print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')} | Total dates: {len(dates)}")
            print(f"    Dates: {', '.join(dates[:10])}...")
