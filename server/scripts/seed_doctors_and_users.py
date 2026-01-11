"""
Seed basic doctors and users for the medical system.
Creates 3 doctors with different specializations if they don't already exist.
This script is idempotent - safe to run multiple times.
"""
import sys
import os

# Add parent directory to path to import server modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_connection import DbPool
from queries.user import UserQueryManager
from constants import UserRole, specializations


def cleanup_orphaned_users():
    """
    Clean up users without corresponding doctor records.
    Removes 'orphaned' users that were created but doctor insert failed.
    """
    print("🧹 Cleaning up orphaned users (users without doctor records)...")
    
    cleaned_count = 0
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            
            # Find all doctor-role users
            cur.execute(
                """
                SELECT u.id, u.email 
                FROM users u 
                WHERE u.role = 'doctor' 
                AND NOT EXISTS (
                    SELECT 1 FROM doctors d WHERE d.user_id = u.id
                )
                """
            )
            orphaned_users = cur.fetchall()
            
            if orphaned_users:
                for user in orphaned_users:
                    print(f"  🗑️  Removing orphaned user: {user['email']} (id={user['id']})")
                    cur.execute("DELETE FROM users WHERE id = %s", (user['id'],))
                    cleaned_count += 1
                print(f"   ✓ Cleaned {cleaned_count} orphaned user(s)")
            else:
                print("   ✓ No orphaned users found")
                
    except Exception as e:
        print(f"⚠️  Warning during cleanup: {str(e)}")


def seed_doctors_and_users():
    """
    Seed 3 doctors with their corresponding user accounts.
    Idempotent: checks if users/doctors exist before creating.
    """
    print("🌱 Seeding doctors and users...")
    
    # First, clean up any orphaned users from previous failed runs
    cleanup_orphaned_users()
    
    # Define doctors to create - using valid specializations from constants.py
    doctors_data = [
        {
            "email": "jan.kowalski@hospital.com",
            "password": "Doctor123!",
            "first_name": "Jan",
            "last_name": "Kowalski",
            "specialization": specializations['CARDIOLOGY'],  # "cardiology"
            "license_number": "LIC1001"
        },
        {
            "email": "anna.nowak@hospital.com",
            "password": "Doctor123!",
            "first_name": "Anna",
            "last_name": "Nowak",
            "specialization": specializations['DERMATOLOGY'],  # "dermatology"
            "license_number": "LIC1002"
        },
        {
            "email": "piotr.zielinski@hospital.com",
            "password": "Doctor123!",
            "first_name": "Piotr",
            "last_name": "Zieliński",
            "specialization": specializations['PEDIATRICS'],  # "pediatrics"
            "license_number": "LIC1003"
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            
            for doctor_data in doctors_data:
                email = doctor_data["email"]
                
                # Check if user already exists
                existing_user = user_manager.get_user_by_email(email)
                
                if existing_user:
                    print(f"  ⏭️  User {email} already exists (user_id={existing_user['id']}), skipping...")
                    skipped_count += 1
                    
                    # Check if doctor record exists for this user
                    existing_doctor = user_manager.get_doctor_by_user_id(existing_user['id'])
                    if existing_doctor:
                        print(f"      Doctor record already exists: {existing_doctor['first_name']} {existing_doctor['last_name']}")
                    else:
                        # User exists but doctor record doesn't - create it
                        print(f"      Creating missing doctor record...")
                        user_manager.doctor.insert_doctor(
                            user_id=existing_user['id'],
                            first_name=doctor_data['first_name'],
                            last_name=doctor_data['last_name'],
                            specialization=doctor_data['specialization'],
                            license_number=doctor_data['license_number']
                        )
                        print(f"      ✓ Doctor record created")
                        created_count += 1
                else:
                    # Create new user and doctor
                    print(f"  ➕ Creating user: {email}")
                    
                    user_id = user_manager.register_user(
                        email=doctor_data['email'],
                        password=doctor_data['password'],
                        role=UserRole.DOCTOR.value,
                        first_name=doctor_data['first_name'],
                        last_name=doctor_data['last_name'],
                        specialization=doctor_data['specialization'],
                        license_number=doctor_data['license_number']
                    )
                    
                    # Activate doctor account (doctors need admin approval by default, but we activate for seed)
                    user_manager.activate_user(user_id)
                    
                    print(f"      ✓ Created and activated: {doctor_data['first_name']} {doctor_data['last_name']} "
                          f"({doctor_data['specialization']})")
                    created_count += 1
            
            print(f"\n✅ Seeding completed!")
            print(f"   📊 {created_count} doctor(s) created/completed, {skipped_count} already existed")
            
    except Exception as e:
        print(f"❌ Error seeding doctors and users: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    seed_doctors_and_users()
