from flask import Blueprint, request, jsonify, g
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from constants import UserRole, AppointmentStatus
from middleware.auth import role_required, token_required
from services.notification_service import NotificationService

bp = Blueprint('appointment', __name__)

@bp.post('/')
@token_required
def create_appointment():
    data = request.get_json() or {}
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)

            if g.role == UserRole.USER.value:
                patient = user_manager.get_patient(data.get('patient_id'))
                if patient['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value:
                doctor = user_manager.get_doctor(data.get('doctor_id'))
                if doctor['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

            appointment_id = appointment_manager.create_appointment(**data)

            if appointment_id and g.role != UserRole.USER.value:
                appointment = appointment_manager.get_appointment(appointment_id)
                patient = user_manager.get_patient(appointment['patient_id'])
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                NotificationService.notify_appointment_created(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name'],
                    appointment_date=appointment['appointment_date']
                )

        return jsonify({"status": "success", "appointment_id": appointment_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/<int:appointment_id>')
@token_required
def get_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if g.role == UserRole.USER.value and appointment['patient_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value and appointment['doctor_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
        return jsonify({"status": "success", "appointment": appointment}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>')
@role_required(UserRole.ADMIN.value, UserRole.USER.value)
def get_appointments_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            user_manager = UserQueryManager(cur)
            appointments = appointment_manager.get_appointments_by_patient(patient_id)
            patient = user_manager.get_patient(patient_id)

            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "appointments": appointments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>/upcoming')
@role_required(UserRole.ADMIN.value, UserRole.USER.value)
def get_upcoming_appointments_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)

            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            appointment_manager = AppointmentQueryManager(cur)
            appointments = appointment_manager.get_upcoming_appointments_by_patient(patient_id)

        return jsonify({"status": "success", "appointments": appointments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:patient_id>/past')
@token_required
def get_past_appointments_by_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": "No patient ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)

            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            appointment_manager = AppointmentQueryManager(cur)
            appointments = appointment_manager.get_past_appointments_by_patient(patient_id)

        return jsonify({"status": "success", "appointments": appointments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
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
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def change_appointment_status(appointment_id):
    data = request.get_json() or {}
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = appointment and appointment['doctor_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this appointment"}), 403

            updated_appointment_id = appointment_manager.change_appointment_status(appointment_id=appointment_id, status=data.get('status'))

            if updated_appointment_id and g.role != UserRole.USER.value:
                user_manager = UserQueryManager(cur)
                patient = user_manager.get_patient(appointment['patient_id'])
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                NotificationService.notify_appointment_status_changed(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name'],
                    status=data.get('status')
                )
        return jsonify({"status": "success", "updated_appointment_id": updated_appointment_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:appointment_id>/complete')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def complete_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = appointment and appointment['doctor_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this appointment"}), 403

            completed_appointment_id = appointment_manager.complete_appointment(appointment_id)

            if completed_appointment_id and g.role != UserRole.USER.value:
                user_manager = UserQueryManager(cur)
                patient = user_manager.get_patient(appointment['patient_id'])
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                NotificationService.notify_appointment_status_changed(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name'],
                    status=AppointmentStatus.COMPLETED.value
                )
        return jsonify({"status": "success", "completed_appointment_id": completed_appointment_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:appointment_id>/cancel')
@token_required
def cancel_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if g.role == UserRole.USER.value and appointment['patient_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value and appointment['doctor_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            cancelled_appointment_id = appointment_manager.cancel_appointment(appointment_id)

            if cancelled_appointment_id and g.role != UserRole.USER.value:
                user_manager = UserQueryManager(cur)
                patient = user_manager.get_patient(appointment['patient_id'])
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                NotificationService.notify_appointment_status_changed(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name'],
                    status=AppointmentStatus.CANCELLED.value
                )
        return jsonify({"status": "success", "cancelled_appointment_id": cancelled_appointment_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:appointment_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def delete_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = appointment and appointment['doctor_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this appointment"}), 403
        
            deleted_appointment = appointment_manager.delete_appointment(appointment_id)
            if not deleted_appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
        return jsonify({"status": "success", "deleted_appointment": deleted_appointment}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500