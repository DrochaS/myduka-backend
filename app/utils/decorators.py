"""Role-based access decorators."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models import Role, User


def _current_user():
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return db.session.get(User, int(user_id))


def role_required(*roles):
    """Require an authenticated user whose role is one of ``roles``."""

    allowed = {r.value if isinstance(r, Role) else r for r in roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _current_user()
            if user is None:
                return jsonify({"error": "Unauthorized"}), 401
            if not user.is_active:
                return jsonify({"error": "Account is deactivated"}), 403
            role_value = user.role.value if isinstance(user.role, Role) else user.role
            if role_value not in allowed:
                return jsonify({"error": "Forbidden"}), 403
            return fn(user, *args, **kwargs)

        return wrapper

    return decorator


def merchant_required(fn):
    return role_required(Role.MERCHANT)(fn)


def admin_required(fn):
    return role_required(Role.ADMIN)(fn)


def clerk_required(fn):
    return role_required(Role.CLERK)(fn)


def admin_or_merchant_required(fn):
    return role_required(Role.ADMIN, Role.MERCHANT)(fn)


def get_claims_role():
    claims = get_jwt()
    return claims.get("role")
