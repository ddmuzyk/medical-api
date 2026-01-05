from constants import UserRole, NOTIFICATION_TABLE, specializations
from utils.queries import create_placeholder_data, get_set_clause_and_values
import datetime as dt
from constants import NotificationType

class NotificationQueryManager:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_notification(self, user_id, type, title, content, is_read=False):
        self.cur.execute(
            f"""
            INSERT INTO {NOTIFICATION_TABLE} (user_id, type, title, content, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            tuple([user_id, type, title, content, is_read, dt.datetime.now()])
        )
        return self.cur.fetchone()['id']
    
    def mark_notification_as_read(self, notification_id):
        self.cur.execute(
            f"""
            UPDATE {NOTIFICATION_TABLE}
            SET is_read = TRUE
            WHERE id = %s
            RETURNING id
            """,
            (notification_id,)
        )
        return self.cur.fetchone()['id']
    
    def get_notification(self, notification_id):
        self.cur.execute(
            f"""
            SELECT * FROM {NOTIFICATION_TABLE}
            WHERE id = %s
            """,
            (notification_id,)
        )
        return self.cur.fetchone()
    
    def get_notifications_by_user(self, user_id):
        self.cur.execute(
            f"""
            SELECT title, type, content, is_read, created_at FROM {NOTIFICATION_TABLE}
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        return self.cur.fetchall()
    
    def delete_notification(self, notification_id):
        self.cur.execute(
            f"""
            DELETE FROM {NOTIFICATION_TABLE}
            WHERE id = %s
            RETURNING id
            """,
            (notification_id,)
        )
        return self.cur.fetchone()['id']
    
    def delete_notifications_by_user(self, user_id):
        self.cur.execute(
            f"""
            DELETE FROM {NOTIFICATION_TABLE}
            WHERE user_id = %s
            RETURNING id
            """,
            (user_id,)
        )
        return [row['id'] for row in self.cur.fetchall()]