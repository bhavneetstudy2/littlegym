"""
Complete Chandigarh Data Import - Phase 2: Database Import
Import all 667 children + parents + leads to database
"""
import pandas as pd
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import re

# Configuration
TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"
EXCEL_FILE = r"C:\Users\Administrator\Downloads\TLG Chandigarh (1).xlsx"
CENTER_ID = 3  # Chandigarh

# Import the master_children from phase 1
exec(open('import_chandigarh_data.py').read())

print("\n" + "=" * 80)
print("PHASE 2: DATABASE IMPORT")
print("=" * 80)

# Connect to database
engine = create_engine(TARGET_DB)
Session = sessionmaker(bind=engine)
db = Session()

# Get admin user for created_by/updated_by
admin_user = db.execute(text("SELECT id FROM users WHERE center_id = :center_id AND role IN ('CENTER_ADMIN', 'SUPER_ADMIN') LIMIT 1"), {"center_id": CENTER_ID}).scalar()
if not admin_user:
    admin_user = db.execute(text("SELECT id FROM users WHERE role = 'SUPER_ADMIN' LIMIT 1")).scalar()

created_by_id = admin_user
print(f"\nUsing user_id {created_by_id} for created_by/updated_by")

# Step 2: Import Children, Parents, Family Links
print("\nStep 2: Importing Children, Parents, and Family Links...")
print("-" * 80)

child_id_map = {}
parent_id_map = {}

for idx, (enquiry_id, child_data) in enumerate(master_children.items(), 1):
    try:
        # Insert Child
        child_insert = text("""
            INSERT INTO children (center_id, first_name, last_name, dob, school, interests, notes, external_id, is_archived, created_by_id, updated_by_id, created_at, updated_at)
            VALUES (:center_id, :first_name, :last_name, :dob, :school, :interests, :notes, :external_id, FALSE, :created_by_id, :updated_by_id, NOW(), NOW())
            RETURNING id
        """)

        # Prepare interests as JSON (send as Python list, SQLAlchemy will convert)
        import json
        interests_json = None
        expectations_val = child_data.get('expectations')
        if expectations_val and str(expectations_val).strip() and str(expectations_val) != 'nan' and expectations_val != '':
            try:
                # Send as Python list, SQLAlchemy converts to JSON
                interests_json = [str(expectations_val)[:500]]
            except:
                interests_json = None

        child_id = db.execute(child_insert, {
            "center_id": CENTER_ID,
            "first_name": (child_data['child_first_name'] or 'Unknown')[:100],
            "last_name": (child_data['child_last_name'] or '')[:100] if child_data['child_last_name'] else None,
            "dob": child_data['dob'],
            "school": (child_data['school'] or '')[:200] if child_data['school'] else None,
            "interests": interests_json,
            "notes": (child_data['remarks'] or '')[:1000] if child_data['remarks'] else None,
            "external_id": enquiry_id[:50],
            "created_by_id": created_by_id,
            "updated_by_id": created_by_id
        }).scalar()

        child_id_map[enquiry_id] = child_id
        stats['children'] += 1

        # Insert or get Parent
        parent_contact = child_data['contact']
        if parent_contact:
            if parent_contact not in parent_id_map:
                existing_parent = db.execute(text("SELECT id FROM parents WHERE phone = :phone AND center_id = :center_id"),
                                            {"phone": parent_contact, "center_id": CENTER_ID}).scalar()

                if existing_parent:
                    parent_id_map[parent_contact] = existing_parent
                else:
                    parent_insert = text("""
                        INSERT INTO parents (center_id, name, phone, email, notes, created_by_id, updated_by_id, created_at, updated_at)
                        VALUES (:center_id, :name, :phone, :email, :notes, :created_by_id, :updated_by_id, NOW(), NOW())
                        RETURNING id
                    """)

                    parent_id = db.execute(parent_insert, {
                        "center_id": CENTER_ID,
                        "name": (child_data['parent_name'] or 'Parent')[:200],
                        "phone": parent_contact[:20],
                        "email": (child_data['email'] or '')[:255] if child_data['email'] else None,
                        "notes": None,
                        "created_by_id": created_by_id,
                        "updated_by_id": created_by_id
                    }).scalar()

                    parent_id_map[parent_contact] = parent_id
                    stats['parents'] += 1

            # Insert Family Link
            family_link_insert = text("""
                INSERT INTO family_links (center_id, child_id, parent_id, relationship, is_primary_contact, created_by_id, updated_by_id, created_at, updated_at)
                VALUES (:center_id, :child_id, :parent_id, :relationship, :is_primary, :created_by_id, :updated_by_id, NOW(), NOW())
            """)

            db.execute(family_link_insert, {
                "center_id": CENTER_ID,
                "child_id": child_id,
                "parent_id": parent_id_map[parent_contact],
                "relationship": 'parent',
                "is_primary": True,
                "created_by_id": created_by_id,
                "updated_by_id": created_by_id
            })

            stats['family_links'] += 1

        if (idx % 100 == 0):
            print(f"  Progress: {idx}/{len(master_children)} children...")
            db.commit()

    except Exception as e:
        error_msg = f"Child {enquiry_id}: {str(e)[:100]}"
        stats['errors'].append(error_msg)
        print(f"  ERROR: {error_msg}")
        db.rollback()
        continue

db.commit()
print(f"OK Imported {stats['children']} children, {stats['parents']} parents, {stats['family_links']} family links")

# Step 3: Import Leads
print("\nStep 3: Importing Leads...")
print("-" * 80)

for idx, (enquiry_id, child_data) in enumerate(master_children.items(), 1):
    try:
        if enquiry_id not in child_id_map:
            continue

        child_id = child_id_map[enquiry_id]

        # Determine status
        if 'Enrolled' in child_data['sources'] or 'Expired' in child_data['sources'] or 'Tracker' in child_data['sources']:
            status = 'CONVERTED'
        elif 'IV' in child_data['sources']:
            status = 'INTRO_ATTENDED'
        else:
            status = 'ENQUIRY_RECEIVED'

        lead_insert = text("""
            INSERT INTO leads (center_id, child_id, status, source, discovery_notes, external_id, created_by_id, updated_by_id, created_at, updated_at)
            VALUES (:center_id, :child_id, :status, :source, :discovery_notes, :external_id, :created_by_id, :updated_by_id, :created_at, NOW())
        """)

        db.execute(lead_insert, {
            "center_id": CENTER_ID,
            "child_id": child_id,
            "status": status,
            "source": 'WALK_IN',
            "discovery_notes": (child_data['remarks'] or '')[:1000] if child_data['remarks'] else None,
            "external_id": enquiry_id[:50],
            "created_by_id": created_by_id,
            "updated_by_id": created_by_id,
            "created_at": child_data['enquiry_date'] or datetime.now()
        })

        stats['leads'] += 1

        if (idx % 100 == 0):
            print(f"  Progress: {idx}/{len(master_children)} leads...")
            db.commit()

    except Exception as e:
        error_msg = f"Lead {enquiry_id}: {str(e)[:100]}"
        stats['errors'].append(error_msg)
        print(f"  ERROR: {error_msg}")
        db.rollback()
        continue

db.commit()
print(f"OK Imported {stats['leads']} leads")

# Save mapping for next phases
import pickle
with open('import_mappings.pkl', 'wb') as f:
    pickle.dump({
        'child_id_map': child_id_map,
        'parent_id_map': parent_id_map,
        'master_children': master_children
    }, f)

db.close()

# Print Summary
print("\n" + "=" * 80)
print("IMPORT SUMMARY - PHASE 2")
print("=" * 80)
print(f"Children imported: {stats['children']}")
print(f"Parents imported: {stats['parents']}")
print(f"Family links created: {stats['family_links']}")
print(f"Leads created: {stats['leads']}")
print(f"\nErrors encountered: {len(stats['errors'])}")

if stats['errors']:
    print("\nFirst 10 errors:")
    for err in stats['errors'][:10]:
        print(f"  - {err}")

print("\n" + "=" * 80)
print("Phase 2 Complete!")
print("Mappings saved to import_mappings.pkl")
print("=" * 80)
