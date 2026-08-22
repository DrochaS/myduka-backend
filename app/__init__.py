from flask import Flask
from flask_cors import CORS
from sqlalchemy.pool import StaticPool

from app.config import Config
from app.extensions import db, jwt, mail, migrate


def create_app(config_object=Config):
    """Application factory for MyDuka Flask API."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite") and ":memory:" in uri:
        app.config.setdefault(
            "SQLALCHEMY_ENGINE_OPTIONS",
            {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
        )

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401

    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.clerk import clerk_bp
    from app.routes.merchant import merchant_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(clerk_bp, url_prefix="/api/clerk")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(merchant_bp, url_prefix="/api/merchant")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()

    return app
