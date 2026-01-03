from flask import Blueprint, request, jsonify
from queries.user import UserQueryManager
from constants import errorMessages, specializations, userRole
from db_connection import DbPool
from middleware.auth import role_required, token_required

bp = Blueprint('doctor', __name__)

@bp.get('/<int:doctor_id>')
def get_doctor(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": errorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor(doctor_id)
            if not doctor:
                return jsonify({"status": "error", "message": errorMessages["USER_NOT_FOUND"]}), 404
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
@role_required(userRole['ADMIN'], userRole['DOCTOR'])
def update_doctor(doctor_id):
    data = request.get_json() or {}
    if not doctor_id:
        return jsonify({"status": "error", "message": errorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            updated_doctor_id = user_manager.update_doctor(doctor_id=doctor_id, **data)
        return jsonify({"status": "success", "updated_doctor_id": updated_doctor_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500