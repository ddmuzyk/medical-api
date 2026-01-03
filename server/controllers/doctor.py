from flask import Blueprint, request, jsonify, g
from queries.user import UserQueryManager
from constants import ErrorMessages, specializations, UserRole
from db_connection import DbPool
from middleware.auth import role_required

bp = Blueprint('doctor', __name__)

@bp.get('/<int:doctor_id>')
def get_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor(doctor_id)
            if not doctor:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
        return jsonify({"status": "success", "doctor": doctor}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/specializations')
def get_all_specializations():
    try:
        return jsonify({"status": "success", "specializations": list(specializations.values())}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/specializations/<string:specialization>')
def get_doctors_by_specialization(specialization):
    if not specialization:
        return jsonify({"status": "error", "message": "No specialization provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctors = user_manager.get_doctors_by_specialization(specialization)
        return jsonify({"status": "success", "doctors": doctors}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:doctor_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def update_doctor(doctor_id):
    data = request.get_json() or {}
    if not doctor_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor(doctor_id)

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = doctor and doctor['user_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this doctor"}), 403

            updated_doctor_id = user_manager.update_doctor(doctor_id=doctor_id, **data)
        return jsonify({"status": "success", "updated_doctor_id": updated_doctor_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:doctor_id>')
@role_required(UserRole.ADMIN.value)
def delete_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor(doctor_id)
            isAdmin = g.role == UserRole.ADMIN.value
            isSelfDeletion = doctor and doctor['user_id'] == g.user_id

            if not isAdmin and not isSelfDeletion:
                return jsonify({"status": "error", "message": "Unauthorized to delete this doctor"}), 403

            deleted_doctor = user_manager.delete_user(doctor['user_id']) if doctor else None
            if not deleted_doctor:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
        return jsonify({"status": "success", "deleted_doctor_id": deleted_doctor}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500