import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import db, User, SensorReading
from auth import generate_token, token_required
from alerts import check_thresholds

load_dotenv()

app = Flask(__name__)
# Render provides DATABASE_URL with postgres:// which SQLAlchemy 1.4+ requires to be postgresql://
db_url = os.getenv("DATABASE_URL", "sqlite:///onion_warehouse.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db.init_app(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

# Create DB tables
with app.app_context():
    db.create_all()

ESP32_API_KEY = os.getenv("ESP32_API_KEY")

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Missing credentials"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "User already exists"}), 409
    
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        token = generate_token(user.username)
        return jsonify({"token": token, "username": user.username}), 200
    
    return jsonify({"msg": "Invalid credentials"}), 401

@app.route('/api/google-login', methods=['POST'])
def google_login():
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({"msg": "Missing token"}), 400
    
    try:
        # Verify Google token via Google's API
        google_res = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        google_data = google_res.json()
        
        if google_res.status_code != 200:
            return jsonify({"msg": "Invalid Google token"}), 401
        
        email = google_data.get('email')
        username = email.split('@')[0]
        
        # Check if user exists, otherwise create
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            user.set_password(os.urandom(16).hex()) # Dummy password for OAuth users
            db.session.add(user)
            db.session.commit()
            
        auth_token = generate_token(user.username)
        return jsonify({"token": auth_token, "username": user.username}), 200
        
    except Exception as e:
        return jsonify({"msg": f"Google Auth Error: {str(e)}"}), 500

@app.route('/api/data', methods=['POST'])
def receive_data():
    api_key = request.headers.get('x-api-key')
    if api_key != ESP32_API_KEY:
        return jsonify({"msg": "Unauthorized"}), 401
    
    data = request.json
    reading = SensorReading(
        temp=data.get('temp'),
        hum=data.get('hum'),
        co2=data.get('co2'),
        nh3=data.get('nh3'),
        ben=data.get('benzene'),
        total_ppm=data.get('total'),
        cooler_on=data.get('cooler', False)
    )
    db.session.add(reading)
    db.session.commit()
    
    # Check for alerts
    check_thresholds(data)
    
    return jsonify({"msg": "Data saved"}), 200

@app.route('/api/readings', methods=['GET'])
@token_required
def get_readings():
    # Return latest 24 readings
    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(24).all()
    # Reverse to keep chronological order for front-end
    return jsonify([r.to_dict() for r in reversed(readings)]), 200

@app.route('/api/latest', methods=['GET'])
@token_required
def get_latest():
    reading = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    if reading:
        return jsonify(reading.to_dict()), 200
    return jsonify({"msg": "No data"}), 404

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "Backend is running"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
