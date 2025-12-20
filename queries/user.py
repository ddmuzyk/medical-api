from constants import userRole
from utils.queries import create_placeholder_data
import datetime as dt
import bcrypt

class UserQueryManager:
    def __init__(self, cursor):
        self.cur = cursor

    def add_user_to_db(self, **user_data):
        timestamp = dt.datetime.now()
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        allowed_columns = {'email', 'password_hash', 'role', 'created_at'}
        columns, placeholders, values = create_placeholder_data(
            {
                'email': user_data['email'],
                'password_hash': hashed_password,
                'role': user_data['role'],
                'created_at': timestamp
            },
            allowed_columns
        )

        self.cur.execute(
            f"""
            INSERT INTO users ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        user_id = self.cur.fetchone()[0]
        return user_id
    
    def add_patient(self, **user_data):
        allowed_columns = {'user_id', 'first_name', 'last_name', 'pesel', 'phone'}
        columns, placeholders, values = create_placeholder_data(user_data, allowed_columns)

        if not columns:
            raise ValueError("No valid columns provided")

        self.cur.execute(
            f"""
            INSERT INTO patients ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        patient_id = self.cur.fetchone()[0]
        return patient_id
    
    def delete_user(self, user_id):
        if not user_id:
            return False
        
        self.cur.execute(
            f"""
            SELECT role FROM users WHERE id = %s
            """,
            (user_id,)
        )

        result = self.cur.fetchone()
        if not result:
            return False
        role = result[0]

        if role == userRole['USER']:
            self.cur.execute(
                f"""
                DELETE FROM patients WHERE user_id = %s
                RETURNING id
                """,
                (user_id,)
            )
        
        self.cur.execute(
            f"""
            DELETE FROM users WHERE id = %s
            returning id
            """,
            (user_id,)
        )

        deleted_user_id = self.cur.fetchone()[0]
        
        return deleted_user_id
        