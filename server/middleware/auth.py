from functools import wraps
from flask import request, jsonify, g
from services.auth_service import AuthService

def token_required(f):
    """Decorator to require valid authentication token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"status": "error", "message": "Token is missing"}), 401

        if token.startswith('Bearer '):
            token = token[7:]
        
        session = AuthService.get_session(token)
        
        if not session:
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 401

        g.user_id = session['user_id']
        g.role = session['role']
        g.token = token
        
        return f(*args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if g.role not in allowed_roles:
                return jsonify({
                    "status": "error", 
                    "message": "Forbidden - insufficient permissions"
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator