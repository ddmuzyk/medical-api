from utils.queries import create_placeholder_data
from constants import appointmentTables
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
        return self.cur.fetchone()[0]
    
    def insert_doctor_availability(self, **availability_data):
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
        return self.cur.fetchone()[0]
    
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
        return self.cur.fetchone()[0]
    
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
        return self.cur.fetchone()[0]
    
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
        return self.cur.fetchone()[0]
    
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
        return self.cur.fetchone()[0]
    
class AppointmentQueryManager:
    def __init__(self, cursor):
        self.helper = AppointmentQueryHelper(cursor)

    def create_appointment(self, **appointment_data):
        return self.helper.insert_appointment(**appointment_data)

    def create_doctor_availability(self, **availability_data):
        return self.helper.insert_doctor_availability(**availability_data)

    def create_prescription(self, **prescription_data):
        prescription_id = self.helper.insert_prescription(**prescription_data)
        if not prescription_id:
            raise Exception("Failed to create prescription")
        
        prescription_item_id = self.helper.insert_prescription_item(
            prescription_id=prescription_id,
            medication_name=prescription_data.get('medication_name'),
            dosage=prescription_data.get('dosage'),
            instructions=prescription_data.get('instructions')
        )
        if not prescription_item_id:
            raise Exception("Failed to create prescription item")
        return prescription_id
    
    def change_appointment_status(self, **appointment_data):
        return self.helper.update_appointment_status(**appointment_data)
    
    def change_doctor_availability(self, **availability_data):
        return self.helper.update_doctor_availability(**availability_data)