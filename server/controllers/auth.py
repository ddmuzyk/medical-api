from flask import Blueprint, request, jsonify, g
from db_connection import DbPool
from services.auth_service import AuthService
from middleware.auth import token_required
from queries.user import UserQueryManager

bp = Blueprint('auth', __name__)

@bp.post('/login')
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            "status": "error", 
            "message": "Email and password required"
        }), 400
    
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_email(email)
            
            if not user:
                return jsonify({
                    "status": "error", 
                    "message": "Invalid credentials"
                }), 401
            
            user_id = user['id']
            password_hash = user['password_hash']
            role = user['role']

            if not AuthService.verify_password(password, password_hash):
                return jsonify({
                    "status": "error", 
                    "message": "Invalid credentials"
                }), 401
            

            token = AuthService.create_session(user_id, role, expiry_hours=24)
            
        return jsonify({
            "status": "success",
            "token": token,
            "user_id": user_id,
            "role": role
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post('/logout')
@token_required
def logout():
    try:
        AuthService.delete_session(g.token)
        return jsonify({
            "status": "success", 
            "message": "Logged out successfully"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.post('/refresh')
@token_required
def refresh():
    try:
        AuthService.refresh_session(g.token, expiry_hours=24)
        return jsonify({
            "status": "success", 
            "message": "Session refreshed"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.get('/verify')
@token_required
def verify():
    return jsonify({
        "status": "success",
        "user_id": g.user_id,
        "role": g.user_role
    }), 200

@bp.get('/me')
@token_required
def get_current_user():
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            user = user_manager.get_user_by_id(g.user_id)
            
            if not user:
                return jsonify({
                    "status": "error", 
                    "message": "User not found"
                }), 404
            
        return jsonify({
            "status": "success",
            "user": user
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500