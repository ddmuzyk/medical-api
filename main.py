from flask import Flask, jsonify
from dotenv import load_dotenv
from db_connection import DbPool
from controllers.user import bp as user_bp
from controllers.appointment import bp as appointment_bp
import atexit

load_dotenv()
app = Flask(__name__)
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(appointment_bp, url_prefix='/appointment')

@atexit.register
def cleanup():
    DbPool.closeall()

if __name__ == "__main__":
    app.run(debug=True)