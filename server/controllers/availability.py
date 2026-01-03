from flask import Blueprint, request, jsonify, g
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from db_connection import DbPool
from middleware.auth import role_required, token_required
from constants import userRole

bp = Blueprint('availability', __name__)

@bp.post('/')
@role_required(userRole['ADMIN'], userRole['DOCTOR'])
def create_doctor_availability():
    data = request.get_json() or {}
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            user = user_manager.get_doctor(data.get('doctor_id'))
            isAdmin = g.role == userRole['ADMIN']

            if not user or (not isAdmin and user['user_id'] != g.user_id):
                return jsonify({"status": "error", "message": "Unauthorized to create availability for this doctor"}), 403

            availability_id = appointment_manager.create_doctor_availability(**data)  
        return jsonify({"status": "success", "availability_id": availability_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
@token_required
def get_doctor_availability(doctor_id):
    if not doctor_id:
        return jsonify({"status": "error", "message": "No doctor ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(doctor_id)
        return jsonify({"status": "success", "availability": availability}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:availability_id>')
@role_required(userRole['ADMIN'], userRole['DOCTOR'])
def update_doctor_availability(availability_id):
    data = request.get_json() or {}
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(availability_id)
            user = user_manager.get_doctor(availability['doctor_id']) if availability else None
            isAdmin = g.role == userRole['ADMIN']
            isSelfModification = user and user['user_id'] == g.user_id

            if not isAdmin and not isSelfModification:
                return jsonify({"status": "error", "message": "Unauthorized to modify this availability"}), 403

            updated_availability_id = appointment_manager.change_doctor_availability(availability_id=availability_id, **data)
        return jsonify({"status": "success", "updated_availability_id": updated_availability_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:availability_id>')
@role_required(userRole['ADMIN'], userRole['DOCTOR'])
def delete_doctor_availability(availability_id):
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability = appointment_manager.get_doctor_availability(availability_id)
            isSelfDeletion = availability and availability['doctor_id'] == g.user_id
            isAdmin = g.role == userRole['ADMIN']

            if not availability or (not isAdmin and not isSelfDeletion):
                return jsonify({"status": "error", "message": "Unauthorized to modify this availability"}), 403

            deleted_availability = appointment_manager.delete_doctor_availability(availability_id)
            if not deleted_availability:
                return jsonify({"status": "error", "message": "Availability not found"}), 404
        return jsonify({"status": "success", "deleted_availability": deleted_availability}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500