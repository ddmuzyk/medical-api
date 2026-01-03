from db_connection import DbPool
from queries.user import UserQueryManager
from queries.appointment import AppointmentQueryManager
from constants import UserRole, specializations
from datetime import datetime, timedelta

def seed_database():
    """Populate database with test data"""
    print("🌱 Seeding database...")
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)

            print("Creating admin...")
            admin_id = user_manager.register_admin(
                email="admin@hospital.com",
                password="Admin123!",
            )

            print("Creating doctors...")
            doctor1_id = user_manager.register_user(
                email="doctor1@hospital.com",
                password="d",
                role=UserRole.DOCTOR,
                first_name="John",
                last_name="Smith",
                specialization=specializations['CARDIOLOGY'],
                license_number="LIC123456"
            )
            
            doctor2_id = user_manager.register_user(
                email="doctor2@hospital.com",
                password="d",
                role=UserRole.DOCTOR,
                first_name="Sarah",
                last_name="Johnson",
                specialization=specializations['PEDIATRICS'],
                license_number="LIC789012",
                is_active=False  # Pending approval
            )
            
            # Create patients
            print("Creating patients...")
            patient1_id = user_manager.register_user(
                email="patient1@email.com",
                password="p",
                role=UserRole.USER,
                first_name="Michael",
                last_name="Brown",
                pesel="90010112345",
                phone="+48123456789"
            )
            
            patient2_id = user_manager.register_user(
                email="patient2@email.com",
                password="p",
                role=UserRole.USER.value,
                first_name="Emma",
                last_name="Davis",
                pesel="85050567890",
                phone="+48987654321"
            )
            
            # Get doctor IDs from users
            doctor1 = user_manager.get_doctor_by_user_id(doctor1_id)
            doctor2 = user_manager.get_doctor_by_user_id(doctor2_id)
            
            # Create availability slots
            print("Creating availability slots...")
            tomorrow = datetime.now() + timedelta(days=1)
            
            for hour in range(9, 17):  # 9 AM to 5 PM
                appointment_manager.create_doctor_availability(
                    doctor_id=doctor1['id'],
                    start_time=tomorrow.replace(hour=hour, minute=0, second=0),
                    end_time=tomorrow.replace(hour=hour + 1, minute=0, second=0)
                )
            
            print("✅ Database seeded successfully!")
            print("\n📋 Test Accounts:")
            print("Admin: admin@hospital.com / Admin123!")
            print("Doctor 1 (Active): doctor1@hospital.com / Doctor123!")
            print("Doctor 2 (Pending): doctor2@hospital.com / Doctor123!")
            print("Patient 1: patient1@email.com / Patient123!")
            print("Patient 2: patient2@email.com / Patient123!")
            
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")

if __name__ == "__main__":
    seed_database()