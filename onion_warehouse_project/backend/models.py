from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Float, nullable=False)
    hum = db.Column(db.Float, nullable=False)
    co2 = db.Column(db.Float)
    nh3 = db.Column(db.Float)
    ben = db.Column(db.Float)
    total_ppm = db.Column(db.Float)
    cooler_on = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "temp": self.temp,
            "T": self.temp,
            "hum": self.hum,
            "H": self.hum,
            "co2": self.co2,
            "CO2": self.co2,
            "nh3": self.nh3,
            "NH3": self.nh3,
            "ben": self.ben,
            "Ben": self.ben,
            "total": self.total_ppm,
            "c": 1 if self.cooler_on else 0,
            "time": self.timestamp.strftime("%H:%M")
        }
