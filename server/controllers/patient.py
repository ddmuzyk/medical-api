from flask import Blueprint, request, jsonify
from queries.user import UserQueryManager
from constants import errorMessages
from db_connection import DbPool
from psycopg2 import errors

bp = Blueprint('patient', __name__)

@bp.get('/<int:patient_id>')
def get_patient(patient_id):
    if not patient_id:
        return jsonify({"status": "error", "message": errorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            patient = user_manager.get_patient(patient_id)
            if not patient:
                return jsonify({"status": "error", "message": errorMessages["USER_NOT_FOUND"]}), 404
        return jsonify({"status": "success", "patient": patient}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@bp.patch('/<int:patient_id>')
def update_patient(patient_id):
    data = request.get_json() or {}
    if not patient_id:
        return jsonify({"status": "error", "message": errorMessages["NO_USER_ID"]}), 400
    try:
        with DbPool.cursor() as cur:
            user_manager = UserQueryManager(cur)
            updated_patient_id = user_manager.update_patient(patient_id=patient_id, **data)
        return jsonify({"status": "success", "updated_patient_id": updated_patient_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500