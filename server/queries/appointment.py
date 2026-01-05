from utils.queries import create_placeholder_data
from constants import AppointmentTables, AppointmentStatus, UserTables
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
            INSERT INTO {AppointmentTables.APPOINTMENTS.value} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def update_appointment_status(self, **appointment_data):
        status, appointment_id = appointment_data.get('status'), appointment_data.get('appointment_id')
        
        self.cur.execute(
            f"""
            UPDATE {AppointmentTables.APPOINTMENTS.value}
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
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE id = %s
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()
    
    def get_appointments_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE patient_id = %s
            ORDER BY appointment_date DESC
            """,
            (patient_id,)
        )
        return self.cur.fetchall()
    
    def get_upcoming_appointments_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE patient_id = %s 
            AND appointment_date > NOW()
            AND status = %s
            ORDER BY appointment_date ASC
            """,
            (patient_id, AppointmentStatus.SCHEDULED.value)
        )
        return self.cur.fetchall()

    def get_past_appointments_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE patient_id = %s 
            AND (appointment_date < NOW() OR status IN (%s, %s))
            ORDER BY appointment_date DESC
            """,
            (patient_id, AppointmentStatus.COMPLETED.value, AppointmentStatus.CANCELLED.value)
        )
        return self.cur.fetchall()
    
    def get_appointments_by_doctor(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE doctor_id = %s
            ORDER BY appointment_date DESC
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def get_appointment_by_availability(self, availability_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.APPOINTMENTS.value}
            WHERE availability_id = %s
            """,
            (availability_id,)
        )
        return self.cur.fetchone()
    
    def delete_appointment(self, appointment_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.APPOINTMENTS.value} WHERE id = %s
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
            SELECT 1 FROM {AppointmentTables.DOCTOR_AVAILABILITY.value}
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
            INSERT INTO {AppointmentTables.DOCTOR_AVAILABILITY.value} ({columns})
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
            UPDATE {AppointmentTables.DOCTOR_AVAILABILITY.value}
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
            SELECT * FROM {AppointmentTables.DOCTOR_AVAILABILITY.value}
            WHERE doctor_id = %s AND is_available = TRUE
            ORDER BY start_time
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def get_availabilities_by_specialization_and_date(self, specialization, date):
        self.cur.execute(
            f"""
            SELECT 
            da.id as availability_id,
            da.doctor_id,
            da.start_time,
            da.end_time,
            da.is_available,
            d.first_name,
            d.last_name,
            d.specialization,
            d.license_number 
            FROM {AppointmentTables.DOCTOR_AVAILABILITY.value} da
            JOIN {UserTables.DOCTORS.value} d ON da.doctor_id = d.id
            WHERE d.specialization = %s
              AND DATE(da.start_time) = %s
              AND da.is_available = TRUE
            ORDER BY da.start_time
            """,
            (specialization, date)
        )
        return self.cur.fetchall()
    
    def get_availability_by_id(self, availability_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.DOCTOR_AVAILABILITY.value}
            WHERE id = %s
            """,
            (availability_id,)
        )
        return self.cur.fetchone()
    
    def delete_doctor_availability(self, availability_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.DOCTOR_AVAILABILITY.value} WHERE id = %s
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
        
        if not availability['is_available']:
            raise ValueError("The selected availability slot is not available")
        
        appointment_data.update({
            "status": AppointmentStatus.SCHEDULED.value,
            "appointment_date": availability['start_time']
        })
        
        appointment_id = self.appointment.insert_appointment(**appointment_data)

         # Mark the availability slot as unavailable
        if appointment_id:
            self.set_availability_unavailable(appointment_data.get('availability_id'))

        return appointment_id

    def create_doctor_availability(self, **availability_data):
        return self.availability.insert_doctor_availability(**availability_data)
    
    def get_doctor_availability(self, doctor_id):
        return self.availability.get_doctor_availability(doctor_id)
    
    def get_availability_by_id(self, availability_id):
        return self.availability.get_availability_by_id(availability_id)
    
    def get_appointment(self, appointment_id):
        return self.appointment.get_appointment(appointment_id)
    
    def get_appointments_by_patient(self, patient_id):
        return self.appointment.get_appointments_by_patient(patient_id)
    
    def get_upcoming_appointments_by_patient(self, patient_id):
        return self.appointment.get_upcoming_appointments_by_patient(patient_id)
    
    def get_past_appointments_by_patient(self, patient_id):
        return self.appointment.get_past_appointments_by_patient(patient_id)
    
    def get_appointments_by_doctor(self, doctor_id):
        return self.appointment.get_appointments_by_doctor(doctor_id)
    
    def get_appointment_by_availability(self, availability_id):
        return self.appointment.get_appointment_by_availability(availability_id)
    
    def get_availabilities_by_specialization_and_date(self, specialization, date):
        return self.availability.get_availabilities_by_specialization_and_date(specialization, date)
    
    def change_appointment_status(self, **appointment_data):
        return self.appointment.update_appointment_status(**appointment_data)
    
    def change_doctor_availability(self, **availability_data):
        return self.availability.update_doctor_availability(**availability_data)
    
    def remove_doctor_availability(self, availability_id):
        return self.availability.delete_doctor_availability(availability_id)
    
    def cancel_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(
            appointment_id=appointment_id, 
            status=AppointmentStatus.CANCELLED.value
        )
    
    def complete_appointment(self, appointment_id):
        return self.appointment.update_appointment_status(appointment_id=appointment_id, status=AppointmentStatus.COMPLETED.value)
    
    def delete_appointment(self, appointment_id):
        return self.appointment.delete_appointment(appointment_id)
    
    def delete_doctor_availability(self, availability_id):
        return self.availability.delete_doctor_availability(availability_id)
    
    def set_availability_unavailable(self, availability_id):
        return self.availability.update_doctor_availability(availability_id=availability_id, is_available=False)
    
    def set_availability_available(self, availability_id):
        return self.availability.update_doctor_availability(availability_id=availability_id, is_available=True)
    
    