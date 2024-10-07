from . import views

from flask import Blueprint
from faster_whisper import WhisperModel
from flask_caching import Cache


def init_cache():
    config = {
        "DEBUG": True,  # some Flask specific configs
        "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
        "CACHE_DEFAULT_TIMEOUT": 300,
    }
    cache = Cache(config=config)
    return cache


def init_whisper():
    model = None
    try:
        model = WhisperModel("/home/harris/Documents/Misc/model", device="cpu")
    except Exception:
        print("model not found")

    return model


doctor = Blueprint(
    "doctor",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/doctor",
    static_url_path="/static/doctor",
)

__all__ = ["views"]
