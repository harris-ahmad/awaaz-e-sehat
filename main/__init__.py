from flask import Flask
import os
import logging
from flask_admin import Admin

from .doctor import doctor
from .views import main
from .extensions import cache

admin = Admin()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = str(os.urandom(24).hex())

    app.register_blueprint(main)
    app.register_blueprint(doctor)

    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info('app startup')

    admin.init_app(app)
    cache.init_app(app)

    return app