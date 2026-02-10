"""
Check column names in Enquiry sheet
"""
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

enquiry_df = pd.read_excel(EXCEL_FILE, sheet_name='Enquiry')

print("Columns in Enquiry sheet:")
for i, col in enumerate(enquiry_df.columns):
    print(f"  {i}: '{col}'")

print(f"\nFirst few rows:")
print(enquiry_df.head(3).to_string())
