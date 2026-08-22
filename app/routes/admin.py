"""Admin routes: clerks, supply requests, payments, performance reports."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import func

from app.extensions import db
from app.models import (
    InviteToken,
    PaymentStatus,
    Role,
    StockEntry,
    SupplyRequest,
    SupplyRequestStatus,
    User,
)
from app.schemas import CreateClerkSchema, PaymentUpdateSchema
from app.utils.decorators import admin_required
from app.utils.email import send_invite_email

admin_bp = Blueprint("admin", __name__)

clerk_schema = CreateClerkSchema()
payment_schema = PaymentUpdateSchema()


def _admin_store_id(admin: User):
    if admin.store_id is None:
        return None, (jsonify({"error": "Admin is not assigned to a store"}), 400)
    return admin.store_id, None


@admin_bp.get("/clerks")
@admin_required
def list_clerks(admin: User):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    clerks = User.query.filter_by(role=Role.CLERK, store_id=store_id).all()
    return jsonify([c.to_dict() for c in clerks]), 200


@admin_bp.post("/clerks")
@admin_required
def create_clerk(admin: User):
    store_id, err = _admin_store_id(admin)
    if err:
        return err

    try:
        data = clerk_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    email = data["email"].lower().strip()
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "User with this email already exists"}), 409

    use_invite = data.get("invite") or not data.get("password")

    if use_invite:
        from flask import current_app

        hours = current_app.config.get("INVITE_TOKEN_HOURS", 48)
        invite = InviteToken.create_invite(
            email=email,
            role=Role.CLERK,
            invited_by_id=admin.id,
            hours=hours,
            store_id=store_id,
        )
        db.session.commit()
        invite_url = send_invite_email(email, invite.token, role="clerk")
        payload = invite.to_dict()
        payload["invite_url"] = invite_url
        return jsonify(payload), 201

    clerk = User(
        email=email,
        full_name=data.get("full_name"),
        role=Role.CLERK,
        store_id=store_id,
        is_active=True,
    )
    clerk.set_password(data["password"])
    db.session.add(clerk)
    db.session.commit()
    return jsonify(clerk.to_dict()), 201


@admin_bp.patch("/clerks/<int:clerk_id>/deactivate")
@admin_required
def deactivate_clerk(admin: User, clerk_id: int):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    clerk = User.query.filter_by(id=clerk_id, role=Role.CLERK, store_id=store_id).first()
    if clerk is None:
        return jsonify({"error": "Clerk not found"}), 404
    clerk.is_active = False
    db.session.commit()
    return jsonify(clerk.to_dict()), 200


@admin_bp.delete("/clerks/<int:clerk_id>")
@admin_required
def delete_clerk(admin: User, clerk_id: int):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    clerk = User.query.filter_by(id=clerk_id, role=Role.CLERK, store_id=store_id).first()
    if clerk is None:
        return jsonify({"error": "Clerk not found"}), 404
    db.session.delete(clerk)
    db.session.commit()
    return jsonify({"message": "Clerk deleted"}), 200


@admin_bp.get("/supply-requests")
@admin_required
def list_supply_requests(admin: User):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    status_filter = request.args.get("status")
    query = SupplyRequest.query.filter_by(store_id=store_id)
    if status_filter:
        try:
            query = query.filter_by(status=SupplyRequestStatus(status_filter))
        except ValueError:
            return jsonify({"error": "Invalid status"}), 400
    items = query.order_by(SupplyRequest.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items]), 200


@admin_bp.post("/supply-requests/<int:request_id>/approve")
@admin_required
def approve_supply_request(admin: User, request_id: int):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    supply = SupplyRequest.query.filter_by(id=request_id, store_id=store_id).first()
    if supply is None:
        return jsonify({"error": "Supply request not found"}), 404
    if supply.status != SupplyRequestStatus.PENDING:
        return jsonify({"error": "Request already reviewed"}), 400

    supply.status = SupplyRequestStatus.APPROVED
    supply.reviewed_by_id = admin.id
    supply.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(supply.to_dict()), 200


@admin_bp.post("/supply-requests/<int:request_id>/decline")
@admin_required
def decline_supply_request(admin: User, request_id: int):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    supply = SupplyRequest.query.filter_by(id=request_id, store_id=store_id).first()
    if supply is None:
        return jsonify({"error": "Supply request not found"}), 404
    if supply.status != SupplyRequestStatus.PENDING:
        return jsonify({"error": "Request already reviewed"}), 400

    supply.status = SupplyRequestStatus.DECLINED
    supply.reviewed_by_id = admin.id
    supply.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(supply.to_dict()), 200


@admin_bp.get("/payments")
@admin_required
def list_payments(admin: User):
    store_id, err = _admin_store_id(admin)
    if err:
        return err
    status_filter = request.args.get("status")
    query = StockEntry.query.filter_by(store_id=store_id)
    if status_filter:
        try:
            query = query.filter_by(payment_status=PaymentStatus(status_filter))
        except ValueError:
            return jsonify({"error": "Invalid payment status"}), 400
    entries = query.order_by(StockEntry.created_at.desc()).all()
    return jsonify([e.to_dict() for e in entries]), 200


@admin_bp.patch("/payments/<int:entry_id>")
@admin_required
def update_payment(admin: User, entry_id: int):
    store_id, err = _admin_store_id(admin)
    if err:
        return err

    try:
        data = payment_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    entry = StockEntry.query.filter_by(id=entry_id, store_id=store_id).first()
    if entry is None:
        return jsonify({"error": "Payment / stock entry not found"}), 404

    entry.payment_status = PaymentStatus(data["payment_status"])
    db.session.commit()
    return jsonify(entry.to_dict()), 200


@admin_bp.get("/reports/clerk-performance")
@admin_required
def clerk_performance(admin: User):
    store_id, err = _admin_store_id(admin)
    if err:
        return err

    rows = (
        db.session.query(
            User.id,
            User.email,
            User.full_name,
            func.count(StockEntry.id).label("entries_count"),
            func.coalesce(func.sum(StockEntry.quantity_received), 0).label("qty_received"),
            func.coalesce(func.sum(StockEntry.spoilt_quantity), 0).label("qty_spoilt"),
        )
        .outerjoin(
            StockEntry,
            (StockEntry.clerk_id == User.id) & (StockEntry.store_id == store_id),
        )
        .filter(User.role == Role.CLERK, User.store_id == store_id)
        .group_by(User.id)
        .all()
    )

    clerks = [
        {
            "clerk_id": r.id,
            "email": r.email,
            "full_name": r.full_name,
            "entries_count": int(r.entries_count),
            "qty_received": int(r.qty_received),
            "qty_spoilt": int(r.qty_spoilt),
        }
        for r in rows
    ]

    # Chart.js-friendly series
    labels = [c["email"] for c in clerks]
    return jsonify(
        {
            "clerks": clerks,
            "entriesByClerk": {
                "labels": labels,
                "values": [c["entries_count"] for c in clerks],
                "label": "Stock entries",
            },
            "spoiltByClerk": {
                "labels": labels,
                "values": [c["qty_spoilt"] for c in clerks],
                "label": "Spoilt units",
            },
        }
    ), 200
