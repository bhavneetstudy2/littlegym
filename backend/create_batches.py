"""
Script to create proper batch data for The Little Gym
"""
import sys
import os
from datetime import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import Batch, Center

def create_batches():
    """Create batch data with proper names and age ranges"""
    db = SessionLocal()

    try:
        # Get the center (Mumbai Central)
        center = db.query(Center).first()
        if not center:
            print("No center found! Please create a center first.")
            return

        # Delete existing batches to avoid duplicates
        db.query(Batch).delete()
        db.commit()

        # Define batches with age ranges
        batches_data = [
            {
                "name": "Giggle Worms",
                "age_min": 0,
                "age_max": 1,
                "days_of_week": ["Monday", "Wednesday", "Friday"],
                "start_time": "10:00",
                "end_time": "10:45",
                "capacity": 8,
                "description": "Parent-child class for babies (0-10 months)"
            },
            {
                "name": "Funny Bugs",
                "age_min": 1,
                "age_max": 2,
                "days_of_week": ["Tuesday", "Thursday", "Saturday"],
                "start_time": "10:00",
                "end_time": "10:45",
                "capacity": 10,
                "description": "Parent-child class for walkers (10-19 months)"
            },
            {
                "name": "Birds",
                "age_min": 2,
                "age_max": 3,
                "days_of_week": ["Monday", "Wednesday", "Friday"],
                "start_time": "11:00",
                "end_time": "11:45",
                "capacity": 12,
                "description": "Parent-child class (19 months - 3 years)"
            },
            {
                "name": "Bugs",
                "age_min": 3,
                "age_max": 4,
                "days_of_week": ["Monday", "Wednesday", "Friday"],
                "start_time": "15:00",
                "end_time": "15:45",
                "capacity": 12,
                "description": "Independent class (3-4 years)"
            },
            {
                "name": "Beasts",
                "age_min": 4,
                "age_max": 6,
                "days_of_week": ["Tuesday", "Thursday", "Saturday"],
                "start_time": "15:00",
                "end_time": "16:00",
                "capacity": 12,
                "description": "Independent class (4-6 years)"
            },
            {
                "name": "Super Beasts",
                "age_min": 6,
                "age_max": 9,
                "days_of_week": ["Tuesday", "Thursday", "Saturday"],
                "start_time": "16:15",
                "end_time": "17:15",
                "capacity": 12,
                "description": "Advanced class (6-9 years)"
            },
            {
                "name": "Good Friends",
                "age_min": 3,
                "age_max": 5,
                "days_of_week": ["Monday", "Wednesday"],
                "start_time": "16:00",
                "end_time": "17:00",
                "capacity": 10,
                "description": "Social skills development (3-5 years)"
            },
            {
                "name": "Grade School",
                "age_min": 6,
                "age_max": 12,
                "days_of_week": ["Friday", "Saturday"],
                "start_time": "17:00",
                "end_time": "18:00",
                "capacity": 15,
                "description": "Sports and fitness for grade schoolers (6-12 years)"
            }
        ]

        created_count = 0
        for batch_data in batches_data:
            # Convert time strings to time objects
            start_parts = batch_data["start_time"].split(":")
            end_parts = batch_data["end_time"].split(":")

            batch = Batch(
                center_id=center.id,
                name=batch_data["name"],
                age_min=batch_data["age_min"],
                age_max=batch_data["age_max"],
                days_of_week=batch_data["days_of_week"],
                start_time=time(int(start_parts[0]), int(start_parts[1])),
                end_time=time(int(end_parts[0]), int(end_parts[1])),
                capacity=batch_data["capacity"],
                active=True,
                is_archived=False
            )
            db.add(batch)
            created_count += 1
            print(f"[OK] Created batch: {batch_data['name']} (Ages {batch_data['age_min']}-{batch_data['age_max']})")

        db.commit()
        print(f"\n[SUCCESS] Successfully created {created_count} batches!")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_batches()
