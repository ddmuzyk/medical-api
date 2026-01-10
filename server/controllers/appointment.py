from flask import Blueprint, request, jsonify, g
import logging
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from constants import UserRole, AppointmentStatus
from middleware.auth import role_required, token_required
from services.notification_service import NotificationService

bp = Blueprint('appointment', __name__)
logger = logging.getLogger(__name__)

@bp.post('/')
@token_required
def create_appointment():
    data = request.get_json() or {}
    # Validate required fields
    required = []
    if not data.get('doctor_id'):
        required.append('doctor_id')
    if not data.get('availability_id'):
        required.append('availability_id')

    if required:
        msg = f"Missing required fields: {', '.join(required)}"
        logger.warning("create_appointment bad request: %s", msg)
        return jsonify({"status": "error", "message": msg}), 400

    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)

            # If the caller is a patient, ensure they have a patient profile
            if g.role == UserRole.USER.value:
                patient = user_manager.get_patient_by_user_id(g.user_id)
                if not patient:
                    logger.warning("create_appointment: patient profile not found for user_id=%s", g.user_id)
                    return jsonify({"message": "Patient profile not found for current user"}), 400
                # ensure provided patient_id (if any) matches the authenticated user's patient id
                if data.get('patient_id') and int(data.get('patient_id')) != int(patient['id']):
                    logger.warning("create_appointment: patient_id mismatch user_id=%s payload_patient_id=%s", g.user_id, data.get('patient_id'))
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
                # set patient_id to the authenticated patient's id to be safe
                data['patient_id'] = patient['id']

            # If the caller is a doctor, validate doctor ownership
            if g.role == UserRole.DOCTOR.value:
                # if doctor_id provided, ensure it exists and belongs to this user
                doctor = user_manager.get_doctor(data.get('doctor_id'))
                if not doctor:
                    logger.warning("create_appointment: doctor not found doctor_id=%s", data.get('doctor_id'))
                    return jsonify({"message": "Doctor not found"}), 404
                if doctor.get('user_id') != g.user_id:
                    logger.warning("create_appointment: doctor ownership mismatch user_id=%s doctor_user_id=%s", g.user_id, doctor.get('user_id'))
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

            # Validate doctor exists (for non-doctor callers as well)
            doctor_check = user_manager.get_doctor(data.get('doctor_id'))
            if not doctor_check:
                logger.warning("create_appointment: doctor not found doctor_id=%s", data.get('doctor_id'))
                return jsonify({"message": "Doctor not found"}), 404

            # Validate availability exists and belongs to doctor
            availability = appointment_manager.get_availability_by_id(data.get('availability_id'))
            if not availability:
                logger.warning("create_appointment: availability not found availability_id=%s", data.get('availability_id'))
                return jsonify({"message": "Availability not found"}), 404

            # Ensure availability belongs to specified doctor
            if str(availability.get('doctor_id')) != str(data.get('doctor_id')):
                logger.warning("create_appointment: availability-doctor mismatch availability_id=%s availability_doctor=%s payload_doctor=%s", data.get('availability_id'), availability.get('doctor_id'), data.get('doctor_id'))
                return jsonify({"status": "error", "message": "Availability does not belong to the specified doctor"}), 400

            # Delegate to query manager to create the appointment (will also check availability availability.is_available)
            appointment_id = appointment_manager.create_appointment(**data)

            # After successful creation, notify if appropriate
            if appointment_id and g.role != UserRole.USER.value:
                appointment = appointment_manager.get_appointment(appointment_id)
                if appointment:
                    patient = user_manager.get_patient(appointment.get('patient_id'))
                    doctor = user_manager.get_doctor(appointment.get('doctor_id'))
                    if patient and doctor:
                        NotificationService.notify_appointment_created(
                            cur,
                            user_id=patient.get('user_id'),
                            doctor_name=doctor.get('last_name'),
                            appointment_date=appointment.get('appointment_date').strftime('%d.%m.%Y') if appointment.get('appointment_date') else ''
                        )

        return jsonify({"status": "success", "appointment_id": appointment_id}), 201
    except ValueError as ve:
        # Known validation errors from query layer
        logger.warning("create_appointment validation error: %s", str(ve))
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        # Unexpected errors
        logger.exception("create_appointment unexpected error")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/<int:appointment_id>')
@token_required
def get_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)
            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404

            if g.role == UserRole.USER.value:
                patient = user_manager.get_patient(appointment['patient_id'])
                if patient['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value:
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                if doctor['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

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
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)

            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

            appointment_manager = AppointmentQueryManager(cur)
            appointments = appointment_manager.get_appointments_by_patient(patient_id)

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
    
@bp.patch('/<int:appointment_id>/complete')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def complete_appointment(appointment_id):
    if not appointment_id:
        return jsonify({"status": "error", "message": "No appointment ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = appointment['doctor_id'] == g.user_id

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
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if g.role == UserRole.USER.value:
                patient = user_manager.get_patient(appointment['patient_id'])
                if patient['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value:
                doctor = user_manager.get_doctor(appointment['doctor_id'])
                if doctor['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

            cancelled_appointment_id = appointment_manager.cancel_appointment(appointment_id)

            if cancelled_appointment_id:
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
            user_manager = UserQueryManager(cur)
            appointment = appointment_manager.get_appointment(appointment_id)

            if not appointment:
                return jsonify({"status": "error", "message": "Appointment not found"}), 404
            
            doctor = user_manager.get_doctor(appointment['doctor_id'])
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = doctor['user_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this appointment" }), 403
        
            deleted_appointment = appointment_manager.delete_appointment(appointment_id)

            if deleted_appointment:
                patient = user_manager.get_patient(appointment['patient_id'])
                NotificationService.notify_appointment_status_changed(
                    cur,
                    user_id=patient['user_id'],
                    doctor_name=doctor['last_name'],
                    status=AppointmentStatus.CANCELLED.value
                )

        return jsonify({"status": "success", "deleted_appointment": deleted_appointment}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500