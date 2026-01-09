from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from db_connection import DbPool
from controllers.user import bp as user_bp
from controllers.appointment import bp as appointment_bp
from controllers.availability import bp as availability_bp
from controllers.prescription import bp as prescription_bp
from controllers.patient import bp as patient_bp
from controllers.doctor import bp as doctor_bp
from controllers.auth import bp as auth_bp
from controllers.notification import bp as notification_bp
import atexit

load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(appointment_bp, url_prefix='/appointment')
app.register_blueprint(availability_bp, url_prefix='/availability')
app.register_blueprint(prescription_bp, url_prefix='/prescription')
app.register_blueprint(patient_bp, url_prefix='/patient')
app.register_blueprint(doctor_bp, url_prefix='/doctor')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(notification_bp, url_prefix='/notification')

@atexit.register
def cleanup():
    DbPool.closeall()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)