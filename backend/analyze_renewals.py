"""
Analyze renewal cases in Excel to understand proper enrollment structure
"""
import sys
sys.path.insert(0, '.')
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

print("="*70)
print("ANALYZING RENEWAL CASES")
print("="*70)

# Load Excel
enrolled_df = pd.read_excel(EXCEL_FILE, sheet_name='Enrolled')
expired_df = pd.read_excel(EXCEL_FILE, sheet_name='Expired')

# Find children who appear in both sheets (renewals)
enrolled_ids = set(enrolled_df['Enquiry ID'].dropna().unique())
expired_ids = set(expired_df['Enquiry ID'].dropna().unique())
renewal_ids = enrolled_ids.intersection(expired_ids)

print(f"\nFound {len(renewal_ids)} children with renewals (in both Enrolled and Expired)")

# Analyze a few examples
examples = ['TLGC0256', 'TLGC0043', 'TLGC0278']

for eid in examples:
    print(f"\n{'='*70}")
    print(f"Example: {eid}")

    # Get from Enrolled sheet
    enrolled_rows = enrolled_df[enrolled_df['Enquiry ID'] == eid]
    print(f"\nEnrolled sheet ({len(enrolled_rows)} records):")
    for idx, row in enrolled_rows.iterrows():
        print(f"  Batch: {row.get('Batch')}")
        print(f"    Booked: {row.get('Booked Classes')} | Duration: {row.get('Duration')}")
        print(f"    Date: {row.get('Date')} | Status: Active")

    # Get from Expired sheet
    expired_rows = expired_df[expired_df['Enquiry ID'] == eid]
    if not expired_rows.empty:
        print(f"\nExpired sheet ({len(expired_rows)} records):")
        for idx, row in expired_rows.iterrows():
            print(f"  Batch: {row.get('Batch')}")
            print(f"    Booked: {row.get('Booked')} | Availed: {row.get('Availed')}")
            print(f"    Status: Expired")

# Find children with multiple entries in Enrolled sheet
print(f"\n{'='*70}")
print("Children with multiple ACTIVE enrollments in same batch:")

enrolled_grouped = enrolled_df.groupby(['Enquiry ID', 'Batch']).size().reset_index(name='count')
multiple_enrolled = enrolled_grouped[enrolled_grouped['count'] > 1]

print(f"\nFound {len(multiple_enrolled)} cases")
for idx, row in multiple_enrolled.head(10).iterrows():
    eid = row['Enquiry ID']
    batch = row['Batch']
    count = row['count']

    print(f"\n{eid} | {batch} ({count} enrollments):")

    rows = enrolled_df[(enrolled_df['Enquiry ID'] == eid) & (enrolled_df['Batch'] == batch)]
    for i, r in rows.iterrows():
        print(f"  Booked: {r.get('Booked Classes')} | Date: {r.get('Date')} | Duration: {r.get('Duration')}")

print("\n" + "="*70)
