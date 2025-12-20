from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .db import db
import os

def create_app():
    # Dynamically determine the correct static and template folder
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    templates_path = os.path.join(base_dir, 'templates')
    static_path = os.path.join(base_dir, 'static')
    print(f"[Flask] Using templates path: {templates_path}")
    print(f"[Flask] Using static path: {static_path}")
    app = Flask(__name__, template_folder=templates_path, static_folder=static_path)
    app.config.from_object(Config)
    db.init_app(app)
    Migrate(app, db)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
