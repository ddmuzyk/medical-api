from constants import userRole, userTables
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

        return user_id
    
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
    