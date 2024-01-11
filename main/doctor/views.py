from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
    make_response
)

from flask_login import (
    login_user, 
    logout_user, 
    login_required, 
    current_user, 
)

import datetime
import threading
import os
import bcrypt

from . import doctor
from .models import Patient, Audio, Doctor
from ..database import DB
from ..extensions import cache, login_manager
from ..prompting import Prompting
from .forms import PatientSearchForm, RegisterForm, LoginForm

@login_manager.user_loader
def load_user(employee_code):
    role, _ = employee_code.split('_')
    if role == 'doctor':
        user = Doctor(employee_code=employee_code)
        user = user.get_doctor(employee_code=employee_code)
        if user:
            return Doctor(
                employee_code=employee_code,
                full_name=user['full_name'],
                password=user['password'],
                created_at=user['created_at'],
            )
    return None

@doctor.route('/dashboard')
@login_required
def dashboard():
    form = PatientSearchForm()
    return render_template(
        template_name_or_list='dashboard.html',
        form=form,
    )

@doctor.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        employee_code = 'doctor_' + form.employee_code.data
        password = form.password.data
        doctor = Doctor(
            employee_code=employee_code,
            password=password,
        )
        doctor = doctor.get_doctor(employee_code=employee_code)
        if doctor and bcrypt.checkpw(
            password=password.encode('utf-8'), hashed_password=doctor['password']):
            login_user(Doctor(
                employee_code=employee_code,
                full_name=doctor['full_name'],
                password=password,
                created_at=doctor['created_at'],
            ))
            session['employee_code'] = employee_code
            flash('Logged in successfully', 'success')
            return redirect(url_for('doctor.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('doctor.login'))
        
    response = make_response(
        render_template(
                    template_name_or_list='login.html',
                    form=form,
                ),
                200,
    )
    response.headers['Content-Type'] = 'text/html'
    return response


@doctor.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_doctor = Doctor(
            employee_code=form.employee_code.data,
            full_name=form.full_name.data,
            password=form.password.data,
        )
        existing_doctor = new_doctor.check_existing()
        if existing_doctor:
            flash('Doctor already exists!', 'danger')
            return redirect(url_for('doctor.register'))
        else:
            new_doctor.add_doctor()
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('doctor.login'))
    response = make_response(
        render_template(
                    template_name_or_list='register.html',
                    form=form,
                ),
                200,
    )
    response.headers['Content-Type'] = 'text/html'
    return response


@doctor.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    session.pop('employee_code', None)
    return redirect(url_for('main.index'))


@doctor.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = PatientSearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        collection = DB['patients']
        patients = collection.find({'$or': [
            {'full_name': {'$regex': searched, '$options': 'i'}},
            {'medical_record_number': {'$regex': searched, '$options': 'i'}},
        ]})

        if patients.distinct('medical_record_number') == []:
                flash('No patient found!', 'danger')
                return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(
                url_for(
                    'doctor.patient',
                    mr_num=patients[0]
                    ['medical_record_number']))
        
    return redirect(url_for('doctor.dashboard'))


@doctor.get('/patient/<string:mr_num>')
@login_required
def patient(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
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
        'patient.html', patient=patient, mr_num=mr_num, nurse_name=nurse_name,
        full_name=full_name, age=age, visit_number=visit_number,
        vitals_recorded_at=vitals_recorded_at, date=date, time=time)


@doctor.route('/patient/<string:mr_num>/record/medical-history',
              methods=['GET', 'POST'])
@login_required
def record_medical_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    allergies = {}
    gestation_age = None
    edd = None

    form_success = False
    audio_success = False

    if request.method == 'POST':
        gravida = request.form.get('gravida')
        allergies = request.form.get('allergies')
        if allergies == 'yes':
            allergy_drug = request.form.get('allergyDrug')
            allergy_pollen = request.form.get('allergyPollen')
            allergy_dust = request.form.get('allergyDust')
            allergy_other = request.form.get('allergyOther')
            allergies = {
                'drug': allergy_drug,
                'pollen': allergy_pollen,
                'dust': allergy_dust,
                'other': allergy_other
            }
        else:
            allergies = {
                'drug': None,
                'pollen': None,
                'dust': None,
                'other': None
            }

        lmp_date = request.form.get('lmp_date')
        lmp_date_temp = None
        gestation_age = None
        edd = None

        if lmp_date:
            lmp_date = datetime.datetime.strptime(
                lmp_date, "%Y-%m-%d").date().strftime("%d %B %Y")
            lmp_date_temp = datetime.datetime.strptime(
                lmp_date, "%d %B %Y").date()

            gestation_age = (
                datetime.datetime.now().date() - lmp_date_temp).days // 7
            edd = lmp_date_temp + datetime.timedelta(days=280)
            edd = edd.strftime("%d %B %Y")
        else:
            lmp_date = None
            gestation_age = None
            edd = None

        medical_history_form_data = {
            'gravida': gravida,
            'allergies': allergies,
            'lmp_date': lmp_date,
            'gestation_age': gestation_age,
            'edd': edd
        }

        collection = DB['patients']
        collection.update_one(
            {'medical_record_number': mr_num},
            {'$set': medical_history_form_data}
        )

        form_success = True

        if 'audio' in request.files:
            audio = request.files['audio']
            filename = f'{mr_num}_medical_history.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)
            audio = Audio(
                audio_type='medical_history', file=audio_path,
                medical_record_number=mr_num)

            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success and not form_success:
        error_response = make_response(
            render_template(
                'record_medical_history.html', patient=patient, mr_num=mr_num,
                nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response

    return render_template(
        'record_medical_history.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, form_success=form_success,
        audio_success=audio_success)


@doctor.route('/patient/<string:mr_num>/record/family-history',
              methods=['GET', 'POST'])
@login_required
def record_family_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False

    if request.method == 'POST':
        if 'audio' in request.files:
            audio = request.files.get('audio', None)
            filename = f'{mr_num}_family_history.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)

            audio = Audio(
                audio_type='family_history', file=audio_path,
                medical_record_number=mr_num)
            
            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success:
        error_response = make_response(
            render_template(
                'record_family_history.html', patient=patient, mr_num=mr_num,
                nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_family_history.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success)


@doctor.route('/patient/<string:mr_num>/record/socioeconomic-history',
                methods=['GET', 'POST'])
@login_required
def record_socioeconomic_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False

    if request.method == 'POST':
        if 'audio' in request.files:
            audio = request.files.get('audio', None)
            filename = f'{mr_num}_socioeconomic_history.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)

            audio = Audio(
                audio_type='socioeconomic_history', file=audio_path,
                medical_record_number=mr_num)
            
            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success:
        error_response = make_response(
            render_template(
                'record_socioeconomic_history.html', patient=patient,
                mr_num=mr_num, nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_socioeconomic_history.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success)


@doctor.route('/patient/<string:mr_num>/record/previous-pregnancy',
                methods=['GET', 'POST'])
@login_required
def record_previous_pregnancy(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False

    if request.method == 'POST':
        if 'audio' in request.files:
            audio = request.files.get('audio', None)
            filename = f'{mr_num}_previous_pregnancy.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)

            audio = Audio(
                audio_type='previous_pregnancy', file=audio_path,
                medical_record_number=mr_num)
            
            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success:
        error_response = make_response(
            render_template(
                'record_previous_pregnancy.html', patient=patient,
                mr_num=mr_num, nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_previous_pregnancy.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success)


@doctor.route('/patient/<string:mr_num>/record/condition-at-booking',
              methods=['GET', 'POST'])
@login_required 
def record_condition_at_booking(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False

    if request.method == 'POST':
        if 'audio' in request.files:
            audio = request.files.get('audio', None)
            filename = f'{mr_num}_condition_at_booking.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)

            audio = Audio(
                audio_type='condition_at_booking', file=audio_path,
                medical_record_number=mr_num)
            
            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success:
        error_response = make_response(
            render_template(
                'record_condition_at_booking.html', patient=patient,
                mr_num=mr_num, nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_condition_at_booking.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success)


@doctor.route('/patient/<string:mr_num>/record/present-pregnancy',
              methods=['GET', 'POST'])
@login_required
def record_present_pregnancy(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    audio_success = False
    form_success = False

    if request.method == 'POST':
        lmp_date = request.form.get('pres_preg_lmp_date')
        if lmp_date:
            lmp_date = datetime.datetime.strptime(
                lmp_date, "%Y-%m-%d").date().strftime("%d %B %Y")

        lmp_date_temp = datetime.datetime.strptime(lmp_date, "%d %B %Y").date()
        gestation_age = (
            datetime.datetime.now().date() - lmp_date_temp).days // 7
        edd = lmp_date_temp + datetime.timedelta(days=280)
        edd = edd.strftime("%d %B %Y")

        pres_preg = {
            'lmp_date': lmp_date,
            'gestation_age': gestation_age,
            'edd': edd
        }

        collection = DB['patients']

        collection.update_one(
            {'medical_record_number': mr_num},
            {'$set': pres_preg}
        )

        form_success = True

        if 'audio' in request.files:
            audio = request.files['audio']
            filename = f'{mr_num}_present_pregnancy.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)
            audio = Audio(
                audio_type='present_preg', file=audio_path,
                medical_record_number=mr_num)

            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success and not form_success:
        error_response = make_response(
            render_template(
                'record_present_pregnancy.html', patient=patient,
                mr_num=mr_num, nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_present_pregnancy.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success,
        form_success=form_success)


@doctor.route('/patient/<string:mr_num>/record/proposed-plan',
              methods=['GET', 'POST'])
@login_required
def record_proposed_plan(mr_num: str) -> str:
    def set_lab_test(lab_test: str) -> None:
        if lab_test in patient:
            lab_tests[lab_test] = True

    patient = Patient.get_patient(mr_num)
    date, time = patient['created_at'].strftime(
        "%d %B %Y"), patient['created_at'].strftime("%H:%M")
    mr_num = patient['medical_record_number']
    nurse_name = patient['recorded_by'].split()[0].capitalize()

    lab_tests = {
        'ultrasoundScan': False,
        'bloodGlucoseRandom': False,
        'urineCulture': False,
        'hbaic': False,
        'urineAnalysis': False,
        'rubellaAntibodyStatus': False,
        'bloodGroup': False,
        'antiHCV': False,
        'hbsag': False,
        'gtt': False,
        'cbc': False,
        'lft': False,
        'hvs': False
    }

    form_success = False
    audio_success = False

    if request.method == 'POST':
        lmp_date = request.form.get('lmp_date')
        next_follow_up_date = request.form.get('next_follow_up_date')
        if lmp_date:
            lmp_date = datetime.datetime.strptime(
                lmp_date, "%Y-%m-%d").date().strftime("%d %B %Y")

        if next_follow_up_date:
            next_follow_up_date = datetime.datetime.strptime(
                next_follow_up_date, "%Y-%m-%d").date().strftime("%d %B %Y")

        for (lab_test, _) in lab_tests.items():
            set_lab_test(lab_test)

        proposed_plan_form_data = {
            'lmp_date': lmp_date,
            'next_follow_up_date': next_follow_up_date,
            'lab_tests': lab_tests
        }

        collection = DB['patients']

        collection.update_one(
            {'medical_record_number': mr_num},
            {'$set': proposed_plan_form_data}
        )

        form_success = True

        if 'audio' in request.files:
            audio = request.files['audio']
            filename = f'{mr_num}_proposed_plan.mp3'
            audio_path = os.path.join('main/doctor/static/audio', filename)
            audio.save(audio_path)
            audio = Audio(
                audio_type='proposed_plan', file=audio_path,
                medical_record_number=mr_num)

            t = threading.Thread(
                target=audio.add_audio_and_transcribe, args=())
            t.start()

            audio_success = True

    if not audio_success and not form_success:
        error_response = make_response(
            render_template(
                'record_proposed_plan.html', patient=patient, mr_num=mr_num,
                nurse_name=nurse_name, date=date, time=time))
        error_response.set_cookie('error', 'true')
        return error_response
    
    return render_template(
        'record_proposed_plan.html', patient=patient, mr_num=mr_num,
        nurse_name=nurse_name, date=date, time=time, audio_success=audio_success,
        form_success=form_success)


@cache.cached(timeout=50, key_prefix='transcription')
def get_cached_transcription(
        audio_type: str, medical_record_number: str) -> str:
    audio = Audio(
        audio_type=audio_type, file=None,
        medical_record_number=medical_record_number)

    transcription = audio.get_transcription(audio_type)

    return transcription


@cache.cached(timeout=50, key_prefix='clarification_response')
def get_cached_clarification_response(
        file_path: str, transcription: str) -> str:
    prompting_engine = Prompting(
        file_path=file_path,
        transcription=transcription)

    clarification_response = prompting_engine.generate_responses()

    return clarification_response


@doctor.route('/patient/<string:mr_num>/transcribe/medical-history',
              methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_medical_history')
def transcribe_medical_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='medical_history', medical_record_number=mr_num)

    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Medical_History.txt',
        transcription=transcription)

    return render_template(
        'transcription_medical_history.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/family-history',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_family_history')
def transcribe_family_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='family_history', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Family_History.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_family_history.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/socioeconomic-history',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_socioeconomic_history')
def transcribe_socioeconomic_history(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='socioeconomic_history', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Socioeconomic_History.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_socioeconomic_history.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/previous-pregnancy',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_previous_pregnancy')
def transcribe_previous_pregnancy(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='previous_pregnancy', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Previous_Pregnancy.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_previous_pregnancy.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/condition-at-booking',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_condition_at_booking')
def transcribe_condition_at_booking(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='condition_at_booking', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Condition_at_Booking.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_condition_at_booking.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/present-pregnancy',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_present_pregnancy')
def transcribe_present_pregnancy(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='present_preg', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Present_Pregnancy.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_present_pregnancy.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)


@doctor.route('/patient/<string:mr_num>/transcribe/proposed-plan',
                methods=['GET', 'POST'])
@login_required
@cache.cached(timeout=50, key_prefix='transcription_proposed_plan')
def transcribe_proposed_plan(mr_num: str) -> str:
    patient = Patient.get_patient(mr_num)
    mr_num = patient['medical_record_number']

    transcription = get_cached_transcription(
        audio_type='proposed_plan', medical_record_number=mr_num)
    
    clarification_response = get_cached_clarification_response(
        file_path='main/scripts/Clarifications_Screen/Proposed_Plan.txt',
        transcription=transcription)
    
    return render_template(
        'transcription_proposed_plan.html',
        transcription=transcription, mr_num=mr_num,
        response=clarification_response)