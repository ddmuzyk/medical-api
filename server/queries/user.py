from constants import UserRole, UserTables, specializations
from utils.queries import create_placeholder_data, get_set_clause_and_values
import datetime as dt
import bcrypt

class PatientQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_patient(self, **patient_data):
        allowed_columns = {'user_id', 'first_name', 'last_name', 'pesel', 'phone'}
        columns, placeholders, values = create_placeholder_data(patient_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {UserTables.PATIENTS} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def get_patient_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            SELECT id, user_id, first_name, last_name, pesel, phone
            FROM {UserTables.PATIENTS} WHERE user_id = %s
            """,
            (user_id,)
        )
        return self.cur.fetchone()
    
    def get_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT id, user_id, first_name, last_name, pesel, phone
            FROM {UserTables.PATIENTS} WHERE id = %s
            """,
            (patient_id,)
        )
        return self.cur.fetchone()
    
    def delete_patient_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {UserTables.PATIENTS} WHERE user_id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()['id']
    
    def update_patient_info(self, **patient_data):
        user_id = patient_data.get('user_id')
        if not user_id:
            raise ValueError("User ID is required for updating patient info")
        
        allowed_columns = {'first_name', 'last_name', 'pesel', 'phone'}
        set_clause_str, values = get_set_clause_and_values({**patient_data, 'user_id': user_id}, allowed_columns)

        self.cur.execute(
            f"""
            UPDATE {UserTables.PATIENTS}
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
class DoctorQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_doctor(self, **doctor_data):
        allowed_specializations = set(specializations.values())
        if 'specialization' in doctor_data and doctor_data['specialization'] not in allowed_specializations:
            raise ValueError("Invalid specialization provided")

        allowed_columns = {'user_id', 'first_name', 'last_name', 'specialization', 'license_number'}
        columns, placeholders, values = create_placeholder_data(doctor_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {UserTables.DOCTORS} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def get_doctor_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            SELECT id, user_id, first_name, last_name, specialization, license_number
            FROM {UserTables.DOCTORS} WHERE user_id = %s
            """,
            (user_id,)
        )
        return self.cur.fetchone()
    
    def get_doctor(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT id, user_id, first_name, last_name, specialization, license_number
            FROM {UserTables.DOCTORS} WHERE id = %s
            """,
            (doctor_id,)
        )
        return self.cur.fetchone()
    
    def get_doctors_by_specialization(self, specialization):
        self.cur.execute(
            f"""
            SELECT id, user_id, first_name, last_name, specialization, license_number
            FROM {UserTables.DOCTORS} WHERE specialization = %s
            """,
            (specialization,)
        )
        return self.cur.fetchall()
    
    def delete_doctor_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {UserTables.DOCTORS} WHERE user_id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()['id']
    
    def update_doctor_info(self, **doctor_data):
        user_id = doctor_data.get('user_id')

        if not user_id:
            raise ValueError("User ID is required for updating doctor info")
        
        allowed_columns = {'first_name', 'last_name', 'specialization', 'license_number'}
        set_clause_str, values = get_set_clause_and_values({**doctor_data, 'user_id': user_id}, allowed_columns)

        self.cur.execute(
            f"""
            UPDATE {UserTables.DOCTORS}
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
class UserQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_user(self, email, password_hash, is_active, role):
        self.cur.execute(
            f"""
            INSERT INTO {UserTables.USERS} (email, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (email, password_hash, role, is_active, dt.datetime.now())
        )
        return self.cur.fetchone()['id']
    
    def get_user_by_id(self, user_id):
        self.cur.execute(
            f"""
            SELECT id, email, role, is_active, created_at FROM {UserTables.USERS} WHERE id = %s
            """,
            (user_id,)
        )
        return self.cur.fetchone()
    
    def get_user_by_email(self, email):
        self.cur.execute(
            f"""
            SELECT id, email, password_hash, role, is_active, created_at FROM {UserTables.USERS} WHERE email = %s
            """,
            (email,)
        )
        return self.cur.fetchone()
    
    def get_pending_users(self):
        self.cur.execute(
            f"""
            SELECT id, email, role, created_at 
            FROM {UserTables.USERS} 
            WHERE is_active = FALSE AND role = %s
            """,
            (UserRole.DOCTOR,)
        )
        return self.cur.fetchall()
    
    def update_user(self, user_id, **user_data):
        allowed_data = {'email', 'password_hash'}
        set_clause_str, values = get_set_clause_and_values({**user_data}, allowed_data)
        values.append(user_id)

        self.cur.execute(
            f"""
            UPDATE {UserTables.USERS}
            SET {set_clause_str}
            WHERE id = %s
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def activate_user(self, user_id):
        self.cur.execute(
            f"""
            UPDATE {UserTables.USERS}
            SET is_active = TRUE
            WHERE id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()['id']
    
    def delete_user(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {UserTables.USERS} WHERE id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()['id']

class UserQueryManager:
    def __init__(self, cursor):
        self.cur = cursor
        self.user = UserQueryHelper(cursor)
        self.patient = PatientQueryHelper(cursor)
        self.doctor = DoctorQueryHelper(cursor)


    def register_user(self, **user_data):
        if not user_data.get('email') or not user_data.get('password') or not user_data.get('role'):
            raise ValueError("Email, password, and role are required")
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_id = self.user.insert_user(
            email=user_data['email'],
            password_hash=hashed_password,
            is_active=user_data['role'] == UserRole.USER,
            role=user_data['role']
        )

        if user_data['role'] == UserRole.USER:
            self.patient.insert_patient(
                user_id=user_id,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                pesel=user_data.get('pesel'),
                phone=user_data.get('phone')
            )

        elif user_data['role'] == UserRole.DOCTOR:
            self.doctor.insert_doctor(
                user_id=user_id,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                specialization=user_data.get('specialization'),
                license_number=user_data.get('license_number')
            )

        return user_id
    
    def register_admin(self, email, password):
        """Registers an admin user directly. Hidden method for seeding purposes."""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_id = self.user.insert_user(
            email=email,
            password_hash=hashed_password,
            is_active=True,
            role=UserRole.ADMIN
        )
        return user_id

    def get_user_by_id(self, user_id):
        return self.user.get_user_by_id(user_id)
    
    def get_user_by_email(self, email):
        return self.user.get_user_by_email(email)

    def get_patient(self, patient_id):
        return self.patient.get_patient(patient_id)
    
    def get_doctor(self, doctor_id):
        return self.doctor.get_doctor(doctor_id)
    
    def get_doctor_by_user_id(self, user_id):
        return self.doctor.get_doctor_by_user_id(user_id)
    
    def get_patient_by_user_id(self, user_id):
        return self.patient.get_patient_by_user_id(user_id)
    
    def get_doctors_by_specialization(self, specialization):
        return self.doctor.get_doctors_by_specialization(specialization)
    
    def get_pending_users(self):
        return self.user.get_pending_users()
    
    def update_user(self, **user_data):
        return self.user.update_user(**user_data)
    
    def update_patient(self, **patient_data):
        return self.patient.update_patient_info(**patient_data)
    
    def update_doctor(self, **doctor_data):
        return self.doctor.update_doctor_info(**doctor_data)
    
    def activate_user(self, user_id):
        return self.user.activate_user(user_id)
    
    def delete_user(self, user_id):
        user_record = self.user.get_user_by_id(user_id)
        if not user_record:
            return None

        role = user_record['role']

        if role == UserRole.USER:
            self.patient.delete_patient_by_user_id(user_id)
        elif role == UserRole.DOCTOR:
            self.doctor.delete_doctor_by_user_id(user_id)

        deleted_user_id = self.user.delete_user(user_id)
        return deleted_user_id
    