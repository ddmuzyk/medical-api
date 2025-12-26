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