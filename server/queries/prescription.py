from utils.queries import create_placeholder_data
from constants import AppointmentTables
import datetime as dt

class PrescriptionQueryHelper:
    def __init__(self, cursor):
        self.cur = cursor

    def get_prescription_by_id(self, prescription_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.PRESCRIPTIONS}
            WHERE id = %s
            """,
            (prescription_id,)
        )
        return self.cur.fetchone()
    
    def get_prescriptions_by_patient(self, patient_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.PRESCRIPTIONS}
            WHERE patient_id = %s
            ORDER BY issued_at DESC
            """,
            (patient_id,)
        )
        return self.cur.fetchall()

    def get_prescription_by_appointment(self, appointment_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.PRESCRIPTIONS}
            WHERE appointment_id = %s
            """,
            (appointment_id,)
        )
        return self.cur.fetchone()
    
    def get_prescriptions_by_doctor(self, doctor_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.PRESCRIPTIONS}
            WHERE doctor_id = %s
            ORDER BY issued_at DESC
            """,
            (doctor_id,)
        )
        return self.cur.fetchall()
    
    def get_prescription_items(self, prescription_id):
        self.cur.execute(
            f"""
            SELECT * FROM {AppointmentTables.PRESCRIPTION_ITEMS}
            WHERE prescription_id = %s
            """,
            (prescription_id,)
        )
        return self.cur.fetchall()
    
    def insert_prescription(self, **prescription_data):
        allowed_columns = {'appointment_id', 'issued_at', 'patient_id', 'doctor_id', 'notes'}
        columns, placeholders, values = create_placeholder_data({
            **prescription_data,
            "issued_at": prescription_data.get("issued_at", dt.datetime.now())
        }, allowed_columns)

        self.cur.execute(
            f"""
            INSERT INTO {AppointmentTables.PRESCRIPTIONS} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def insert_prescription_items(self, prescription_id, prescription_items):
        prescription_values = []
        allowed_columns = {'prescription_id', 'medication_name', 'dosage', 'instructions'}
        for item in prescription_items:
            columns, placeholders, values = create_placeholder_data({**item, "prescription_id": prescription_id}, allowed_columns)
            prescription_values.append(tuple(values))

        self.cur.execute(
            f"""
            INSERT INTO {AppointmentTables.PRESCRIPTION_ITEMS} ({columns})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(values)
        )
        return self.cur.fetchone()['id']
    
    def delete_prescription(self, prescription_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.PRESCRIPTIONS} WHERE id = %s
            RETURNING id
            """,
            (prescription_id,)
        )
        return self.cur.fetchone()['id']
    
    def delete_prescription_item(self, prescription_item_id):
        self.cur.execute(
            f"""
            DELETE FROM {AppointmentTables.PRESCRIPTION_ITEMS} WHERE id = %s
            RETURNING id
            """,
            (prescription_item_id,)
        )
        return self.cur.fetchone()['id']
    
class PrescriptionQueryManager:
    def __init__(self, cursor):
        self.cur = cursor
        self.prescription = PrescriptionQueryHelper(cursor)

    def create_prescription(self, **prescription_data):
        prescription_id = self.prescription.insert_prescription(**prescription_data)
        if not prescription_id:
            raise Exception("Failed to create prescription")
        
        prescription_item_id = self.prescription.insert_prescription_items(
            prescription_id,
            prescription_items=prescription_data.get('prescription_items', []),
        )

        if not prescription_item_id:
            raise Exception("Failed to create prescription item")
        return prescription_id
    
    def get_prescription(self, prescription_id):
        return self.prescription.get_prescription_by_id(prescription_id)
    
    def get_prescriptions_by_patient(self, user_id):
        return self.prescription.get_prescriptions_by_patient(user_id)
    
    def get_prescriptions_by_doctor(self, doctor_id):
        return self.prescription.get_prescriptions_by_doctor(doctor_id)
    
    def remove_prescription(self, prescription_id):
        return self.prescription.delete_prescription(prescription_id)
    
    def delete_prescription(self, prescription_id):
        return self.prescription.delete_prescription(prescription_id)
    
    def delete_prescription_item(self, prescription_item_id):
        self.prescription.delete_prescription_item(prescription_item_id)