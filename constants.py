userRole = {
    'ADMIN': 'admin',
    'USER': 'user',
    'DOCTOR': 'doctor'
}

userTables = {
    'USERS': 'users',
    'PATIENTS': 'patients',
    'DOCTORS': 'doctors'
}

appointmentTables = {
    'APPOINTMENTS': 'appointments',
    'DOCTOR_AVAILABILITY': 'doctor_availability',
    'PRESCRIPTIONS': 'prescriptions',
    'PRESCRIPTION_ITEMS': 'prescription_items'
}

appointmentStatus = {
    'SCHEDULED': 'scheduled',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled',
}

specializations = {
    'CARDIOLOGY': 'cardiology',
    'DERMATOLOGY': 'dermatology',
    'NEUROLOGY': 'neurology',
    'PEDIATRICS': 'pediatrics',
    'OCULIST': 'oculist',
    'ORTHOPEDICS': 'orthopedics',
    'PSYCHIATRY': 'psychiatry',
    'GYNECOLOGY': 'gynecology',
    "ONCOLOGY": 'oncology',
    'ENT': 'ear_nose_throat',
    'GENERAL_MEDICINE': 'general_medicine'
}

errorMessages = {
    'USER_EXISTS': 'User with this email already exists.',
    'NO_USER_ID': 'No user ID provided.',
    'USER_NOT_FOUND': 'User not found.'
}