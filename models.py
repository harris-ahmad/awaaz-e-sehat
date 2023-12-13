from app import db
import datetime
from flask_login import UserMixin
import bcrypt

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_code = db.Column(db.String(100), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def verify_password(password_hash, password):
        same_password = bcrypt.checkpw(password=password.encode('utf-8'), hashed_password=password_hash)
        return same_password

class Nurse(db.Model, UserMixin):
    __tablename__ = 'nurses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='nurse', lazy='joined')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Doctor(db.Model, UserMixin):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='doctor', lazy='joined')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# add a patient model 
class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medical_record_number = db.Column(db.String(100), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_cnic = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_type = db.Column(db.String(100), nullable=False)
    visit_number = db.Column(db.Integer, nullable=False, default=1)
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    b_bp_sys = db.Column(db.Integer)
    b_bp_dia = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    pulse = db.Column(db.Integer)
    bsr = db.Column(db.Integer)
    urine_albumin = db.Column(db.String(100))
    hb = db.Column(db.Float)
    spO2 = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bmi = db.Column(db.Float)

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm:
            return round(self.weight_kg / ((self.height_cm / 100) ** 2), 2)
        return None
    
    @bmi.setter
    def bmi(self, bmi):
        self.bmi = bmi
