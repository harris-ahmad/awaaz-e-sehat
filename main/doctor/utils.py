from faster_whisper import WhisperModel
from flask_caching import Cache


def init_whisper():
    model = None
    try:
        model = WhisperModel("/home/harris/Documents/Misc/model", device="cpu")
    except Exception:
        print("model not found")

    return model


def init_cache():
    config = {
        "DEBUG": True,  # some Flask specific configs
        "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
        "CACHE_DEFAULT_TIMEOUT": 300,
    }
    cache = Cache(config=config)
    return cache
