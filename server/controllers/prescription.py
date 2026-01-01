from flask import Blueprint, request, jsonify
from queries.prescription import PrescriptionQueryManager
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('prescription', __name__)

@bp.post('/create')
def create_prescription():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            prescription_id = prescription_manager.create_prescription(**data)  
        return jsonify({"status": "success", "prescription_id": prescription_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/<int:prescription_id>')
def get_prescription(prescription_id):
    if not prescription_id:
        return jsonify({"status": "error", "message": "No prescription ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            prescription = prescription_manager.get_prescription(prescription_id)
            if not prescription:
                return jsonify({"status": "error", "message": "Prescription not found"}), 404
        return jsonify({"status": "success", "prescription": prescription}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>')
def get_prescriptions_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            prescriptions = prescription_manager.get_prescriptions_by_patient(patient_id)
        return jsonify({"status": "success", "prescriptions": prescriptions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
def get_prescriptions_by_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": "No doctor ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            prescriptions = prescription_manager.get_prescriptions_by_doctor(doctor_id)
        return jsonify({"status": "success", "prescriptions": prescriptions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:prescription_id>')
def delete_prescription(prescription_id):
    if not prescription_id:
        return jsonify({"status": "error", "message": "No prescription ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            deleted_prescription = prescription_manager.delete_prescription(prescription_id)
            if not deleted_prescription:
                return jsonify({"status": "error", "message": "Prescription not found"}), 404
        return jsonify({"status": "success", "deleted_prescription": deleted_prescription}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500