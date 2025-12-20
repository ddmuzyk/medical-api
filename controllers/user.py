from flask import Blueprint, request, jsonify
from queries.user import UserQueryManager
from constants import userRole, errorMessages
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('user', __name__)

@bp.post('/register')
def register_user():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    pesel = data.get('pesel')
    phone = data.get('phone')
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.add_user_to_db(username, password, role=userRole['USER'])  
        return jsonify({"status": "success", "user_id": user_id}), 201
    except errors.UniqueViolation:
        return jsonify({"status": "error", "message": errorMessages["USER_EXISTS"]}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 

@bp.post('/delete')
def delete_users():
    data = request.get_json() or {}
    user_ids = data.get('user_ids', [])
    if not user_ids:
        return jsonify({"status": "error", "message": "No user IDs provided."}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            deleted_count = user_manager.delete_users(*user_ids)
        return jsonify({"status": "success", "deleted_count": deleted_count}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500