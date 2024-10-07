import datetime
from flask import session
import bcrypt
from .utils import init_whisper
from ..database import CLIENT as client
from bson import binary
from flask_login import UserMixin

model = init_whisper()


class Nurse(UserMixin):
    def __init__(
        self, employee_code, full_name, password, created_at=datetime.datetime.now()
    ):
        super().__init__()
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password
        self.id = employee_code

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    def add_nurse(self):
        db = client["users"]
        collection = db["nurse"]
        existing_nurse = self.check_existing()
        if existing_nurse is False:
            new_nurse = dict(
                employee_code="nurse_" + self.employee_code,
                full_name=self.full_name,
                password=bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()),
                created_at=self.created_at,
            )
            collection.insert_one(new_nurse)
            return True
        else:
            return False

    def check_existing(self):
        db = client["users"]
        collection = db["nurse"]
        existing_nurse = collection.find_one({"employee_code": self.employee_code})
        return True if existing_nurse is not None else False

    @staticmethod
    def get_nurse(employee_code):
        db = client["users"]
        collection = db["nurse"]
        nurse = collection.find_one({"employee_code": employee_code})
        return nurse

    def __repr__(self):
        return f"<Nurse {self.employee_code}>"


class Patient:
    def __init__(
        self,
        medical_record_number,
        full_name,
        cnic,
        age,
        patient_type,
        weight_kg,
        height_cm,
        b_bp_sys,
        b_bp_dia,
        temperature,
        pulse,
        bsr,
        urine_albumin,
        hb,
        spO2,
        created_at=datetime.datetime.now(),
        visit_number=1,
    ) -> None:
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
        self.recorded_by = (
            Nurse.get_nurse(session["employee_code"])["full_name"]
            .split()[0]
            .capitalize()
        )

    def add_patient(self):
        db = client["users"]
        collection = db["patients"]
        existing_patient = collection.find_one(
            {"medical_record_number": self.medical_record_number}
        )
        self.recorded_by = (
            Nurse.get_nurse(session["employee_code"])["full_name"]
            .split()[0]
            .capitalize()
        )
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
                recorded_by=self.recorded_by,
            )
            collection.insert_one(new_patient)
            return True
        else:
            return False

    @staticmethod
    def get_patient(medical_record_number):
        db = client["users"]
        collection = db["patients"]
        patient = collection.find_one({"medical_record_number": medical_record_number})
        return patient

    @staticmethod
    def check_existing(medical_record_number):
        db = client["users"]
        collection = db["patients"]
        existing_patient = collection.find_one(
            {"medical_record_number": medical_record_number}
        )
        return True if existing_patient is not None else False

    def __repr__(self):
        return f"<Patient {self.medical_record_number}>"


class Doctor(UserMixin):
    def __init__(
        self,
        employee_code,
        full_name="",
        password="",
        created_at=datetime.datetime.now(),
    ):
        self.employee_code = employee_code
        self.full_name = full_name
        self.created_at = created_at
        self.password = password
        self.id = employee_code

    @property
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    def add_doctor(self):
        db = client["users"]
        collection = db["doctor"]
        existing_doctor = self.check_existing()
        if existing_doctor is False:
            new_doctor = dict(
                employee_code="doctor_" + self.employee_code,
                full_name=self.full_name,
                password=bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()),
                created_at=self.created_at,
            )
            collection.insert_one(new_doctor)
            return True
        else:
            return False

    def check_existing(self):
        db = client["users"]
        collection = db["doctor"]
        existing_doctor = collection.find_one({"employee_code": self.employee_code})
        return True if existing_doctor is not None else False

    @staticmethod
    def get_doctor(employee_code):
        db = client["users"]
        collection = db["doctor"]
        doctor = collection.find_one({"employee_code": employee_code})
        return doctor

    def __repr__(self):
        return f"<Doctor {self.employee_code}>"


class Audio:
    def __init__(self, audio_type, file, medical_record_number):
        self.audio_type = audio_type
        self.audio_path = file
        self.medical_record_number = medical_record_number
        if file is not None:
            self.audio_binary = binary.Binary(open(file, "rb").read())
        else:
            self.audio_binary = None

        self.transcribed_text = ""

    def add_audio_and_transcribe(self):
        db = client["users"]
        collection = db["audios"]
        existing_audio = collection.find_one(
            {"medical_record_number": self.medical_record_number}
        )
        if not existing_audio:
            new_audio = {
                "medical_record_number": self.medical_record_number,
                "audios": [
                    {"audio_type": self.audio_type, "audio_binary": self.audio_binary}
                ],
            }

            collection.insert_one(new_audio)
            print("Audio added to database")

            segments, _ = model.transcribe(
                self.audio_path, language="ur", task="transcribe"
            )
            predicted_text = " ".join([segment[4] for segment in segments])
            self.transcribed_text = predicted_text

            new_transcription = {
                "medical_record_number": self.medical_record_number,
                "audios": [
                    {"audio_type": self.audio_type, "transcription": predicted_text}
                ],
            }

            collection.update_one(
                {"medical_record_number": self.medical_record_number},
                {"$push": {"transcriptions": new_transcription}},
            )

            print("Audio processed and transcribed")

            return True
        else:
            audios = existing_audio.get("audios", [])
            for audio in audios:
                if audio["audio_type"] == self.audio_type:
                    return False
            audios.append(
                {"audio_type": self.audio_type, "audio_binary": self.audio_binary}
            )
            collection.update_one(
                {"medical_record_number": self.medical_record_number},
                {"$set": {"audios": audios}},
            )

        segments, _ = model.transcribe(
            self.audio_path, language="ur", task="transcribe"
        )
        predicted_text = " ".join([segment[4] for segment in segments])
        self.transcribed_text = predicted_text

        new_transcription = {
            "medical_record_number": self.medical_record_number,
            "audios": [
                {"audio_type": self.audio_type, "transcription": predicted_text}
            ],
        }

        collection.update_one(
            {"medical_record_number": self.medical_record_number},
            {"$push": {"transcriptions": new_transcription}},
        )

        print("Audio processed and transcribed")
        return True

    def add_clarification_question(self, question):
        db = client["users"]
        collection = db["audios"]
        existing_audio = collection.find_one(
            {"medical_record_number": self.medical_record_number}
        )
        if not existing_audio:
            return False
        else:
            audios = existing_audio.get("audios", [])
            for audio in audios:
                if audio["audio_type"] == self.audio_type:
                    audio["clarification_question"] = question
                    collection.update_one(
                        {"medical_record_number": self.medical_record_number},
                        {"$set": {"audios": audios}},
                    )
                    return True
            return False

    def get_transcription(self, audio_type):
        db = client["users"]
        collection = db["audios"]
        existing_audio = collection.find_one(
            {"medical_record_number": self.medical_record_number}
        )
        if existing_audio:
            transcriptions = existing_audio.get("transcriptions", [])
            for transcription in transcriptions:
                audios = transcription.get("audios", [])
                for audio in audios:
                    if audio["audio_type"] == audio_type:
                        return audio.get("transcription", "")
        return ""
