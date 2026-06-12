import os
from flask import Flask

def create_app():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base, 'templates'),
                static_folder=os.path.join(base, 'static'))
    app.secret_key = 'srmss-secret-key-change-in-production'

    from controllers.login import login_bp
    from controllers.users import users_bp
    from controllers.vehicles import vehicles_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(vehicles_bp)

    return app
