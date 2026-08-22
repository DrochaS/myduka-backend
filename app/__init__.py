from flask import Flask
from flask_cors import CORS

from app.config import Config


def create_app(config_object=Config):
    """Application factory for MyDuka Flask API."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.routes.analytics import analytics_bp

    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
