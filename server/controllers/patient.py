from flask import Blueprint, request, jsonify, g
from queries.user import UserQueryManager
from constants import ErrorMessages, UserRole
from db_connection import DbPool
from middleware.auth import role_required, token_required

bp = Blueprint('patient', __name__)

@bp.get('/<int:patient_id>')
@token_required
def get_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)
            if not patient:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
            
            if g.role == UserRole.USER.value:
                if patient['user_id'] != g.user_id:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403
            elif g.role == UserRole.DOCTOR.value:
                doctor = user_manager.get_doctor_by_user_id(g.user_id)
                if not doctor:
                    return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "patient": patient}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:patient_id>')
@role_required(UserRole.ADMIN.value, UserRole.USER.value)
def update_patient(patient_id):
    data = request.get_json() or {}
    if not patient_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)

            if not patient:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = patient['user_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this patient"}), 403

            updated_patient_id = user_manager.update_patient(patient_id=patient_id, **data)
        return jsonify({"status": "success", "updated_patient_id": updated_patient_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500