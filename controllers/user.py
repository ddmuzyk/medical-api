from flask import Blueprint, request, jsonify

bp = Blueprint('user', __name__)

@bp.post('/register')
def register_user():
    data = request.get_json() or {}
    username, password = data.get('username'), data.get('password')
    print(f"Registering user: {username} with password: {password}")
    return jsonify({'message': f'User {username} registered successfully'}), 201