from enum import Enum

class StrEnum(str, Enum):
    def __str__(self):
        return self.value
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
class UserRole(StrEnum):
    ADMIN = 'admin'
    USER = 'user'
    DOCTOR = 'doctor'

class UserTables(StrEnum):
    USERS = 'users'
    PATIENTS = 'patients'
    DOCTORS = 'doctors'

class AppointmentTables(StrEnum):
    APPOINTMENTS = 'appointments'
    DOCTOR_AVAILABILITY = 'doctor_availability'
    PRESCRIPTIONS = 'prescriptions'
    PRESCRIPTION_ITEMS = 'prescription_items'

class AppointmentStatus(StrEnum):
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

class NotificationType(StrEnum):
    APPOINTMENT_REMINDER = 'appointment_reminder'
    NEW_PRESCRIPTION = 'new_prescription'
    GENERAL_NOTIFICATION = 'general_notification'

class ErrorMessages(StrEnum):
    USER_EXISTS = 'User with this email already exists.'
    NO_USER_ID = 'No user ID provided.'
    USER_NOT_FOUND = 'User not found.'