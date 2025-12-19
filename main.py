from flask import Flask, jsonify
from dotenv import load_dotenv
from db_connection import DbPool
from controllers.user import bp as user_bp
import atexit

load_dotenv()
app = Flask(__name__)
app.register_blueprint(user_bp, url_prefix='/users')

@app.get("/doctors")
def list_doctors():
    with DbPool.cursor(commit=False) as cur:
        cur.execute("SELECT * FROM doctors")
        rows = cur.fetchall()
    return jsonify(rows)

@atexit.register
def cleanup():
    DbPool.closeall()

if __name__ == "__main__":
    app.run(debug=True)