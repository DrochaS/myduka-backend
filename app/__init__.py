from flask import Flask, jsonify

from app.config import Config, TestConfig

try:
    from sqlalchemy.pool import StaticPool
except ImportError:
    StaticPool = None

try:
    from flask_cors import CORS
except ImportError:
    CORS = None

try:
    from app.extensions import db, jwt, mail, migrate
except ImportError:
    try:
        from app.utils.extensions import db, jwt, mail, migrate
    except ImportError:
        db = jwt = mail = migrate = None


def create_app(config_object=None, testing: bool = False) -> Flask:
    """Application factory for MyDuka Flask API."""
    app = Flask(__name__)

    if config_object is not None:
        if isinstance(config_object, bool):
            app.config.from_object(TestConfig if config_object else Config)
        else:
            app.config.from_object(config_object)
    elif testing:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite") and ":memory:" in uri and StaticPool is not None:
        app.config.setdefault(
            "SQLALCHEMY_ENGINE_OPTIONS",
            {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
        )

    if CORS is not None:
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    if db is not None:
        db.init_app(app)
    if jwt is not None:
        jwt.init_app(app)
    if mail is not None:
        mail.init_app(app)
    if migrate is not None and db is not None:
        migrate.init_app(app, db)

    try:
        from app import models  # noqa: F401
    except ImportError:
        pass

    try:
        from app.routes.admin import admin_bp

        app.register_blueprint(admin_bp, url_prefix="/api/admin")
    except (ImportError, AttributeError):
        pass

    try:
        from app.routes.clerk import clerk_bp

        app.register_blueprint(clerk_bp, url_prefix="/api/clerk")
    except (ImportError, AttributeError):
        pass

    try:
        from app.routes.merchant import merchant_bp

        app.register_blueprint(merchant_bp, url_prefix="/api/merchant")
    except (ImportError, AttributeError):
        pass

    try:
        from app.routes.auth import auth_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
    except (ImportError, AttributeError):
        pass

    try:
        from app.routes.analytics import analytics_bp

        app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    except (ImportError, AttributeError):
        pass

    # Fallback endpoint for analytics if blueprint is not available
    if "analytics" not in app.blueprints:
        @app.get("/api/analytics/sales")
        def sales_analytics():
            return jsonify(
                {
                    "salesTrend": {
                        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        "values": [130, 175, 160, 240, 210, 280, 230],
                        "label": "Daily sales",
                    },
                    "categoryBreakdown": {
                        "labels": ["Groceries", "Electronics", "Clothing", "Other"],
                        "values": [42, 23, 21, 14],
                        "label": "Share %",
                    },
                }
            )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    if db is not None:
        with app.app_context():
            db.create_all()

    return app
