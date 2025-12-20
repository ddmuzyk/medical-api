from constants import userRole
from db_connection import DbPool
import datetime as dt
import bcrypt

class UserQueryManager:
    def __init__(self, cursor):
        self.cur = cursor

    def add_user_to_db(self, email, password, role=userRole['USER']):
        timestamp = dt.datetime.now()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        self.cur.execute(
            """
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (email, hashed_password, role, timestamp)
        )
        user_id = self.cur.fetchone()[0]
        return user_id
    
    def delete_users(self, *userIds):
        if not userIds:
            return 0
        
        placeholders = ','.join(['%s'] * len(userIds))
        self.cur.execute(
            f"""
            DELETE FROM users WHERE id IN ({placeholders})
            """,
            userIds
        )
        return self.cur.rowcount