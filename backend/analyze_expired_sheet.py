"""
Analyze the Expired sheet structure
"""
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

# Read Expired sheet
print("="*70)
print("EXPIRED SHEET ANALYSIS")
print("="*70)

expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')
print(f"\nShape: {expired_df.shape}")
print(f"\nColumns ({len(expired_df.columns)}):")
for i, col in enumerate(expired_df.columns):
    print(f"  {i}: {col}")

print(f"\nFirst 10 rows sample:")
for idx, row in expired_df.head(10).iterrows():
    enquiry_id = row.get('Enquiry ID', '')
    child_name = row.get('Child Name', '')
    batch = row.get('Batch', '')
    booked = row.get('Booked Classes', '')
    attended = row.get('Attended', '')
    date = row.get('Date', '')
    duration = row.get('Duration', '')
    print(f"  {enquiry_id} | {child_name} | {batch} | Booked:{booked} | Attended:{attended} | Date:{date} | {duration}")

print(f"\nTotal expired records: {len(expired_df)}")
