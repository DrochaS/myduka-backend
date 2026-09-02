import os

from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect, text
from sqlalchemy.pool import StaticPool

from app.config import Config
from app.extensions import db, jwt, mail, migrate


def create_app(config_object=Config):
    """Application factory for MyDuka Flask API."""
    application = Flask(__name__)
    application.config.from_object(config_object)

    uri = application.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite") and ":memory:" in uri:
        application.config.setdefault(
            "SQLALCHEMY_ENGINE_OPTIONS",
            {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
        )

    cors_origins_env = os.getenv("CORS_ORIGINS")
    if cors_origins_env:
        raw_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
        cors_origins = "*" if "*" in raw_origins else raw_origins
    else:
        frontend_url = application.config.get("FRONTEND_URL", "http://localhost:5173")
        cors_origins = [o.strip() for o in frontend_url.split(",") if o.strip()]

    CORS(
        application,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    db.init_app(application)
    jwt.init_app(application)
    mail.init_app(application)
    migrate.init_app(application, db)

    from app import models  # noqa: F401

    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.clerk import clerk_bp
    from app.routes.merchant import merchant_bp
    from app.routes.storefront import storefront_bp

    application.register_blueprint(auth_bp, url_prefix="/api/auth")
    application.register_blueprint(clerk_bp, url_prefix="/api/clerk")
    application.register_blueprint(admin_bp, url_prefix="/api/admin")
    application.register_blueprint(merchant_bp, url_prefix="/api/merchant")
    application.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    application.register_blueprint(storefront_bp, url_prefix="/api/storefront")

    @application.get("/health")
    def health():
        return {"status": "ok"}

    with application.app_context():
        db.create_all()
        # This project initializes its local SQLite schema with create_all().
        # Add the optional product image column for existing development databases.
        if uri.startswith("sqlite"):
            columns = {
                column["name"] for column in inspect(db.engine).get_columns("products")
            }
            if "image_url" not in columns:
                db.session.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500)"))
                db.session.commit()

    return application
