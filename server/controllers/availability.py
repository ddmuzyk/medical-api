from flask import Blueprint, request, jsonify, g
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from middleware.auth import role_required, token_required
from constants import UserRole, AppointmentStatus
from services.notification_service import NotificationService

bp = Blueprint('availability', __name__)

@bp.post('/')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def create_doctor_availability():
    data = request.get_json() or {}
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            user = user_manager.get_doctor(data.get('doctor_id'))
            isAdmin = g.role == UserRole['ADMIN']

            if not user or (not isAdmin and user['user_id'] != g.user_id):
                return jsonify({"status": "error", "message": "Unauthorized to create availability for this doctor"}), 403

            availability_id = appointment_manager.create_doctor_availability(**data)  
        return jsonify({"status": "success", "availability_id": availability_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
@token_required
def get_doctor_availability(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": "No doctor ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(doctor_id)
        return jsonify({"status": "success", "availability": availability}), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/')
@token_required
def get_availabilities_by_specialization_and_date():
    specialization = request.args.get('specialization')
    date = request.args.get('date')
    if not specialization or not date:
        return jsonify({"status": "error", "message": "Specialization and date are required"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availabilities = appointment_manager.get_availabilities_by_specialization_and_date(specialization, date)

            if not availabilities:
                return jsonify({"status": "error", "message": "No availabilities found"}), 404
            
            structured_availabilities = [
                {
                    "availability_id": a['availability_id'],
                    "start_time": str(a['start_time']),
                    "end_time": str(a['end_time']),
                    "is_available": a['is_available'],
                    "doctor": {
                        "doctor_id": a['doctor_id'],
                        "first_name": a['first_name'],
                        "last_name": a['last_name'],
                        "specialization": a['specialization'],
                        "license_number": a['license_number'],
                    }
                }
                for a in availabilities
            ]
        return jsonify({"status": "success", "availabilities": structured_availabilities}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:availability_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def update_doctor_availability(availability_id):
    data = request.get_json() or {}
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(availability_id)
            user = user_manager.get_doctor(availability['doctor_id']) if availability else None
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = user and user['user_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this availability"}), 403

            updated_availability_id = appointment_manager.change_doctor_availability(availability_id=availability_id, **data)
        return jsonify({"status": "success", "updated_availability_id": updated_availability_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:availability_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def delete_doctor_availability(availability_id):
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(availability_id)
            isSelfDeletion = availability and availability['doctor_id'] == g.user_id
            isAdmin = g.role == UserRole['ADMIN']

            if not availability or (not isAdmin and not isSelfDeletion):
                return jsonify({"status": "error", "message": "Unauthorized to modify this availability"}), 403
            
            appointment = appointment_manager.get_appointment_by_availability(availability_id)
            if appointment:
                appointment_manager.cancel_appointment(appointment['id'])
                user_manager = UserQueryManager(cur)
                user_id = user_manager.get_patient(appointment['patient_id'])['user_id']
                doctor_name = user_manager.get_doctor(appointment['doctor_id'])['first_name']
                NotificationService.notify_appointment_status_changed(
                    cur,
                    user_id=user_id,
                    doctor_name=doctor_name,
                    status=AppointmentStatus.CANCELLED.value
                )

            deleted_availability = appointment_manager.delete_doctor_availability(availability_id)
            if not deleted_availability:
                return jsonify({"status": "error", "message": "Availability not found"}), 404
        return jsonify({"status": "success", "deleted_availability": deleted_availability}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500