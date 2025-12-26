from utils.queries import create_placeholder_data
from constants import appointmentTables, appointmentStatus
import datetime as dt

class AppointmentQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_appointment(self, **appointment_data):
        allowed_columns = {'patient_id', 'doctor_id', 'availability_id', 'appointment_date', 'status', 'created_at'}
        columns, placeholders, values = create_placeholder_data({
            **appointment_data,
            "created_at": appointment_data.get("created_at", dt.datetime.now())
        }, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {appointmentTables['APPOINTMENTS']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def update_appointment_status(self, **appointment_data):
        status, appointment_id = appointment_data.get('status'), appointment_data.get('appointment_id')
        allowed_statuses = {'scheduled', 'completed', 'canceled'}
        if appointment_data.get('status') not in allowed_statuses:
            raise ValueError("Invalid status value")
        
        self.cur.execute(
            f"""
            UPDATE {appointmentTables['APPOINTMENTS']}
            SET status = %s
            WHERE id = %s
            RETURNING id
            """,
            (status, appointment_id)
        )
        return self.cur.fetchone()['id']
    
    def get_appointment_by_id(self, appointment_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['APPOINTMENTS']}
            WHERE id = %s
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()
    
    def get_appointments_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['APPOINTMENTS']}
            WHERE patient_id = %s
            ORDER BY appointment_date DESC
            """,
            (patient_id,)
        )
        return self.cur.fetchall()
    
    def get_appointments_by_doctor(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['APPOINTMENTS']}
            WHERE doctor_id = %s
            ORDER BY appointment_date DESC
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
class AvailabilityQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_doctor_availability(self, **availability_data):
        start_time, end_time, doctor_id = availability_data.get('start_time'), availability_data.get('end_time'), availability_data.get('doctor_id')
        
        if (not start_time) or (not end_time):
            raise ValueError("start_time and end_time must be provided")
        if start_time and end_time and start_time >= end_time:
            raise ValueError("start_time must be before end_time")
        
        self.cur.execute(
            f"""
            SELECT 1 FROM {appointmentTables['DOCTOR_AVAILABILITY']}
            WHERE doctor_id = %s AND
                  ((start_time, end_time) OVERLAPS (%s, %s))
            """,
            (availability_data.get('doctor_id'), start_time, end_time)
        )
        if self.cur.fetchone():
            raise ValueError("The specified time slot overlaps with existing availability")
        
        allowed_columns = {'doctor_id', 'is_available', 'start_time', 'end_time'}
        columns, placeholders, values = create_placeholder_data(availability_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {appointmentTables['DOCTOR_AVAILABILITY']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def update_doctor_availability(self, **availability_data):
        is_available, availability_id = availability_data.get('is_available'), availability_data.get('availability_id')
        if not isinstance(is_available, bool):
            raise ValueError("is_available must be a boolean value")
        
        if availability_id is None:
            raise ValueError("Availability_id must be provided")
        
        self.cur.execute(
            f"""
            UPDATE {appointmentTables['DOCTOR_AVAILABILITY']}
            SET is_available = %s
            WHERE id = %s
            RETURNING id
            """,
            (is_available, availability_id)
        )
        return self.cur.fetchone()['id']
    
    def get_doctor_availability(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['DOCTOR_AVAILABILITY']}
            WHERE doctor_id = %s AND is_available = TRUE
            ORDER BY start_time
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def delete_doctor_availability(self, availability_id):
        self.cur.execute(
            f"""
            DELETE FROM {appointmentTables['DOCTOR_AVAILABILITY']} WHERE id = %s
            RETURNING id
            """,
            (availability_id,)
        )
        return self.cur.fetchone()['id']
    
class PrescriptionQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def get_prescription_by_appointment(self, appointment_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['PRESCRIPTIONS']}
            WHERE appointment_id = %s
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()
    
    def get_prescription_items(self, prescription_id):
        self.cur.execute(
            f"""
            SELECT * FROM {appointmentTables['PRESCRIPTION_ITEMS']}
            WHERE prescription_id = %s
            """,
            (prescription_id,)
        )
        return self.cur.fetchall()
    
    def delete_prescription(self, prescription_id):
        self.cur.execute(
            f"""
            DELETE FROM {appointmentTables['PRESCRIPTIONS']} WHERE id = %s
            RETURNING id
            """,
            (prescription_id,)
        )
        return self.cur.fetchone()['id']
    
    def insert_prescription(self, **prescription_data):
        allowed_columns = {'appointment_id', 'issued_at', 'patient_id', 'doctor_id', 'notes'}
        columns, placeholders, values = create_placeholder_data({
            **prescription_data,
            "issued_at": prescription_data.get("issued_at", dt.datetime.now())
        }, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {appointmentTables['PRESCRIPTIONS']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def insert_prescription_item(self, **item_data):
        allowed_columns = {'prescription_id', 'medication_name', 'dosage', 'instructions'}
        columns, placeholders, values = create_placeholder_data(item_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {appointmentTables['PRESCRIPTION_ITEMS']} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']

class AppointmentQueryManager:
    def __init__(self, cursor):
        self.cur = cursor
        self.appointment = AppointmentQueryHelper(cursor)
        self.availability = AvailabilityQueryHelper(cursor)
        self.prescription = PrescriptionQueryHelper(cursor)

    def create_appointment(self, **appointment_data):
        patient_id = appointment_data.get('patient_id')
        doctor_id = appointment_data.get('doctor_id')
        
        self.cur.execute("SELECT 1 FROM patients WHERE id = %s", (patient_id,))
        if not self.cur.fetchone():
            raise ValueError(f"Patient with id {patient_id} does not exist")

        self.cur.execute("SELECT 1 FROM doctors WHERE id = %s", (doctor_id,))
        if not self.cur.fetchone():
            raise ValueError(f"Doctor with id {doctor_id} does not exist")

    def create_doctor_availability(self, **availability_data):
        return self.availability.insert_doctor_availability(**availability_data)

    def create_prescription(self, **prescription_data):
        prescription_id = self.prescription.insert_prescription(**prescription_data)
        if not prescription_id:
            raise Exception("Failed to create prescription")
        
        prescription_item_id = self.prescription.insert_prescription_item(
            prescription_id=prescription_id,
            medication_name=prescription_data.get('medication_name'),
            dosage=prescription_data.get('dosage'),
            instructions=prescription_data.get('instructions')
        )
        if not prescription_item_id:
            raise Exception("Failed to create prescription item")
        return prescription_id
    
    def change_appointment_status(self, **appointment_data):
        return self.appointment.update_appointment_status(**appointment_data)
    
    def change_doctor_availability(self, **availability_data):
        return self.availability.update_doctor_availability(**availability_data)
    
    def remove_doctor_availability(self, availability_id):
        return self.availability.delete_doctor_availability(availability_id)
    
    def remove_prescription(self, prescription_id):
        return self.prescription.delete_prescription(prescription_id)
    
    def cancel_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(appointment_id=appointment_id, status=appointmentStatus['CANCELLED'])
    
    def complete_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(appointment_id=appointment_id, status=appointmentStatus['COMPLETED'])