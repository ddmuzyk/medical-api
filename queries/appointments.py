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