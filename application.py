from flask import Flask, render_template, redirect, url_for, flash, session, Blueprint, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import datetime
import bcrypt
import os
from typing import Tuple

from webforms import (
    LoginForm,
    RegisterForm,
    PatientSearchForm,
    PatientForm,
    DoctorPatientForm
)

from models import Nurse, Doctor, Patient, Audio
from database import client

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


@login_manager.user_loader
def load_user(user_id) -> UserMixin:
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


@application.errorhandler(404)
def page_not_found(e) -> str:
    return render_template('404.html'), 404


@application.errorhandler(500)
def server_error(e) -> str:
    return render_template('500.html'), 500


@application.errorhandler(403)
def forbidden(e) -> Tuple[str, int]:
    return '''
    <h1>Forbidden</h1>
    <p>The server understood the request but refuses to authorize it.</p>
    ''', 403


@application.route('/')
@application.route('/home')
def home():
    return render_template('index.html')


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
        employee_code = 'doctor_' + form.employee_code.data
        password = form.password.data
        doctor = Doctor.get_doctor(employee_code)
        if doctor and bcrypt.checkpw(password.encode('utf-8'), doctor['password']):
            login_user(Doctor(
                employee_code=doctor['employee_code'],
                full_name=doctor['full_name'],
                password=doctor['password'],
                created_at=doctor['created_at']
            ))
            session['employee_code'] = doctor['employee_code']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('doctor_login'))
    return render_template('./doctor/login.html', form=form)


@application.route('/doctor/logout')
@login_required
def doctor_logout():
    logout_user()
    session.pop('employee_code', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))


@application.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = Doctor.get_doctor(employee_code)[
            'full_name'].split()[0].capitalize()
        curr_date, curr_time = datetime.datetime.now().strftime(
            "%d %B %Y"), datetime.datetime.now().strftime("%H:%M")
        employee_code = session['employee_code']
        form = PatientSearchForm()
        return render_template(
            template_name_or_list='./doctor/dashboard.html',
            first_name=first_name,
            curr_date=curr_date,
            curr_time=curr_time,
            form=form,
            employee_code=employee_code
        )
    return redirect(url_for('doctor_login'))


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
    visit_number = patient['visit_number']
    vitals_recorded_at = patient['created_at'].strftime(
        "%d %B %Y %H:%M")
    return render_template(
        './doctor/patient.html', patient=patient, date=date, time=time, mr_num=mr_num,
        nurse_name=nurse_name, full_name=full_name, age=age, visit_number=visit_number, vitals_recorded_at=vitals_recorded_at)


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

        if gravida:
            session['gravida'] = gravida

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
        session['med_history_form_filled'] = True
    
    print(request.files)

    if 'audio' in request.files:
        print('audio_data found')
        audio_file = request.files['audio']
        file_name = f'{medical_record_number}_medical_history.wav'
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
        session['all_medical_history_recorded'] = True
        return redirect(
            url_for(
                'record_family_history',
                medical_record_number=medical_record_number))
    elif form_success and not audio_success:
        session['all_medical_history_recorded'] = False
    elif not form_success and audio_success:
        session['all_medical_history_recorded'] = False
    else:
        session['all_medical_history_recorded'] = False
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
        file_name = f'{medical_record_number}_family_history.wav'
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
        session['all_family_history_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_family_history_recorded'] = False

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
        file_name = f'{medical_record_number}_socio_history.wav'
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
        session['all_socio_history_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_socio_history_recorded'] = False

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
        file_name = f'{medical_record_number}_prev_preg.wav'
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
        session['all_prev_preg_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_prev_preg_recorded'] = False

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
        file_name = f'{medical_record_number}_prop_plan.wav'
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
        session['all_prop_plan_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_prop_plan_recorded'] = False

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
        session['all_cond_booking_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_cond_booking_recorded'] = False

    return render_template(
        './doctor/cond-at-booking.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


@application.route('/doctor/patient/<string:medical_record_number>/present-preg/record',
                   methods=['POST', 'GET'])
@login_required
def record_present_preg_record(medical_record_number):
    patient = Patient.get_patient(medical_record_number)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    if 'audio_data' in request.files:
        audio_file = request.files['audio_data']
        file_name = f'{medical_record_number}_present_preg.wav'
        audio_path = os.path.join(
            application.root_path, 'static', 'audio', file_name)
        audio_file.save(audio_path)
        audio = Audio(
            audio_type='present-pregnancy',
            file=audio_path,
            medical_record_number=medical_record_number
        )
        audio.add_audio()
        audio_success = True

    if audio_success:
        session['all_present_preg_recorded'] = True
        return redirect(
            url_for(
                'doctor_patient',
                medical_record_number=medical_record_number))
    else:
        session['all_present_preg_recorded'] = False

    return render_template(
        './doctor/present-preg.html', patient=patient, date=date, time=time,
        mr_num=mr_num, nurse_name=nurse_name)


if __name__ == '__main__':
    application.run(debug=True)