from flask import (
    Flask, 
    render_template, 
    redirect, 
    url_for, 
    flash, 
    session, 
    Blueprint
)

from flask_login import (
    LoginManager, 
    login_user, 
    logout_user, 
    login_required, 
    current_user
)

from webforms import (
    LoginForm, 
    RegisterForm, 
    ForgotPasswordForm, 
    ChangePasswordForm, 
    PatientForm, 
    PatientSearchForm
)

from models import (
    User,
    Nurse,
    Patient
)

import datetime

# database
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(
    __name__,
    static_folder='assets',
)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

home_blueprint = Blueprint('home', __name__, template_folder='.')
doctor_blueprint = Blueprint('doctor', __name__, template_folder='doctor')
nurse_blueprint = Blueprint('nurse', __name__, template_folder='nurse')

# register blueprints
app.register_blueprint(doctor_blueprint, url_prefix='/doctor')
app.register_blueprint(nurse_blueprint, url_prefix='/nurse')
app.register_blueprint(home_blueprint, url_prefix='/')

# database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'nurse_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

####################### INDEX ROUTE #######################
@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')


####################### NURSE ROUTES #######################
@app.route('/nurse/dashboard')
@login_required
def nurse_dashboard():
    if 'employee_code' in session:
        employee_code = session['employee_code']
        first_name = User.query.filter_by(employee_code=employee_code).first()
        first_name = first_name.full_name.split(' ')[0].capitalize()
        curr_date, curr_time = datetime.datetime.utcnow().date(), datetime.datetime.utcnow().time().isoformat(timespec='minutes')
        form = PatientSearchForm()
        return render_template('dashboard.html', employee_code=employee_code, first_name=first_name, curr_date=curr_date, curr_time=curr_time, form=form)
    return redirect(url_for('nurse_login'))


@app.route('/nurse/register', methods=['GET', 'POST'])
def nurse_register():
    form = RegisterForm()
    if form.validate_on_submit():
        print(form.employee_code.data, form.full_name.data, form.password.data)
        existing_user = User.query.filter_by(employee_code=form.employee_code.data).first()
        if existing_user:
            flash('Employee code already exists!', 'danger')
            return redirect(url_for('nurse_register'))
        user = User(
            employee_code=form.employee_code.data,
            full_name=form.full_name.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        nurse = Nurse(
            user_id=user.id
        )
        db.session.add(nurse)
        db.session.commit()
        flash('Registered successfully!', 'success')
        return redirect(url_for('nurse_login'))
    return render_template('signup.html', form=form)


@app.route('/nurse/login', methods=['GET', 'POST'])
def nurse_login():
    form = LoginForm()
    if form.validate_on_submit():
        print(form.employee_code.data, form.password.data)
        user = User.query.filter_by(employee_code=form.employee_code.data).first()
        if user and User.verify_password(user.password_hash, form.password.data):
            login_user(user)
            session['employee_code'] = user.employee_code
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Invalid employee code or password!', category='warning')
    return render_template('login.html', form=form)


@app.route('/nurse/vitals', methods=['GET', 'POST'])
@login_required
def nurse_vitals():
    form = PatientForm()
    if form.validate_on_submit():
        print(form.patient_name.data, form.patient_cnic.data, form.patient_age.data, form.patient_type.data)
        patient = Patient.query.filter_by(medical_record_number=form.medical_record_number.data).first()
        if not patient:
            vitals = Patient(
                medical_record_number=form.medical_record_number.data,
                patient_name=form.patient_name.data,
                patient_cnic=form.patient_cnic.data,
                patient_age=form.patient_age.data,
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
                created_at=datetime.datetime.utcnow().date()
            )
            db.session.add(vitals)
            db.session.commit()
            flash('Vitals recorded successfully!', 'success')
            return redirect(url_for('nurse_thank_you'))
        if patient and patient.created_at.date() == datetime.datetime.utcnow().date():
            flash('Patient already exists!', 'danger')
            return redirect(url_for('nurse_vitals'))
        elif patient and patient.created_at.date() != datetime.datetime.utcnow().date():
            flash('Patient had visited earlier in the day!', 'danger')
            patient.visit_number += 1
            db.session.commit()
            return redirect(url_for('nurse_vitals'))
        flash('Vitals recorded successfully!', 'success')
        return redirect(url_for('nurse_thank_you'))
    return render_template('vitals.html', form=form)

@app.route('/nurse/thank-you', methods=['GET', 'POST'])
@login_required
def nurse_thank_you():
    return render_template('thank-you.html')

@app.route('/nurse/search', methods=['GET', 'POST'])
@login_required
def nurse_search():
    form = PatientSearchForm()
    searched = form.searched.data
    patients = Patient.query.all()
    if form.validate_on_submit():
        patients = Patient.query.filter_by(patient_name=form.searched.data).all()
    return render_template(
        'patients.html',
        patients=patients,
        searched=searched,
    )

@app.route('/nurse/patients/<int:medical_record_number>')
@login_required
def nurse_patient(medical_record_number):
    patient = Patient.query.filter_by(medical_record_number=medical_record_number).first()
    # get the timestamp when this data was recorded
    date = patient.created_at.date()
    time = patient.created_at.time().isoformat(timespec='minutes')
    mr_num = patient.medical_record_number
    nurse_name = User.query.filter_by(employee_code=session['employee_code']).first()
    nurse_name = nurse_name.full_name.split(' ')[0].capitalize()
    return render_template('patient.html', patient=patient, date=date, time=time, mr_num=mr_num, nurse_name=nurse_name)


@app.route('/nurse/forgot-password', methods=['GET', 'POST'])
@login_required
def nurse_forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(employee_code=session['employee_code']).first()
        if user and User.verify_password(user.password_hash, form.old_password.data):
            user.password = form.new_password.data
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Invalid old password!', 'danger')
    return render_template('forgot-password.html', form=form)


@app.route('/nurse/profile')
@login_required
def nurse_update_profile():
    pass

@app.route('/nurse/change-password', methods=['GET', 'POST'])
@login_required
def nurse_change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(employee_code=session['employee_code']).first()
        if user and User.verify_password(user.password_hash, form.current_password.data):
            user.password = form.new_password.data
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('nurse_dashboard'))
        else:
            flash('Invalid old password!', 'danger')
    return render_template('change-password.html', form=form)

@app.route('/nurse/logout')
@login_required
def nurse_logout():
    logout_user()
    session.pop('employee_code', None)
    return redirect(url_for('home'))