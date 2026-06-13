import os
from flask import Flask

def create_app():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base, 'templates'),
                static_folder=os.path.join(base, 'static'))
    app.secret_key = 'srmss-secret-key-change-in-production'

    from controllers.login import login_bp
    from controllers.dashboard import dashboard_bp
    from controllers.routes import routes_bp
    from controllers.vehicles import vehicles_bp
    from controllers.drivers import drivers_bp
    from controllers.scheduling import scheduling_bp
    from controllers.fuel import fuel_bp
    from controllers.maintenance import maintenance_bp
    from controllers.reports import reports_bp
    from controllers.assign_driver import assign_driver_bp
    from controllers.assign_route import assign_route_bp
    from controllers.approvals import approvals_bp
    from controllers.users import users_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(assign_driver_bp)
    app.register_blueprint(assign_route_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(fuel_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(users_bp)

    return app
