from flask import Flask, render_template, redirect, url_for, flash, session, Blueprint, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import datetime
import bcrypt
import weasyprint
import os
import threading
from bson.objectid import ObjectId
from bson import binary

from webforms import LoginForm, RegisterForm, PatientSearchForm, UpdateEmployeeProfile, ChangePasswordForm, PatientForm, DoctorPatientForm

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://harris:harris123@atlascluster.1jhzzr5.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

application = Flask(__name__)
application.config['SECRET_KEY'] = str(os.urandom(24).hex())

home_blueprint = Blueprint(
    'home', __name__, template_folder='.', url_prefix='/')
doctor_blueprint = Blueprint(
    'doctor', __name__, template_folder='doctor', url_prefix='/doctor')
nurse_blueprint = Blueprint(
    'nurse', __name__, template_folder='nurse', url_prefix='/nurse')

application.register_blueprint(home_blueprint)
application.register_blueprint(doctor_blueprint)
application.register_blueprint(nurse_blueprint)

login_manager = LoginManager()
login_manager.init_app(application)
login_manager.blueprint_login_views = {
    'home': 'home',
    'doctor': 'doctor_login',
    'nurse': 'nurse_login'
}


class Nurse(UserMixin):
    def __init__(self, employee_code, full_name, password,
                 created_at=datetime.datetime.now()):
        super().__init__()
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password
        self.id = employee_code

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def add_nurse(self):
        db = client['users']
        collection = db['nurse']
        existing_nurse = self.check_existing()
        if existing_nurse is False:
            new_nurse = dict(
                employee_code='nurse_' + self.employee_code,
                full_name=self.full_name,
                password=bcrypt.hashpw(
                    self.password.encode('utf-8'), bcrypt.gensalt()),
                created_at=self.created_at
            )
            collection.insert_one(new_nurse)
            return True
        else:
            return False

    def check_existing(self):
        db = client['users']
        collection = db['nurse']
        existing_nurse = collection.find_one(
            {'employee_code': self.employee_code})
        return True if existing_nurse is not None else False

    @staticmethod
    def get_nurse(employee_code):
        db = client['users']
        collection = db['nurse']
        nurse = collection.find_one({'employee_code': employee_code})
        return nurse

    def __repr__(self):
        return f'<Nurse {self.employee_code}>'


class Doctor(UserMixin):
    def __init__(self, employee_code, full_name, password,
                 created_at=datetime.datetime.now()):
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password
        self.id = employee_code

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def add_doctor(self):
        db = client['users']
        collection = db['doctor']
        existing_doctor = self.check_existing()
        if existing_doctor is False:
            new_doctor = dict(
                employee_code='doctor_' + self.employee_code,
                full_name=self.full_name,
                password=bcrypt.hashpw(
                    self.password.encode('utf-8'), bcrypt.gensalt()),
                created_at=self.created_at
            )
            collection.insert_one(new_doctor)
            return True
        else:
            return False

    def check_existing(self):
        db = client['users']
        collection = db['doctor']
        existing_doctor = collection.find_one(
            {'employee_code': self.employee_code})
        return True if existing_doctor is not None else False

    @staticmethod
    def get_doctor(employee_code):
        db = client['users']
        collection = db['doctor']
        doctor = collection.find_one({'employee_code': employee_code})
        return doctor

    def __repr__(self):
        return f'<Doctor {self.employee_code}>'


class Patient:
    def __init__(
            self, medical_record_number, full_name, cnic, age, patient_type, weight_kg,
            height_cm, b_bp_sys, b_bp_dia, temperature, pulse, bsr, urine_albumin, hb,
            spO2, created_at=datetime.datetime.now(),
            visit_number=1) -> None:
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
        self.recorded_by = Nurse.get_nurse(session['employee_code'])[
            'full_name'].split()[0].capitalize()

    def add_patient(self):
        db = client['users']
        collection = db['patients']
        existing_patient = collection.find_one(
            {'medical_record_number': self.medical_record_number})
        self.recorded_by = Nurse.get_nurse(session['employee_code'])[
            'full_name'].split()[0].capitalize()
        if existing_patient is None:
            new_patient = dict(
                medical_record_number=self.medical_record_number,
                full_name=self.full_name,
                cnic=self.cnic,
                age=self.age,
                patient_type=self.patient_type,
                weight_kg=self.weight_kg,
                height_cm=self.height_cm,
                b_bp_sys=self.b_bp_sys,
                b_bp_dia=self.b_bp_dia,
                temperature=self.temperature,
                pulse=self.pulse,
                bsr=self.bsr,
                urine_albumin=self.urine_albumin,
                hb=self.hb,
                spO2=self.spO2,
                created_at=self.created_at,
                visit_number=self.visit_number,
                recorded_by=self.recorded_by
            )
            collection.insert_one(new_patient)
            return True
        else:
            return False

    @staticmethod
    def get_patient(medical_record_number):
        db = client['users']
        collection = db['patients']
        patient = collection.find_one(
            {'medical_record_number': medical_record_number})
        return patient

    @staticmethod
    def check_existing(medical_record_number):
        db = client['users']
        collection = db['patients']
        existing_patient = collection.find_one(
            {'medical_record_number': medical_record_number})
        return True if existing_patient is not None else False

    def __repr__(self):
        return f'<Patient {self.medical_record_number}>'


class Audio:
    def __init__(self, audio_type, file, medical_record_number):
        self.audio_type = audio_type
        self.audio_path = file
        self.medical_record_number = medical_record_number
        self.audio_binary = binary.Binary(open(file, 'rb').read())
        self.transcribed_text = ''

    def add_audio(self):
        db = client['users']
        collection = db['audios']
        existing_audio = collection.find_one(
            {'medical_record_number': self.medical_record_number})
        if not existing_audio or existing_audio['audio_type'] != self.audio_type:
            new_audio = dict(
                audio_type=self.audio_type,
                audio_binary=self.audio_binary,
                medical_record_number=self.medical_record_number
            )
            collection.insert_one(new_audio)
            return True
        if existing_audio is None:
            new_audio = dict(
                audio_type=self.audio_type,
                audio_binary=self.audio_binary,
                medical_record_number=self.medical_record_number
            )
            collection.insert_one(new_audio)
            return True
        else:
            return False

    def add_transcription(self):
        self.transcribed_text = self.transcribe_audio()
        db = client['users']
        collection = db['audios']
        collection.update_one(
            {'medical_record_number': self.medical_record_number},
            {'$set': {
                'transcribed_text': self.transcribed_text
            }}
        )
        return True

    @staticmethod
    def get_audio(medical_record_number):
        db = client['users']
        collection = db['audios']
        audio = collection.find_one(
            {'medical_record_number': medical_record_number})
        return audio

    @staticmethod
    def get_transcription(medical_record_number):
        db = client['users']
        collection = db['audios']
        audio = collection.find_one(
            {'medical_record_number': medical_record_number})
        return audio['transcribed_text']

    @staticmethod
    def transcribe_audio():
        pass


@login_manager.user_loader
def load_user(user_id):
    role, _ = user_id.split('_')
    if role == 'doctor':
        user = Doctor.get_doctor(user_id)
        if not user:
            return None
        return Doctor(
            user['employee_code'],
            user['full_name'],
            user['password'],
            user['created_at'])
    elif role == 'nurse':
        user = Nurse.get_nurse(user_id)
        if not user:
            return None
        return Nurse(
            user['employee_code'],
            user['full_name'],
            user['password'],
            user['created_at'])
    else:
        return None


########################################## ERROR HANDLERS ##########################################


@application.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@application.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@application.errorhandler(403)
def forbidden(e):
    return '''
    <h1>Forbidden</h1>
    <p>The server understood the request but refuses to authorize it.</p>
    ''', 403


########################################## HOME ##########################################


@application.route('/')
@application.route('/home')
def home():
    return render_template('index.html')

########################################## NURSE ##########################################


@application.route('/nurse/register', methods=['GET', 'POST'])
def nurse_register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_nurse = Nurse(
            employee_code=form.employee_code.data,
            full_name=form.full_name.data,
            password=form.password.data,
        )
        existing_nurse = new_nurse.check_existing()
        if not existing_nurse:
            new_nurse.add_nurse()
            flash('Registered successfully!', 'success')
            return redirect(url_for('nurse_login'))
        else:
            flash('User already exists!', 'danger')
            return redirect(url_for('nurse_register'))
    return render_template('./nurse/signup.html', form=form)


@application.route('/nurse/login', methods=['GET', 'POST'])
def nurse_login():
    form = LoginForm()
    if form.validate_on_submit():
        employee_code = 'nurse_' + form.employee_code.data
        password = form.password.data
        nurse = Nurse.get_nurse(employee_code)
        login_successful=False
        if nurse and bcrypt.checkpw(password.encode('utf-8'), nurse['password']):
            login_user(Nurse(
                employee_code=nurse['employee_code'],
                full_name=nurse['full_name'],
                password=nurse['password'],
                created_at=nurse['created_at']
            ))
            login_successful=True
            session['employee_code'] = employee_code
            flash('Logged in successfully!', 'success')
            return render_template('./nurse/login.html', form=form, login_successful=login_successful)
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('nurse_login'))
    return render_template('./nurse/login.html', form=form)


@application.route('/nurse/dashboard')
@login_required
def nurse_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = Nurse.get_nurse(employee_code)[
            'full_name'].split()[0].capitalize()
        curr_date, curr_time = datetime.datetime.now().strftime(
            "%d %B %Y"), datetime.datetime.now().strftime("%H:%M")
        form = PatientSearchForm()
        return render_template(
            template_name_or_list='./nurse/dashboard.html',
            first_name=first_name,
            curr_date=curr_date,
            curr_time=curr_time,
            form=form
        )
    return redirect(url_for('nurse_login'))


@application.route('/nurse/vitals', methods=['GET', 'POST'])
@login_required
def nurse_vitals():
    form = PatientForm()
    if form.validate_on_submit():
        existing_patient = Patient.check_existing(
            form.medical_record_number.data)
        if not existing_patient:
            new_patient = Patient(
                medical_record_number=form.medical_record_number.data,
                full_name=form.patient_name.data,
                cnic=form.patient_cnic.data,
                age=form.patient_age.data,
                patient_type=form.patient_type.data,
                weight_kg=form.weight_kg.data,
                height_cm=form.height_cm.data,
                b_bp_sys=form.b_bp_sys.data,
                b_bp_dia=form.b_bp_dia.data,
                temperature=form.temperature.data,
                pulse=form.pulse.data,
                bsr=form.bsr.data,
                urine_albumin=form.urine_albumin.data,
                hb=form.hb.data,
                spO2=form.spO2.data,
                visit_number=1,
            )
            new_patient.add_patient()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Patient already exists!', 'danger')
            return redirect(url_for('nurse_vitals'))
    return render_template('./nurse/vitals.html', form=form)


@application.route('/nurse/profile/update', methods=['GET', 'POST'])
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
        template_name_or_list='./nurse/update-profile.html',
        form=form,
        curr_full_name=curr_full_name,
        curr_employee_code=curr_employee_code
    )


@application.route('/nurse/change-password', methods=['GET', 'POST'])
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
    return render_template('./nurse/change-password.html', form=form)


@application.route('/nurse/search', methods=['POST', 'GET'])
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
        if patients.distinct('medical_record_number') == []:
            flash('No patient found!', 'danger')
            return redirect(url_for('nurse_dashboard'))
        else:
            return redirect(
                url_for(
                    'nurse_patient',
                    medical_record_number=patients[0]
                    ['medical_record_number']))
    return redirect(url_for('nurse_dashboard'))


@application.route('/nurse/patient/<string:medical_record_number>')
@login_required
def nurse_patient(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()
    full_name = patient['full_name']
    age = patient['age']
    return render_template(
        './nurse/patient.html', patient=patient, date=date, time=time, mr_num=mr_num,
        nurse_name=nurse_name, full_name=full_name, age=age)


@application.route('/nurse/patients/<string:medical_record_number>/download')
@login_required
def nurse_download(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date = patient['created_at'].strftime("%d %B %Y")
    time = patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = Nurse.get_nurse(session['employee_code'])['full_name']
    nurse_name = nurse_name.split()[0].capitalize()
    full_name = patient['full_name']
    age = patient['age']
    rendered = render_template(
        './nurse/patient.html', patient=patient, date=date, time=time, mr_num=mr_num,
        nurse_name=nurse_name, full_name=full_name, age=age)
    pdf = weasyprint.HTML(string=rendered).write_pdf()
    response = application.make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=Patient Details {mr_num}.pdf'
    return response


@application.route('/nurse/logout')
@login_required
def nurse_logout():
    logout_user()
    session.pop('employee_code', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

########################################## DOCTOR ##########################################


@application.route('/doctor/register', methods=['GET', 'POST'])
def doctor_register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_doctor = Doctor(
            employee_code=form.employee_code.data,
            full_name=form.full_name.data,
            password=form.password.data,
        )
        existing_doctor = new_doctor.check_existing()
        if not existing_doctor:
            new_doctor.add_doctor()
            flash('Registered successfully!', 'success')
            return redirect(url_for('doctor_login'))
        else:
            flash('User already exists!', 'danger')
            return redirect(url_for('doctor_register'))
    return render_template('./doctor/signup.html', form=form)


@application.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    form = LoginForm()
    if form.validate_on_submit():
        employee_code = 'doctor' + form.employee_code.data
        password = form.password.data
        doctor = Doctor.get_doctor(employee_code)
        login_successful=False
        if doctor and bcrypt.checkpw(password.encode('utf-8'), doctor['password']):
            login_user(Doctor(
                employee_code=doctor['employee_code'],
                full_name=doctor['full_name'],
                password=doctor['password'],
                created_at=doctor['created_at']
            ))
            login_successful=True
            session['employee_code'] = employee_code
            flash('Logged in successfully!', 'success')
            return render_template('./doctor/login.html', form=form, login_successful=login_successful)
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('doctor_login'))
    return render_template('./doctor/login.html', form=form)


@application.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = Doctor.get_doctor(employee_code)[
            'full_name'].split()[0].capitalize()
        curr_date, curr_time = datetime.datetime.now().strftime(
            "%d %B %Y"), datetime.datetime.now().strftime("%H:%M")
        form = PatientSearchForm()
        return render_template(
            template_name_or_list='./doctor/dashboard.html',
            first_name=first_name,
            curr_date=curr_date,
            curr_time=curr_time,
            form=form
        )
    return redirect(url_for('doctor_login'))


@application.route('/doctor/profile/update', methods=['GET', 'POST'])
@login_required
def doctor_update_profile():
    if 'employee_code' in session:
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
        template_name_or_list='./doctor/update-profile.html',
        form=form,
        curr_full_name=curr_full_name,
        curr_employee_code=curr_employee_code
    )


@application.route('/doctor/change-password', methods=['GET', 'POST'])
@login_required
def doctor_change_password():
    if 'employee_code' in session:
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
    return render_template('./doctor/change-password.html', form=form)


@application.route('/doctor/search', methods=['POST', 'GET'])
@login_required
def doctor_search():
    if 'employee_code' in session:
        form = PatientSearchForm()
        if form.validate_on_submit():
            searched = form.searched.data
            db = client['users']
            collection = db['patients']
            patients = collection.find({'$or': [
                {'full_name': {'$regex': searched, '$options': 'i'}},
                {'medical_record_number': {'$regex': searched, '$options': 'i'}},
            ]})
            if patients.distinct('medical_record_number') == []:
                flash('No patient found!', 'danger')
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(
                    url_for(
                        'doctor_patient',
                        medical_record_number=patients[0]
                        ['medical_record_number']))
    return redirect(url_for('doctor_dashboard'))


@application.route('/doctor/logout')
@login_required
def doctor_logout():
    logout_user()
    session.pop('employee_code', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))


# temp: to be removed later
@application.route('/doctor/vitals', methods=['GET', 'POST'])
@login_required
def doctor_vitals():
    pass


@application.route('/doctor/patient/<string:medical_record_number>')
@login_required
def doctor_patient(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()
    full_name = patient['full_name']
    age = patient['age']
    return render_template(
        './doctor/patient.html', patient=patient, date=date, time=time, mr_num=mr_num,
        nurse_name=nurse_name, full_name=full_name, age=age)


@application.route(
    '/doctor/patient/<string:medical_record_number>/medical-history/record',
    methods=['POST', 'GET'])
@login_required
def record_medical_history(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()
    form = DoctorPatientForm()
    form_success = False
    audio_success = False
    if form.validate_on_submit():
        gravida = form.gravida.data
        lmp_date = form.lmp_date.data
        has_allergies = form.has_allergies.data
        allergy_drug = form.allergy_drug.data
        allergy_pollen = form.allergy_pollen.data
        allergy_dust = form.allergy_dust.data
        allergy_other = form.allergy_other.data

        gestation_age = (datetime.datetime.now().date() - lmp_date).days // 7
        edd = lmp_date + datetime.timedelta(days=280)

        db = client['users']
        collection = db['patients']
        collection.update_one(
            {'medical_record_number': medical_record_number},
            {'$set': {
                'gravida': gravida,
                'lmp_date': lmp_date,
                'gestation_age': gestation_age,
                'edd': edd,
                'has_allergies': has_allergies,
                'allergy_drug': allergy_drug,
                'allergy_pollen': allergy_pollen,
                'allergy_dust': allergy_dust,
                'allergy_other': allergy_other
            }}
        )
        flash('Medical history recorded successfully!', 'success')
        form_success = True

    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='medical-history',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if form_success and audio_success:
        return redirect(
            url_for(
                'record_family_history',
                medical_record_number=medical_record_number))
    else:
        flash('Please fill all the fields!', 'danger')
    return render_template(
        './doctor/record-medical-hist.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name, form=form)


@application.route('/doctor/patient/<string:medical_record_number>/family-history/record',
                   methods=['POST', 'GET'])
@login_required
def record_family_history_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='family-history',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        flash('Please submit an audio file!', 'danger')

    return render_template(
        './doctor/record-family-hist.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


@application.route('/doctor/patient/<string:medical_record_number>/socio-hist/record',
                   methods=['POST', 'GET'])
@login_required
def record_social_history_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='socioeconomic-history',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        flash('Please submit an audio file!', 'danger')

    return render_template(
        './doctor/record-socio-hist.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


@application.route('/doctor/patient/<string:medical_record_number>/prev-preg/record',
                   methods=['POST', 'GET'])
@login_required
def record_prev_preg_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='previous-pregnancies',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        flash('Please submit an audio file!', 'danger')

    return render_template(
        './doctor/record-prev-preg.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


@application.route('/doctor/patient/<string:medical_record_number>/prop-plan/record',
                   methods=['POST', 'GET'])
@login_required
def record_prop_plan_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='proposed-plan',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        flash('Please submit an audio file!', 'danger')

    return render_template(
        './doctor/record-proposed-plan.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


@application.route('/doctor/patient/<string:medical_record_number>/cond-booking/record',
                   methods=['POST', 'GET'])
@login_required
def record_cond_booking_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}.mp3'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='condition-at-booking',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        flash('Please submit an audio file!', 'danger')

    return render_template(
        './doctor/cond-at-booking.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)
