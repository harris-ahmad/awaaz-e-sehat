from flask import Blueprint


doctor = Blueprint(
    "doctor",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/doctor",
    static_url_path="/static/doctor",
)
