"""
Detailed analysis of Expired sheet
"""
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')

print("First 5 rows - all columns with values:")
for idx, row in expired_df.head(5).iterrows():
    print(f"\nRow {idx}:")
    for col in expired_df.columns:
        val = row[col]
        if pd.notna(val) and str(val).strip():
            print(f"  {col}: {val}")

# Check Booked/Availed/Balance columns
print("\n\nBooked/Availed/Balance values for first 20 rows:")
for idx, row in expired_df.head(20).iterrows():
    enquiry = row.get('Enquiry ID', '')
    name = row.get('Child Name', '')
    booked = row.get('Booked', '')
    availed = row.get('Availed', '')
    balance = row.get('Balance', '')
    print(f"  {enquiry} | {name} | B:{booked} | A:{availed} | Bal:{balance}")
