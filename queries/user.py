from constants import userRole, userTables, specializations
from utils.queries import create_placeholder_data
import datetime as dt
import bcrypt

class UserQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_user(self, email, password_hash, role):
        self.cur.execute(
            f"""
            INSERT INTO {userTables['USERS']} (email, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (email, password_hash, role, dt.datetime.now())
        )
        return self.cur.fetchone()[0]
    
    def insert_patient(self, **patient_data):
        allowed_columns = {'user_id', 'first_name', 'last_name', 'pesel', 'phone'}
        columns, placeholders, values = create_placeholder_data(patient_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {userTables['PATIENTS']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()[0]
    
    def insert_doctor(self, **doctor_data):
        allowed_specializations = set(specializations.values())
        if 'specialization' in doctor_data and doctor_data['specialization'] not in allowed_specializations:
            raise ValueError("Invalid specialization provided")

        allowed_columns = {'user_id', 'first_name', 'last_name', 'specialization', 'license_number'}
        columns, placeholders, values = create_placeholder_data(doctor_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {userTables['DOCTORS']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()[0]
    
    def delete_user(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {userTables['USERS']} WHERE id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()[0]
    
    def delete_patient_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {userTables['PATIENTS']} WHERE user_id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()[0]
    
    def delete_doctor_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {userTables['DOCTORS']} WHERE user_id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return self.cur.fetchone()[0]
    
    def get_user_by_user_id(self, user_id):
        self.cur.execute(
            f"""
            SELECT id, email, role, created_at FROM {userTables['USERS']} WHERE id = %s
            """,
            (user_id,)
        )
        return self.cur.fetchone()
    
    def update_patient_info(self, **patient_data):
        user_id = patient_data.get('user_id')
        if not user_id:
            raise ValueError("User ID is required for updating patient info")
        
        allowed_columns = {'first_name', 'last_name', 'pesel', 'phone'}
        set_clauses = []
        values = []
        for key in allowed_columns:
            if key in patient_data:
                set_clauses.append(f"{key} = %s")
                values.append(patient_data[key])
        
        if not set_clauses:
            raise ValueError("No valid fields provided for update")
        
        values.append(user_id)
        set_clause_str = ", ".join(set_clauses)

        self.cur.execute(
            f"""
            UPDATE {userTables['PATIENTS']}
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()[0]
    
    def update_doctor_info(self, **doctor_data):
        user_id = doctor_data.get('user_id')
        if not user_id:
            raise ValueError("User ID is required for updating doctor info")
        
        allowed_columns = {'first_name', 'last_name', 'specialization', 'license_number'}
        set_clauses = []
        values = []
        for key in allowed_columns:
            if key in doctor_data:
                set_clauses.append(f"{key} = %s")
                values.append(doctor_data[key])
        
        if not set_clauses:
            raise ValueError("No valid fields provided for update")
        
        values.append(user_id)
        set_clause_str = ", ".join(set_clauses)

        self.cur.execute(
            f"""
            UPDATE {userTables['DOCTORS']}
            SET {set_clause_str}
            WHERE user_id = %s
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()[0]

class UserQueryManager:
    def __init__(self, cursor):
        self.cur = cursor
        self.helper = UserQueryHelper(cursor)

    def register_user(self, **user_data):
        if not user_data.get('email') or not user_data.get('password') or not user_data.get('role'):
            raise ValueError("Email, password, and role are required")
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_id = self.helper.insert_user(
            email=user_data['email'],
            password_hash=hashed_password,
            role=user_data['role']
        )

        if user_data['role'] == userRole['USER']:
            self.helper.insert_patient(
                user_id=user_id,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                pesel=user_data.get('pesel'),
                phone=user_data.get('phone')
            )

        elif user_data['role'] == userRole['DOCTOR']:
            self.helper.insert_doctor(
                user_id=user_id,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                specialization=user_data.get('specialization'),
                license_number=user_data.get('license_number')
            )

        return user_id
    
    def update_user(self, user_id, **user_data):
        result = self.helper.get_user_by_user_id(user_id)
        if not result:
            raise ValueError("User not found")
        role = result[2]

        if role == userRole['USER']:
            updated_id = self.helper.update_patient_info(user_id=user_id, **user_data)
        else:
            raise ValueError("Update functionality for this role is not implemented")

        return updated_id
    
    def delete_user(self, user_id):
        if not user_id:
            return False
        
        result = self.helper.get_user_by_user_id(user_id)

        if not result:
            return False
        role = result[2]

        if role == userRole['USER']:
            self.helper.delete_patient_by_user_id(user_id)
        elif role == userRole['DOCTOR']:
            self.helper.delete_doctor_by_user_id(user_id)

        deleted_user_id = self.helper.delete_user(user_id)
        return deleted_user_id
    