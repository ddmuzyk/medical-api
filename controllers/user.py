from flask import Blueprint, request, jsonify
from queries.user import UserQueryManager
from constants import userRole, errors
from db_connection import DbPool

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
    print(f"Registering user: {username} with password: {password}")
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user_id = user_manager.add_user_to_db(username, password, role=userRole['USER'])
        return jsonify({"status": "success", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": errors["USER_EXISTS"]}), 500
