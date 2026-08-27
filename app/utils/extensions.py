"""Shared Flask extensions (initialized in create_app)."""

from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()
