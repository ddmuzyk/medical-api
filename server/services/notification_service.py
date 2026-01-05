from queries.notification import NotificationQueryManager
from constants import NotificationType

class NotificationMessagesManager:
    @staticmethod
    def get_content_for_appointment_created(doctor_name, appointment_date):
        return f"Wizyta u Dr. {doctor_name} jest zaplanowana na {appointment_date}"
    
    @staticmethod
    def transform_appointment_status_to_message(status):
        status_messages = {
            "canceled": "anulowana",
            "completed": "zakończona",
            "rescheduled": "przełożona"
        }
        return status_messages.get(status, "zmieniona")
    
    @staticmethod
    def get_content_for_appointment_status_changed(doctor_name, status):
        return f"Twoja wizyta u Dr. {doctor_name} została zmieniona na {NotificationMessagesManager.transform_appointment_status_to_message(status)}"
    
    @staticmethod
    def get_title_for_appointment_status_changed(status):
        return f"Wizyta {NotificationMessagesManager.transform_appointment_status_to_message(status).title()}"
    
    @staticmethod
    def get_content_for_prescription_created(doctor_name):
        return f"Dr. {doctor_name} wystawił Ci nową receptę"
    
    @staticmethod
    def get_account_activated_message(email):
        return f"Twoje konto lekarza ({email}) zostało aktywowane przez administratora"

class NotificationService:
    @staticmethod
    def notify_appointment_created(cur, user_id, doctor_name, appointment_date):
        """Send notification when appointment is created"""
        try:
            notification_manager = NotificationQueryManager(cur)
            notification_manager.insert_notification(
                user_id=user_id,
                type=NotificationType.APPOINTMENT_REMINDER.value,
                title="Wizyta Utworzona",
                content=NotificationMessagesManager.get_content_for_appointment_created(doctor_name, appointment_date),
                is_read=False
            )
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
    
    @staticmethod
    def notify_appointment_status_changed(cur, user_id, doctor_name, status):
        try:
            notification_manager = NotificationQueryManager(cur)
            notification_manager.insert_notification(
                user_id=user_id,
                type=NotificationType.APPOINTMENT_REMINDER.value,
                title=NotificationMessagesManager.get_title_for_appointment_status_changed(status),
                content=NotificationMessagesManager.get_content_for_appointment_status_changed(doctor_name, status),
                is_read=False
            )
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
    
    @staticmethod
    def notify_prescription_created(cur, user_id, doctor_name):
        try:
            notification_manager = NotificationQueryManager(cur)
            notification_manager.insert_notification(
            user_id=user_id,
                type=NotificationType.NEW_PRESCRIPTION.value,
                title="Nowa Recepta",
                content=NotificationMessagesManager.get_content_for_prescription_created(doctor_name),
                is_read=False
            )
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
    
    @staticmethod
    def notify_account_activated(cur, user_id, email):
        """Send notification when doctor account is activated"""
        try:
            notification_manager = NotificationQueryManager(cur)
            notification_manager.insert_notification(
                user_id=user_id,
                type=NotificationType.GENERAL_NOTIFICATION.value,
                title="Konto Aktywowane",
                content=NotificationMessagesManager.get_account_activated_message(email),
                is_read=False
            )
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")