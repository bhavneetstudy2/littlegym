"""
Analyze the Tracker tab in the Excel file to understand structure
"""
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

# List all sheets
xl = pd.ExcelFile(EXCEL_FILE)
print("Available sheets:", xl.sheet_names)

# Read Tracker tab
print("\n" + "="*70)
print("TRACKER TAB ANALYSIS")
print("="*70)

try:
    tracker_df = pd.read_excel(EXCEL_FILE, sheet_name='Tracker')
    print(f"\nShape: {tracker_df.shape}")
    print(f"\nColumns ({len(tracker_df.columns)}):")
    for i, col in enumerate(tracker_df.columns):
        print(f"  {i}: {col}")

    print(f"\nFirst 5 rows:")
    print(tracker_df.head())

    print(f"\nSample data (first 3 rows, all columns):")
    for idx, row in tracker_df.head(3).iterrows():
        print(f"\nRow {idx}:")
        for col in tracker_df.columns:
            val = row[col]
            if pd.notna(val):
                print(f"  {col}: {val}")

except Exception as e:
    print(f"Error reading Tracker tab: {e}")

    # Try to find similar tab names
    for sheet in xl.sheet_names:
        if 'track' in sheet.lower() or 'skill' in sheet.lower() or 'progress' in sheet.lower():
            print(f"\nTrying sheet: {sheet}")
            try:
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                print(f"  Shape: {df.shape}")
                print(f"  Columns: {list(df.columns)[:10]}...")
            except:
                pass
