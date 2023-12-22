from flask import Flask, render_template, redirect, url_for, flash, session, Blueprint, request
from flask_login import LoginManager, login_user, logout_user, login_required
import datetime
import bcrypt
import weasyprint
import os

from faster_whisper import WhisperModel

from webforms import LoginForm, RegisterForm, PatientSearchForm, UpdateEmployeeProfile, ChangePasswordForm, PatientForm

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://harris:harris123@atlascluster.1jhzzr5.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# setting up the model
try:
    model_size = "large-v3"
    model = WhisperModel(model_size_or_path=model_size)
    print('Whisper Model Initialized')
except Exception as e:
    print('Error initializing the model')
    
app = Flask(__name__)
app.config['SECRET_KEY'] = str(os.urandom(24).hex())

home_blueprint = Blueprint('home', __name__, template_folder='.')
doctor_blueprint = Blueprint('doctor', __name__, template_folder='doctor')
nurse_blueprint = Blueprint('nurse', __name__, template_folder='nurse')

app.register_blueprint(doctor_blueprint, url_prefix='/doctor')
app.register_blueprint(nurse_blueprint, url_prefix='/nurse')
app.register_blueprint(home_blueprint, url_prefix='/')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.blueprint_login_views = {
    'doctor': '/doctor/login',
    'nurse': '/nurse/login'
}

class Nurse:
    def __init__(self, employee_code, full_name, password, created_at=datetime.datetime.now()):
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    
    def add_nurse(self):
        db = client['users']
        collection = db['nurse']
        existing_nurse = self.check_existing()
        if existing_nurse is False:
            new_nurse = dict(
                employee_code = 'nurse_' + self.employee_code,
                full_name = self.full_name,
                password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt()),
                created_at = self.created_at
            )
            collection.insert_one(new_nurse)
            return True
        else:
            return False

    def check_existing(self):
        db = client['users']
        collection = db['nurse']
        existing_nurse = collection.find_one({'employee_code': self.employee_code})
        return True if existing_nurse is not None else False

    @staticmethod 
    def get_nurse(employee_code):
        db = client['users']
        collection = db['nurse']
        nurse = collection.find_one({'employee_code': employee_code})
        return nurse
    
    @staticmethod
    def is_authenticated():
        return True
    
    @staticmethod
    def is_active():
        return True
    
    @staticmethod
    def is_anonymous():
        return False
    
    def get_id(self):
        return self.employee_code
    
    def __repr__(self):
        return f'<Nurse {self.employee_code}>'
    
class Doctor:
    def __init__(self, employee_code, full_name, password, created_at=datetime.datetime.now()):
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    
    def add_doctor(self):
        db = client['users']
        collection = db['doctor']
        existing_doctor = self.check_existing()
        if existing_doctor is False:
            new_doctor = dict(
                employee_code = 'doctor_' + self.employee_code,
                full_name = self.full_name,
                password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt()),
                created_at = self.created_at
            )
            collection.insert_one(new_doctor)
            return True
        else:
            return False

    def check_existing(self):
        db = client['users']
        collection = db['doctor']
        existing_doctor = collection.find_one({'employee_code': self.employee_code})
        return True if existing_doctor is not None else False

    @staticmethod 
    def get_doctor(employee_code):
        db = client['users']
        collection = db['doctor']
        doctor = collection.find_one({'employee_code': employee_code})
        return doctor
    
    @staticmethod
    def is_authenticated():
        return True
    
    @staticmethod
    def is_active():
        return True
    
    @staticmethod
    def is_anonymous():
        return False
    
    def get_id(self):
        return self.employee_code
    
    @login_manager.user_loader
    def load_user(employee_code):
        db = client['users']
        collection = db['doctor']
        user = collection.find_one({'employee_code': employee_code})
        if not user:
            return None
        return Doctor(user['employee_code'], user['full_name'], user['password'], user['created_at'])
    
    def __repr__(self):
        return f'<Doctor {self.employee_code}>'
    
class Patient:
    def __init__(self, medical_record_number, full_name, cnic, age, patient_type, weight_kg, \
                 height_cm, b_bp_sys, b_bp_dia, temperature, pulse, bsr, urine_albumin, hb,  \
                 spO2, created_at=datetime.datetime.now(), visit_number=1) -> None:
        self.medical_record_number = medical_record_number
        self.full_name = full_name
        self.cnic = cnic
        self.age = age
        self.patient_type = patient_type
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.b_bp_sys = b_bp_sys
        self.b_bp_dia = b_bp_dia
        self.temperature = temperature
        self.pulse = pulse
        self.bsr = bsr
        self.urine_albumin = urine_albumin
        self.hb = hb
        self.spO2 = spO2
        self.created_at = created_at
        self.visit_number = visit_number
        self.recorded_by = Nurse.get_nurse(session['employee_code'])['full_name'].split()[0].capitalize()
    
    def add_patient(self):
        db = client['users']
        collection = db['patients']
        existing_patient = collection.find_one({'medical_record_number': self.medical_record_number})
        self.recorded_by = Nurse.get_nurse(session['employee_code'])['full_name'].split()[0].capitalize()
        if existing_patient is None:
            new_patient = dict(
                medical_record_number = self.medical_record_number,
                full_name = self.full_name,
                cnic = self.cnic, 
                age = self.age,
                patient_type = self.patient_type,
                weight_kg = self.weight_kg,
                height_cm = self.height_cm,
                b_bp_sys = self.b_bp_sys,
                b_bp_dia = self.b_bp_dia,
                temperature = self.temperature,
                pulse = self.pulse,
                bsr = self.bsr,
                urine_albumin = self.urine_albumin,
                hb = self.hb,
                spO2 = self.spO2,
                created_at = self.created_at,
                visit_number = self.visit_number,
                recorded_by = self.recorded_by
            )
            collection.insert_one(new_patient)
            return True
        else:
            return False

    @staticmethod
    def get_patient(medical_record_number):
        db = client['users']
        collection = db['patients']
        patient = collection.find_one({'medical_record_number': medical_record_number})
        return patient
    
    @staticmethod
    def check_existing(medical_record_number):
        db = client['users']
        collection = db['patients']
        existing_patient = collection.find_one({'medical_record_number': medical_record_number})
        return True if existing_patient is not None else False
    
    def __repr__(self):
        return f'<Patient {self.medical_record_number}>'
        
@login_manager.user_loader
def load_user(user_id):
    role, _ = user_id.split('_')
    if role == 'doctor':
        user = Doctor.get_doctor(user_id)
        if not user:
            return None
        return Doctor(user['employee_code'], user['full_name'], user['password'], user['created_at'])
    elif role == 'nurse':
        user = Nurse.get_nurse(user_id)
        if not user:
            return None
        return Nurse(user['employee_code'], user['full_name'], user['password'], user['created_at'])

########################################## ERROR HANDLERS ##########################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

########################################## HOME ##########################################

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

########################################## NURSE ##########################################

@app.route('/nurse/register', methods=['GET', 'POST'])
def nurse_register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_nurse = Nurse(
            employee_code = form.employee_code.data,
            full_name = form.full_name.data,
            password = form.password.data,
        )
        existing_nurse = new_nurse.check_existing()
        if not existing_nurse:
            new_nurse.add_nurse()
            flash('Registered successfully!', 'success')
            return redirect(url_for('nurse_login'))
        else:
            flash('User already exists!', 'danger')
            return redirect(url_for('nurse_register'))
    return render_template('signup.html', form=form)

@app.route('/nurse/login', methods=['GET', 'POST'])
def nurse_login():
    form = LoginForm()
    if form.validate_on_submit():
        employee_code = 'nurse_' + form.employee_code.data
        password = form.password.data
        nurse = Nurse.get_nurse(employee_code)
        if nurse and bcrypt.checkpw(password.encode('utf-8'), nurse['password']):
            login_user(Nurse(
                employee_code = nurse['employee_code'],
                full_name = nurse['full_name'],
                password = nurse['password'],
                created_at = nurse['created_at']
            ))
            session['employee_code'] = employee_code
            flash('Logged in successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('nurse_login'))
    return render_template('login.html', form=form)

@app.route('/nurse/dashboard')
@login_required
def nurse_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = Nurse.get_nurse(employee_code)['full_name'].split()[0].capitalize()
        curr_date, curr_time = datetime.datetime.now().strftime("%d %B %Y"), datetime.datetime.now().strftime("%H:%M")
        form = PatientSearchForm()
        return render_template(
            template_name_or_list='dashboard.html',
            first_name=first_name,
            curr_date=curr_date,
            curr_time=curr_time,
            form=form
        )
    return redirect(url_for('nurse_login'))

@app.route('/nurse/vitals', methods=['GET', 'POST'])
@login_required
def nurse_vitals():
    form = PatientForm()
    if form.validate_on_submit():
        existing_patient = Patient.check_existing(form.medical_record_number.data)
        if not existing_patient:
            new_patient = Patient(
                medical_record_number = form.medical_record_number.data,
                full_name = form.patient_name.data,
                cnic = form.patient_cnic.data,
                age = form.patient_age.data,
                patient_type = form.patient_type.data,
                weight_kg = form.weight_kg.data,
                height_cm = form.height_cm.data,
                b_bp_sys = form.b_bp_sys.data,
                b_bp_dia = form.b_bp_dia.data,
                temperature = form.temperature.data,
                pulse = form.pulse.data,
                bsr = form.bsr.data,
                urine_albumin = form.urine_albumin.data,
                hb = form.hb.data,
                spO2 = form.spO2.data,
                visit_number = 1,
            )
            new_patient.add_patient()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Patient already exists!', 'danger')
            return redirect(url_for('nurse_vitals'))
    return render_template('vitals.html', form=form)

@app.route('/nurse/profile/update', methods=['GET', 'POST'])
@login_required
def nurse_update_profile():
    form = UpdateEmployeeProfile()
    profile = Nurse.get_nurse(session['employee_code'])
    curr_full_name, curr_employee_code = profile['full_name'], profile['employee_code']
    if form.validate_on_submit():
        full_name = form.full_name.data
        employee_code = form.employee_code.data
        if full_name != curr_full_name or employee_code != curr_employee_code:
            db = client['users']
            collection = db['nurse']
            collection.update_one(
                {'employee_code': curr_employee_code},
                {'$set': {
                    'full_name': full_name,
                    'employee_code': employee_code
                }}
            )
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('No changes made!', 'danger')
            return redirect(url_for('nurse_dashboard'))
    return render_template(
        template_name_or_list='update-profile.html',
        form=form,
        curr_full_name=curr_full_name,
        curr_employee_code=curr_employee_code
    )

@app.route('/nurse/change-password', methods=['GET', 'POST'])
@login_required
def nurse_change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        nurse = Nurse.get_nurse(session['employee_code'])
        if bcrypt.checkpw(current_password.encode('utf-8'), nurse['password']):
            if new_password == confirm_password:
                db = client['users']
                collection = db['nurse']
                collection.update_one(
                    {'employee_code': session['employee_code']},
                    {'$set': {
                        'password': bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    }}
                )
                flash('Password changed successfully!', 'success')
                return redirect(url_for('nurse_dashboard'))
            else:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('nurse_change_password'))
        else:
            flash('Invalid password!', 'danger')
            return redirect(url_for('nurse_change_password'))
    return render_template('change-password.html', form=form)

@app.route('/nurse/search', methods=['POST', 'GET'])
@login_required
def nurse_search():
    form = PatientSearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        db = client['users']
        collection = db['patients']
        patients = collection.find({'$or': [
            {'full_name': {'$regex': searched, '$options': 'i'}},
            {'medical_record_number': {'$regex': searched, '$options': 'i'}},
        ]})
        return redirect(url_for('nurse_patient', medical_record_number=patients[0]['medical_record_number']))
    return redirect(url_for('nurse_dashboard'))

@app.route('/nurse/patient/<string:medical_record_number>')
@login_required
def nurse_patient(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime("%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()
    return render_template('patient.html', patient=patient, date=date, time=time, mr_num=mr_num, nurse_name=nurse_name)

@app.route('/nurse/patients/<string:medical_record_number>/download')
@login_required
def nurse_download(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date = patient['created_at'].strftime("%d %B %Y")
    time = patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = Nurse.get_nurse(session['employee_code'])['full_name']
    nurse_name = nurse_name.split()[0].capitalize()
    rendered = render_template('patient.html', patient=patient, date=date, time=time, mr_num=mr_num, nurse_name=nurse_name)
    pdf = weasyprint.HTML(string=rendered).write_pdf()
    response = app.make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Patient Details {mr_num}.pdf'
    return response

@app.route('/nurse/logout')
@login_required
def nurse_logout():
    logout_user()
    session.pop('employee_code', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

########################################## DOCTOR ##########################################

@app.route('/doctor/register', methods=['GET', 'POST'])
def doctor_register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_doctor = Doctor(
            employee_code = form.employee_code.data,
            full_name = form.full_name.data,
            password = form.password.data,
        )
        existing_doctor = new_doctor.check_existing()
        if not existing_doctor:
            new_doctor.add_doctor()
            flash('Registered successfully!', 'success')
            return redirect(url_for('doctor_login'))
        else:
            flash('User already exists!', 'danger')
            return redirect(url_for('doctor_register'))
    return render_template('signup.html', form=form)

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    form = LoginForm()
    if form.validate_on_submit():
        employee_code = 'doctor_' + form.employee_code.data
        password = form.password.data
        doctor = Doctor.get_doctor(employee_code)
        if doctor and bcrypt.checkpw(password.encode('utf-8'), doctor['password']):
            login_user(Doctor(
                employee_code = doctor['employee_code'],
                full_name = doctor['full_name'],
                password = doctor['password'],
                created_at = doctor['created_at']
            ))
            session['employee_code'] = employee_code
            flash('Logged in successfully!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('doctor_login'))
    return render_template('login.html', form=form)

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = Doctor.get_doctor(employee_code)['full_name'].split()[0].capitalize()
        curr_date, curr_time = datetime.datetime.now().strftime("%d %B %Y"), datetime.datetime.now().strftime("%H:%M")
        form = PatientSearchForm()
        return render_template(
            template_name_or_list='dashboard.html',
            first_name=first_name,
            curr_date=curr_date,
            curr_time=curr_time,
            form=form
        )
    return redirect(url_for('doctor_login'))

@app.route('/doctor/profile/update', methods=['GET', 'POST'])
@login_required
def doctor_update_profile():
    form = UpdateEmployeeProfile()
    profile = Doctor.get_doctor(session['employee_code'])
    curr_full_name, curr_employee_code = profile['full_name'], profile['employee_code']
    if form.validate_on_submit():
        full_name = form.full_name.data
        employee_code = form.employee_code.data
        if full_name != curr_full_name or employee_code != curr_employee_code:
            db = client['users']
            collection = db['doctor']
            collection.update_one(
                {'employee_code': curr_employee_code},
                {'$set': {
                    'full_name': full_name,
                    'employee_code': employee_code
                }}
            )
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('No changes made!', 'danger')
            return redirect(url_for('doctor_dashboard'))
    return render_template(
        template_name_or_list='update-profile.html',
        form=form,
        curr_full_name=curr_full_name,
        curr_employee_code=curr_employee_code
    )

@app.route('/doctor/change-password', methods=['GET', 'POST'])
@login_required
def doctor_change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        doctor = Doctor.get_doctor(session['employee_code'])
        if bcrypt.checkpw(current_password.encode('utf-8'), doctor['password']):
            if new_password == confirm_password:
                db = client['users']
                collection = db['doctor']
                collection.update_one(
                    {'employee_code': session['employee_code']},
                    {'$set': {
                        'password': bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    }}
                )
                flash('Password changed successfully!', 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('doctor_change_password'))
        else:
            flash('Invalid password!', 'danger')
            return redirect(url_for('doctor_change_password'))
    return render_template('change-password.html', form=form)

@app.route('/doctor/search', methods=['POST', 'GET'])
@login_required
def doctor_search():
    form = PatientSearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        db = client['users']
        collection = db['patients']
        patients = collection.find({'$or': [
            {'full_name': {'$regex': searched, '$options': 'i'}},
            {'medical_record_number': {'$regex': searched, '$options': 'i'}},
        ]})
        return redirect(url_for('doctor_patient', medical_record_number=patients[0]['medical_record_number']))
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/logout')
@login_required
def doctor_logout():
    logout_user()
    session.pop('employee_code', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/doctor/vitals', methods=['GET', 'POST']) # temp: to be removed later
@login_required
def doctor_vitals():
    pass

@app.route('/doctor/patient/<string:medical_record_number>')
@login_required
def doctor_patient(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime("%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()
    return render_template('patient.html', patient=patient, date=date, time=time, mr_num=mr_num, nurse_name=nurse_name)

@app.route('/doctor/patient/<string:medical_record_number>/record/medical-history', methods=['POST', 'GET'])
@login_required
def record_medical_history(medical_record_number):
    if 'audio_data' not in request.files:
        flash('Please submit a recording to proceed.')
        return render_template('record-medical-hist.html')
    
    file = request.files['audio_data']
    audio_path = './audio/'
    file.save(audio_path) 

    segments, _ = model.transcribe(file, language='ur')
    segments = list(segments)
    prediction = ""
    for i in segments:
        prediction += i[4]
