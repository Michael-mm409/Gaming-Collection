import os
from flask import Flask
from flask_migrate import Migrate
from app.core.database import db
from app.config import Config

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

	from app.api.v1.routes import bp
	app.register_blueprint(bp)

	return app
