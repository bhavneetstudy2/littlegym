"""
Analyze how much skill data is in the Tracker sheet
"""
import pandas as pd

EXCEL_FILE = r'C:\Users\Administrator\Downloads\TLG Chandigarh.xlsx'

tracker_df = pd.read_excel(EXCEL_FILE, sheet_name='Tracker')

skill_columns = [
    'Cartwheel', 'Handstand', 'Forward Roll', 'Backward Roll',
    'Locomotor Skills', 'Balance on Beam', 'Jumps on Beam', 'Turns on Beam',
    'High Beams', 'Beam Mounts', 'Beam Dismounts',
    'Bar Mounts', 'Hangs on Bar', 'Bar Skills', 'Bar Dismounts', 'Vaulting'
]

print(f"Total rows: {len(tracker_df)}")
print(f"Skill columns: {len(skill_columns)}")

# Count rows with at least one skill filled
rows_with_skills = 0
rows_with_all_empty = 0

for idx, row in tracker_df.iterrows():
    has_any_skill = False
    for col in skill_columns:
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            has_any_skill = True
            break
    if has_any_skill:
        rows_with_skills += 1
    else:
        rows_with_all_empty += 1

print(f"\nRows with at least one skill: {rows_with_skills}")
print(f"Rows with all skills empty: {rows_with_all_empty}")

# Show first 5 rows with skills
print("\nSample rows with skill data:")
count = 0
for idx, row in tracker_df.iterrows():
    has_any_skill = False
    for col in skill_columns:
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            has_any_skill = True
            break
    if has_any_skill:
        print(f"  {row.get('Enquiry ID')} | {row.get('Child Name')} | {row.get('Batch')}")
        count += 1
        if count >= 10:
            break
