# app/__init__.py
from flask import Flask
from app.config import config_by_name
from app.models import db


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)

    # Register blueprints as routes get built:
    # from app.routes.clerk import bp as clerk_bp
    # app.register_blueprint(clerk_bp)

    return app