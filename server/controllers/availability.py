from flask import Blueprint, request, jsonify
from queries.appointment import AppointmentQueryManager
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('availability', __name__)

@bp.post('/')
def create_doctor_availability():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability_id = appointment_manager.create_doctor_availability(**data)  
        return jsonify({"status": "success", "availability_id": availability_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.get('/doctor/<int:doctor_id>')
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
def update_doctor_availability(availability_id):
    data = request.get_json() or {}
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            updated_availability_id = appointment_manager.change_doctor_availability(availability_id=availability_id, **data)
        return jsonify({"status": "success", "updated_availability_id": updated_availability_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.delete('/<int:availability_id>')
def delete_doctor_availability(availability_id):
    if not availability_id:
        return jsonify({"status": "error", "message": "No availability ID provided"}), 400
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            deleted_availability = appointment_manager.delete_doctor_availability(availability_id)
            if not deleted_availability:
                return jsonify({"status": "error", "message": "Availability not found"}), 404
        return jsonify({"status": "success", "deleted_availability": deleted_availability}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500