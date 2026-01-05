from flask import Blueprint, request, jsonify, g
from queries.prescription import PrescriptionQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from constants import UserRole
from middleware.auth import token_required, role_required
from services.notification_service import NotificationService

bp = Blueprint('prescription', __name__)

@bp.post('/create')
@role_required(UserRole.DOCTOR.value, UserRole.ADMIN.value)
def create_prescription():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            prescription_id = prescription_manager.create_prescription(**data)  

            if prescription_id:
                user_manager = UserQueryManager(cur)
                patient = user_manager.get_patient(data.get('patient_id'))
                doctor = user_manager.get_doctor(data.get('doctor_id'))
                NotificationService.notify_prescription_created(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name']
                )
        return jsonify({"status": "success", "prescription_id": prescription_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/<int:prescription_id>')
@token_required
def get_prescription(prescription_id):
    if not prescription_id:
        return jsonify({"status": "error", "message": "No prescription ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            prescription_manager = PrescriptionQueryManager(cur)
            user_manager = UserQueryManager(cur)
            prescription = prescription_manager.get_prescription(prescription_id)

            if not prescription:
                return jsonify({"status": "error", "message": "Prescription not found"}), 404

            if g.role == UserRole.USER.value:
                patient = user_manager.get_patient(prescription['patient_id'])
                if patient['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value:
                doctor = user_manager.get_doctor(prescription['doctor_id'])
                if doctor['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "prescription": prescription}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>')
@role_required(UserRole.ADMIN.value, UserRole.USER.value)
def get_prescriptions_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)

            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            prescription_manager = PrescriptionQueryManager(cur)
            prescriptions = prescription_manager.get_prescriptions_by_patient(patient_id)
        return jsonify({"status": "success", "prescriptions": prescriptions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def get_prescriptions_by_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": "No doctor ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor(doctor_id)

            if g.role == UserRole.DOCTOR.value and doctor['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            prescription_manager = PrescriptionQueryManager(cur)
            prescriptions = prescription_manager.get_prescriptions_by_doctor(doctor_id)
        return jsonify({"status": "success", "prescriptions": prescriptions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:prescription_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def delete_prescription(prescription_id):
    if not prescription_id:
        return jsonify({"status": "error", "message": "No prescription ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            prescription_manager = PrescriptionQueryManager(cur)
            prescription = prescription_manager.get_prescription(prescription_id)
            if not prescription:
                return jsonify({"status": "error", "message": "Prescription not found"}), 404
            doctor = user_manager.get_doctor(prescription['doctor_id']) if prescription else None

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfDeletion = doctor and doctor['user_id'] == g.user_id
            if not isAdmin and not isSelfDeletion:
                return jsonify({"status": "error", "message": "Unauthorized to delete this prescription"}), 403

            deleted_prescription = prescription_manager.delete_prescription(prescription_id)
            if not deleted_prescription:
                return jsonify({"status": "error", "message": "Prescription not found"}), 404
        return jsonify({"status": "success", "deleted_prescription": deleted_prescription}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500