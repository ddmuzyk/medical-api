from utils.queries import create_placeholder_data
from constants import AppointmentTables, AppointmentStatus
import datetime as dt

class AppointmentQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def insert_appointment(self, **appointment_data):
        allowed_columns = {'patient_id', 'doctor_id', 'availability_id', 'appointment_date', 'status', 'created_at'}
        columns, placeholders, values = create_placeholder_data({
            **appointment_data,
            "created_at": dt.datetime.now()
        }, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {AppointmentTables.APPOINTMENTS} ({columns})
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
            UPDATE {AppointmentTables.APPOINTMENTS}
            SET status = %s
            WHERE id = %s
            RETURNING id
            """,
            (status, appointment_id)
        )
        return self.cur.fetchone()['id']
    
    def get_appointment(self, appointment_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS}
            WHERE id = %s
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()
    
    def get_appointments_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS}
            WHERE patient_id = %s
            ORDER BY appointment_date DESC
            """,
            (patient_id,)
        )
        return self.cur.fetchall()
    
    def get_appointments_by_doctor(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS}
            WHERE doctor_id = %s
            ORDER BY appointment_date DESC
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def delete_appointment(self, appointment_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.APPOINTMENTS} WHERE id = %s
            RETURNING id
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()['id']
    
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
            SELECT 1 FROM {AppointmentTables.DOCTOR_AVAILABILITY}
            WHERE doctor_id = %s AND
                  ((start_time, end_time) OVERLAPS (%s, %s))
            """,
            (doctor_id, start_time, end_time)
        )
        if self.cur.fetchone():
            raise ValueError("The specified time slot overlaps with existing availability")
        
        allowed_columns = {'doctor_id', 'is_available', 'start_time', 'end_time'}
        columns, placeholders, values = create_placeholder_data(availability_data, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {AppointmentTables.DOCTOR_AVAILABILITY} ({columns})
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
            UPDATE {AppointmentTables.DOCTOR_AVAILABILITY}
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
            SELECT * FROM {AppointmentTables.DOCTOR_AVAILABILITY}
            WHERE doctor_id = %s AND is_available = TRUE
            ORDER BY start_time
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def get_availability_by_id(self, availability_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.DOCTOR_AVAILABILITY}
            WHERE id = %s
            """,
            (availability_id,)
        )
        return self.cur.fetchone()
    
    def delete_doctor_availability(self, availability_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.DOCTOR_AVAILABILITY} WHERE id = %s
            RETURNING id
            """,
            (availability_id,)
        )
        return self.cur.fetchone()['id']
    


class AppointmentQueryManager:
    def __init__(self, cursor):
        self.cur = cursor
        self.appointment = AppointmentQueryHelper(cursor)
        self.availability = AvailabilityQueryHelper(cursor)

    def create_appointment(self, **appointment_data):
        patient_id = appointment_data.get('patient_id')
        doctor_id = appointment_data.get('doctor_id')
        
        self.cur.execute("SELECT 1 FROM patients WHERE id = %s", (patient_id,))
        if not self.cur.fetchone():
            raise ValueError(f"Patient with id {patient_id} does not exist")

        self.cur.execute("SELECT 1 FROM doctors WHERE id = %s", (doctor_id,))
        if not self.cur.fetchone():
            raise ValueError(f"Doctor with id {doctor_id} does not exist")
        
        availability = self.availability.get_availability_by_id(appointment_data.get('availability_id'))
        if not availability:
            raise ValueError(f"Availability with id {appointment_data.get('availability_id')} does not exist")
        
        appointment_data.update({
            "status": AppointmentStatus['SCHEDULED'],
            "appointment_date": availability['start_time']
        })
        
        return self.appointment.insert_appointment(**appointment_data)

    def create_doctor_availability(self, **availability_data):
        return self.availability.insert_doctor_availability(**availability_data)
    
    def get_doctor_availability(self, doctor_id):
        return self.availability.get_doctor_availability(doctor_id)
    
    def get_appointment(self, appointment_id):
        return self.appointment.get_appointment(appointment_id)
    
    def get_appointments_by_patient(self, patient_id):
        return self.appointment.get_appointments_by_patient(patient_id)
    
    def get_appointments_by_doctor(self, doctor_id):
        return self.appointment.get_appointments_by_doctor(doctor_id)
    
    def change_appointment_status(self, **appointment_data):
        return self.appointment.update_appointment_status(**appointment_data)
    
    def change_doctor_availability(self, **availability_data):
        return self.availability.update_doctor_availability(**availability_data)
    
    def remove_doctor_availability(self, availability_id):
        return self.availability.delete_doctor_availability(availability_id)
    
    def cancel_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(appointment_id=appointment_id, status=AppointmentStatus['CANCELLED'])
    
    def complete_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(appointment_id=appointment_id, status=AppointmentStatus['COMPLETED'])
    
    def delete_appointment(self, appointment_id):
        return self.appointment.delete_appointment(appointment_id)
    
    def delete_doctor_availability(self, availability_id):
        return self.availability.delete_doctor_availability(availability_id)
    
    