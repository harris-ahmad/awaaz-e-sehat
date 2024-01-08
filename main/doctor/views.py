from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
    Response,
    make_response
)

import datetime
import threading
import os

from . import doctor
from .models import Patient, Audio, Doctor
from ..database import DB
from .forms import PatientSearchForm

@doctor.route('/dashboard')
def dashboard():
    form = PatientSearchForm()
    return render_template(
        template_name_or_list='dashboard.html',
        form=form,
    )

@doctor.route('/logout')
def logout():
    session.pop('employee_code', None)
    return redirect(url_for('doctor_dashboard'))


@doctor.route('/search')
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
                return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(
                url_for(
                    'patient',
                    medical_record_number=patients[0]
                    ['medical_record_number']))
        
    return redirect(url_for('dashboard'))


@doctor.get('/patient/<string:mr_num>')
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


@doctor.route('/patient/<string:mr_num>/transcribe/medical-history',
              methods=['GET', 'POST'])
def transcribe_medical_history(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/family-history',
                methods=['GET', 'POST'])
def transcribe_family_history(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/socioeconomic-history',
                methods=['GET', 'POST'])
def transcribe_socioeconomic_history(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/previous-pregnancy',
                methods=['GET', 'POST'])
def transcribe_previous_pregnancy(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/condition-at-booking',
                methods=['GET', 'POST'])
def transcribe_condition_at_booking(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/present-pregnancy',
                methods=['GET', 'POST'])
def transcribe_present_pregnancy(mr_num: str) -> str:
    pass


@doctor.route('/patient/<string:mr_num>/transcribe/proposed-plan',
                methods=['GET', 'POST'])
def transcribe_proposed_plan(mr_num: str) -> str:
    pass