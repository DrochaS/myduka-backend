"""Route package for MyDuka Flask blueprints."""

from app.routes.admin import admin_bp
from app.routes.analytics import analytics_bp
from app.routes.auth import auth_bp
from app.routes.clerk import clerk_bp
from app.routes.merchant import merchant_bp

__all__ = [
    "auth_bp",
    "clerk_bp",
    "admin_bp",
    "merchant_bp",
    "analytics_bp",
]
