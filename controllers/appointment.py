from flask import Blueprint, request, jsonify
from queries.appointment import AppointmentQueryManager
from queries.user import UserQueryManager
from constants import userRole, errorMessages
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('appointment', __name__)

@bp.post('/create')
def create_appointment():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            appointment_id = appointment_manager.create_appointment(**data)  
        return jsonify({"status": "success", "appointment_id": appointment_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.post('/create/availability')
def create_doctor_availability():
    data = request.get_json() or {}
    
    try:
        with DbPool.cursor() as cur:
            appointment_manager = AppointmentQueryManager(cur)
            availability_id = appointment_manager.create_doctor_availability(**data)  
        return jsonify({"status": "success", "availability_id": availability_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500