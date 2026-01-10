from flask import Blueprint, request, jsonify, g
from queries.user import UserQueryManager
from constants import ErrorMessages
from db_connection import DbPool
from psycopg2 import errors
from middleware.auth import token_required, role_required
from constants import UserRole

bp = Blueprint('user', __name__)

@bp.get('/pending')
@role_required(UserRole.ADMIN.value)
def get_pending_users():
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            pending_users = user_manager.get_pending_users()
        return jsonify({"status": "success", "pending_users": pending_users}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/patient/<int:user_id>')
@role_required(UserRole.ADMIN.value, UserRole.USER.value)
def get_patient(user_id):
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient_by_user_id(user_id)

            if not patient:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
            if g.role == UserRole.USER.value and patient['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "patient": patient}), 200
    except errors.NoDataFound:
        return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:user_id>')
@role_required(UserRole.ADMIN.value, UserRole.DOCTOR.value)
def get_doctor(user_id):
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            doctor = user_manager.get_doctor_by_user_id(user_id)

            if not doctor:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
            if g.role == UserRole.DOCTOR.value and doctor['user_id'] != g.user_id:
                return jsonify({"status": "error", "message": "Unauthorized"}), 403

        return jsonify({"status": "success", "doctor": doctor}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post('/register')
def register_user():
    data = request.get_json() or {}
    data['role'] = UserRole.USER.value
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.register_user(**data)  
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": ErrorMessages.USER_EXISTS.value}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.post('/register/doctor')
def register_doctor():
    data = request.get_json() or {}
    data['role'] = UserRole.DOCTOR.value
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.register_user(**data)  
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": ErrorMessages.USER_EXISTS.value}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:user_id>')
@token_required
def update_user(user_id):
    data = request.get_json() or {}
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_id(user_id)

            if not user:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = user['id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this user"}), 403

            updated_user_id = user_manager.update_user(user_id=user_id, **data)
        return jsonify({"status": "success", "updated_user_id": updated_user_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:user_id>/activate')
@role_required(UserRole.ADMIN.value)
def activate_user(user_id):
    """Admin activates pending doctor accounts"""
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            activated_user_id = user_manager.activate_user(user_id)
            if not activated_user_id:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
        return jsonify({"status": "success", "activated_user_id": activated_user_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.delete('/<int:user_id>')
@token_required
def delete_user(user_id):
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages.NO_USER_ID.value}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_id(user_id)

            if not user:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404

            isAdmin = g.role == UserRole.ADMIN.value
            isSelfModification = user['id'] == g.user_id
            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to delete this user"}), 403

            deleted_user = user_manager.delete_user(user_id)
            if not deleted_user:
                return jsonify({"status": "error", "message": ErrorMessages.USER_NOT_FOUND.value}), 404
        return jsonify({"status": "success", "deleted_user": deleted_user}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500