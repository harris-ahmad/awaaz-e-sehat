from flask_wtf import FlaskForm

from wtforms import (
    StringField, 
    PasswordField, 
    SubmitField, 
    IntegerField, 
    SelectField, 
    RadioField,
    BooleanField,
    DateField,
)

from wtforms.validators import (
    DataRequired, 
    EqualTo, 
    Length, 
    Optional
)

class LoginForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), EqualTo('confirm_password')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), EqualTo('confirm_password')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpdateEmployeeProfile(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    submit = SubmitField('Update')

class PatientForm(FlaskForm):
    medical_record_number = StringField('Medical Record Number', validators=[DataRequired()])
    patient_name = StringField('Patient Name', validators=[DataRequired()])
    patient_cnic = StringField('Patient CNIC', validators=[Length(min=13, max=13)])
    patient_age = IntegerField('Patient Age', validators=[DataRequired()])
    patient_type = SelectField('Patient Type', choices=[('general', 'General'), ('private', 'Private'), \
                                    ('employee', 'Employee'), ('company_cases', 'Company Cases')], validators=[DataRequired()])
    weight_kg = IntegerField('Weight (kg)', validators=[Optional()])
    height_cm = IntegerField('Height (cm)', validators=[Optional()])
    b_bp_sys = IntegerField('Blood Pressure (Systolic)', validators=[Optional()])
    b_bp_dia = IntegerField('Blood Pressure (Diastolic)', validators=[Optional()])
    temperature = IntegerField('Temperature', validators=[Optional()])
    pulse = IntegerField('Pulse', validators=[Optional()])
    bsr = IntegerField('BSR', validators=[Optional()])
    urine_albumin = SelectField('Urine Albumin', choices=[('1+', '1+ (30 mg/dL)'), ('2+', '2+ (100 mg/dL)'), \
                                    ('3+', '3+ (300 mg/dL)'), ('4+', '4+ (1000 mg/dL)')], validators=[Optional()])
    hb = IntegerField('HB', validators=[Optional()])
    spO2 = IntegerField('SpO2', validators=[Optional()])
    submit = SubmitField('Submit')

class DoctorPatientForm(FlaskForm):
    has_allergies = RadioField('Does the patient have any allergies?', 
                               choices=[('yes', 'Yes'), ('no', 'No')], 
                               validators=[DataRequired()])
    allergy_drug = BooleanField('Drug')
    allergy_pollen = BooleanField('Pollen')
    allergy_dust = BooleanField('Dust')
    allergy_other = BooleanField('Other')
    gravida = SelectField('Gravida', choices=[('0', '0 / PG')] + [(str(n), str(n)) for n in range(1, 11)], validators=[Optional()])
    lmp_date = DateField('LMP Date', validators=[DataRequired()])
    submit = SubmitField('Submit')

class PatientSearchForm(FlaskForm):
    searched = StringField('Searched', validators=[DataRequired()])
    submit = SubmitField('Search')