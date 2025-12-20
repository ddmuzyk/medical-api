from flask import Blueprint, request, jsonify
from queries.user import UserQueryManager
from constants import userRole, errorMessages
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('user', __name__)

@bp.post('/register')
def register_user():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', userRole['USER'])
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_data = {
                'email': email,
                'password': password,
                'role': role
            }
            user_id = user_manager.add_user_to_db(**user_data)  
            if role == userRole["USER"]:
                patient_data = {
                    'user_id': user_id,
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'pesel': data.get('pesel'),
                    'phone': data.get('phone')
                }
                patient_data = {k: v for k, v in patient_data.items() if v is not None}
                user_manager.add_patient(**patient_data)
            
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": errorMessages["USER_EXISTS"]}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 

@bp.post('/delete')
def delete_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": errorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            deleted_user = user_manager.delete_user(user_id)
            if not deleted_user:
                return jsonify({"status": "error", "message": errorMessages["USER_NOT_FOUND"]}), 404
        return jsonify({"status": "success", "deleted_user": deleted_user}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500