from flask_caching import Cache
from flask_login import LoginManager

login_manager = LoginManager()

cache = Cache(config={
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
})