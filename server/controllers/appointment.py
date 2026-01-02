from flask import Blueprint, request, jsonify, g
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from constants import userRole
from middleware.auth import role_required, token_required

bp = Blueprint('appointment', __name__)

@bp.post('/')
@token_required
def create_appointment():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment_id = appointment_manager.create_appointment(**data)  
        return jsonify({"status": "success", "appointment_id": appointment_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/<int:appointment_id>')
def get_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if g.role == userRole['USER'] and appointment['patient_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403
            if g.role == userRole['DOCTOR'] and appointment['doctor_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
        return jsonify({"status": "success", "appointment": appointment}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>')
def get_appointments_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            user_manager = UserQueryManager(cur)
            appointments = appointment_manager.get_appointments_by_patient(patient_id)
            patient = user_manager.get_patient(patient_id)

            if g.role == userRole['USER'] and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403
            if g.role == userRole['DOCTOR']:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "appointments": appointments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
def get_appointments_by_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": "No doctor ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointments = appointment_manager.get_appointments_by_doctor(doctor_id)
        return jsonify({"status": "success", "appointments": appointments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:appointment_id>/status')
def change_appointment_status(appointment_id):
    data = request.get_json() or {}
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            updated_appointment_id = appointment_manager.change_appointment_status(appointment_id=appointment_id, **data)
        return jsonify({"status": "success", "updated_appointment_id": updated_appointment_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:appointment_id>')
def delete_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            deleted_appointment = appointment_manager.delete_appointment(appointment_id)
            if not deleted_appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
        return jsonify({"status": "success", "deleted_appointment": deleted_appointment}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500