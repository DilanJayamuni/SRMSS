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
    from controllers.drivers import drivers_bp
    from controllers.assign_driver import assign_driver_bp
    from controllers.scheduling import scheduling_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(assign_driver_bp)
    app.register_blueprint(scheduling_bp)

    return app
