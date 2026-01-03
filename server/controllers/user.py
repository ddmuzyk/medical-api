from flask import Blueprint, request, jsonify, g
from queries.user import UserQueryManager
from constants import ErrorMessages
from db_connection import DbPool
from psycopg2 import errors
from middleware.auth import token_required, role_required
from constants import UserRole

bp = Blueprint('user', __name__)

@bp.post('/register')
def register_user():
    data = request.get_json() or {}
    data['role'] = UserRole['USER']
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.register_user(**data)  
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": ErrorMessages["USER_EXISTS"]}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.post('/register/doctor')
def register_doctor():
    data = request.get_json() or {}
    data['role'] = UserRole.DOCTOR
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.register_user(**data)  
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": ErrorMessages["USER_EXISTS"]}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:user_id>')
@token_required
def update_user(user_id):
    data = request.get_json() or {}
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_id(user_id)
            isAdmin = g.role == UserRole.ADMIN
            isSelfModification = user and user['user_id'] == g.user_id
            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this user"}), 403

            updated_user_id = user_manager.update_user(user_id=user_id, **data)
        return jsonify({"status": "success", "updated_user_id": updated_user_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.delete('/<int:user_id>')
@token_required
def delete_user(user_id):
    if not user_id:
        return jsonify({"status": "error", "message": ErrorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_id(user_id)
            isAdmin = g.role == UserRole.ADMIN
            isSelfModification = user and user['user_id'] == g.user_id
            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to delete this user"}), 403

            deleted_user = user_manager.delete_user(user_id)
            if not deleted_user:
                return jsonify({"status": "error", "message": ErrorMessages["USER_NOT_FOUND"]}), 404
        return jsonify({"status": "success", "deleted_user": deleted_user}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500