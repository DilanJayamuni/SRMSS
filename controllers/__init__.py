import os
from flask import Flask

def create_app():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base, 'templates'),
                static_folder=os.path.join(base, 'static'))
    app.secret_key = 'srmss-secret-key-change-in-production'

    return app
