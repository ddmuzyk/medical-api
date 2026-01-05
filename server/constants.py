from enum import Enum
class UserRole(Enum):
    ADMIN = 'admin'
    USER = 'user'
    DOCTOR = 'doctor'

class UserTables(Enum):
    USERS = 'users'
    PATIENTS = 'patients'
    DOCTORS = 'doctors'

class AppointmentTables(Enum):
    APPOINTMENTS = 'appointments'
    DOCTOR_AVAILABILITY = 'doctor_availability'
    PRESCRIPTIONS = 'prescriptions'
    PRESCRIPTION_ITEMS = 'prescription_items'

class AppointmentStatus(Enum):
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

specializations = {
    'CARDIOLOGY': 'cardiology',
    'DERMATOLOGY': 'dermatology',
    'NEUROLOGY': 'neurology',
    'PEDIATRICS': 'pediatrics',
    'OPHTHALMOLOGY': 'ophthalmology',
    'ORTHOPEDICS': 'orthopedics',
    'PSYCHIATRY': 'psychiatry',
    'RHEUMATOLOGY': 'rheumatology',
    'GYNECOLOGY': 'gynecology',
    "ONCOLOGY": 'oncology',
    'GENERAL_MEDICINE': 'general_medicine'
}

NOTIFICATION_TABLE = 'notifications'

class NotificationType(Enum):
    APPOINTMENT_REMINDER = 'appointment_reminder'
    NEW_PRESCRIPTION = 'new_prescription'
    GENERAL_NOTIFICATION = 'general_notification'

class ErrorMessages(Enum):
    USER_EXISTS = 'User with this email already exists.'
    NO_USER_ID = 'No user ID provided.'
    USER_NOT_FOUND = 'User not found.'