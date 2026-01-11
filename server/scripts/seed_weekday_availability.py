"""
Seed weekday availability for all doctors.
Generates Mon-Fri slots from 09:00 to 17:00 (60 min intervals) for 4 weeks ahead.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import server modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_connection import DbPool
from queries.user import UserQueryManager
from queries.appointment import AppointmentQueryManager


def seed_weekday_availability():
    """
    Seed availability slots for all doctors.
    - Mon-Fri only (weekday 0-4)
    - 09:00 to 17:00 (slots at 09:00, 10:00, ..., 16:00)
    - 4 weeks ahead from today
    - is_available = TRUE
    - Skip duplicates (check by doctor_id + start_time)
    """
    print("🌱 Seeding weekday availability for all doctors...")
    
    added_count = 0
    skipped_count = 0
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            
            # Get all doctors
            cur.execute("SELECT id, first_name, last_name, specialization FROM doctors")
            doctors = cur.fetchall()
            
            if not doctors:
                print("⚠️  No doctors found in database. Please create doctors first.")
                return
            
            print(f"📋 Found {len(doctors)} doctor(s)")
            
            # Generate slots for 4 weeks ahead
            today = datetime.now().date()
            end_date = today + timedelta(weeks=4)
            
            print(f"📅 Generating slots from {today} to {end_date}")
            
            for doctor in doctors:
                doctor_id = doctor['id']
                doctor_name = f"{doctor['first_name']} {doctor['last_name']}"
                doctor_added = 0
                doctor_skipped = 0
                
                current_date = today
                while current_date <= end_date:
                    # Skip weekends (Monday=0, Sunday=6)
                    if current_date.weekday() < 5:  # Mon-Fri
                        # Generate slots from 09:00 to 16:00 (last slot starts at 16:00, ends at 17:00)
                        for hour in range(9, 17):
                            start_time = datetime.combine(current_date, datetime.min.time()).replace(
                                hour=hour, minute=0, second=0
                            )
                            end_time = start_time + timedelta(hours=1)
                            
                            # Check if slot already exists for this doctor at this time
                            cur.execute(
                                """
                                SELECT id FROM doctor_availability 
                                WHERE doctor_id = %s AND start_time = %s
                                """,
                                (doctor_id, start_time)
                            )
                            existing = cur.fetchone()
                            
                            if existing:
                                doctor_skipped += 1
                            else:
                                # Insert new availability slot
                                try:
                                    appointment_manager.create_doctor_availability(
                                        doctor_id=doctor_id,
                                        start_time=start_time,
                                        end_time=end_time,
                                        is_available=True
                                    )
                                    doctor_added += 1
                                except Exception as e:
                                    # Skip if there's an overlap error (handled by backend validation)
                                    if "overlaps" in str(e).lower():
                                        doctor_skipped += 1
                                    else:
                                        raise
                    
                    current_date += timedelta(days=1)
                
                print(f"  ✓ {doctor_name} ({doctor['specialization']}): "
                      f"{doctor_added} added, {doctor_skipped} skipped")
                added_count += doctor_added
                skipped_count += doctor_skipped
            
            print(f"\n✅ Seeding completed!")
            print(f"   📊 Total: {added_count} slots added, {skipped_count} skipped (duplicates)")
            
    except Exception as e:
        print(f"❌ Error seeding availability: {str(e)}")
        raise


if __name__ == "__main__":
    seed_weekday_availability()
