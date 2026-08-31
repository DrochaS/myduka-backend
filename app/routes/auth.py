"""Authentication routes: register, login, invite, accept-invite, me."""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models import InviteToken, Role, User
from app.schemas import AcceptInviteSchema, InviteAdminSchema, LoginSchema, RegisterSchema
from app.utils.decorators import merchant_required
from app.utils.email import send_invite_email

auth_bp = Blueprint("auth", __name__)

login_schema = LoginSchema()
register_schema = RegisterSchema()
invite_schema = InviteAdminSchema()
accept_schema = AcceptInviteSchema()


@auth_bp.post("/register")
def register():
    """Register an account and return an access token."""
    try:
        data = register_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    email = data["email"].lower().strip()
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "User with this email already exists"}), 409

    user = User(
        email=email,
        full_name=data.get("full_name"),
        role=Role(data["role"]),
        is_active=True,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role.value, "store_id": None},
    )
    return jsonify({"access_token": access_token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    user = User.query.filter_by(email=data["email"].lower().strip()).first()
    if user is None or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    role_value = user.role.value if isinstance(user.role, Role) else user.role
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": role_value, "store_id": user.store_id},
    )
    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200


@auth_bp.post("/invite-admin")
@merchant_required
def invite_admin(merchant: User):
    try:
        data = invite_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    email = data["email"].lower().strip()
    existing = User.query.filter_by(email=email).first()
    if existing is not None:
        return jsonify({"error": "User with this email already exists"}), 409

    hours = current_app.config.get("INVITE_TOKEN_HOURS", 48)
    invite = InviteToken.create_invite(
        email=email,
        role=Role.ADMIN,
        invited_by_id=merchant.id,
        hours=hours,
        store_id=data.get("store_id"),
    )
    db.session.commit()

    invite_url = send_invite_email(email, invite.token, role="admin")
    payload = invite.to_dict()
    payload["invite_url"] = invite_url
    return jsonify(payload), 201


@auth_bp.post("/accept-invite")
def accept_invite():
    try:
        data = accept_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    invite = InviteToken.query.filter_by(token=data["token"]).first()
    if invite is None or not invite.is_valid():
        return jsonify({"error": "Invalid or expired invite token"}), 400

    if User.query.filter_by(email=invite.email).first() is not None:
        return jsonify({"error": "User already registered"}), 409

    user = User(
        email=invite.email,
        full_name=data.get("full_name"),
        role=invite.role,
        store_id=invite.store_id,
        is_active=True,
    )
    user.set_password(data["password"])
    invite.mark_used()
    db.session.add(user)
    db.session.commit()

    role_value = user.role.value if isinstance(user.role, Role) else user.role
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": role_value, "store_id": user.store_id},
    )
    return jsonify({"access_token": access_token, "user": user.to_dict()}), 201


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200
