"""Clerk routes: stock entries and supply requests."""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models import (
    PaymentStatus,
    Product,
    StockEntry,
    SupplyRequest,
    SupplyRequestStatus,
    User,
)
from app.schemas import SpoiltGoodsSchema, StockEntrySchema, SupplyRequestCreateSchema
from app.utils.decorators import clerk_required

clerk_bp = Blueprint("clerk", __name__)

stock_schema = StockEntrySchema()
spoilt_schema = SpoiltGoodsSchema()
supply_schema = SupplyRequestCreateSchema()


def _require_store(clerk: User):
    if clerk.store_id is None:
        return None, (jsonify({"error": "Clerk is not assigned to a store"}), 400)
    return clerk.store_id, None


@clerk_bp.get("/products")
@clerk_required
def list_products(clerk: User):
    store_id, err = _require_store(clerk)
    if err:
        return err

    products = Product.query.filter_by(store_id=store_id, is_active=True).order_by(Product.name).all()
    return jsonify([product.to_dict() for product in products]), 200


@clerk_bp.get("/stock-entries")
@clerk_required
def list_stock_entries(clerk: User):
    store_id, err = _require_store(clerk)
    if err:
        return err
    entries = (
        StockEntry.query.filter_by(clerk_id=clerk.id, store_id=store_id)
        .order_by(StockEntry.created_at.desc())
        .all()
    )
    return jsonify([e.to_dict() for e in entries]), 200


@clerk_bp.post("/stock-entries")
@clerk_required
def create_stock_entry(clerk: User):
    store_id, err = _require_store(clerk)
    if err:
        return err

    try:
        data = stock_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    product = db.session.get(Product, data["product_id"])
    if product is None or product.store_id != store_id:
        return jsonify({"error": "Product not found in your store"}), 404

    payment = PaymentStatus(data["payment_status"])
    entry = StockEntry(
        product_id=product.id,
        store_id=store_id,
        clerk_id=clerk.id,
        quantity_received=data["quantity_received"],
        stock_quantity=data["stock_quantity"],
        spoilt_quantity=data.get("spoilt_quantity", 0),
        buy_price=data["buy_price"],
        sell_price=data["sell_price"],
        payment_status=payment,
    )

    # Update product on-hand stock and prices
    product.quantity_in_stock = data["stock_quantity"]
    product.buy_price = data["buy_price"]
    product.sell_price = data["sell_price"]

    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@clerk_bp.patch("/stock-entries/<int:entry_id>/spoilt")
@clerk_required
def report_spoilt_goods(clerk: User, entry_id: int):
    store_id, err = _require_store(clerk)
    if err:
        return err

    try:
        data = spoilt_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    entry = StockEntry.query.filter_by(
        id=entry_id, clerk_id=clerk.id, store_id=store_id
    ).first()
    if entry is None:
        return jsonify({"error": "Stock entry not found"}), 404

    product = db.session.get(Product, entry.product_id)
    quantity = data["spoilt_quantity"]
    if product is None or quantity > product.quantity_in_stock:
        return jsonify({"error": "Spoilt quantity exceeds stock on hand"}), 400

    entry.spoilt_quantity += quantity
    entry.stock_quantity -= quantity
    product.quantity_in_stock -= quantity
    db.session.commit()
    return jsonify(entry.to_dict()), 200


@clerk_bp.get("/supply-requests")
@clerk_required
def list_own_supply_requests(clerk: User):
    requests_q = (
        SupplyRequest.query.filter_by(clerk_id=clerk.id)
        .order_by(SupplyRequest.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in requests_q]), 200


@clerk_bp.post("/supply-requests")
@clerk_required
def create_supply_request(clerk: User):
    store_id, err = _require_store(clerk)
    if err:
        return err

    try:
        data = supply_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    product = db.session.get(Product, data["product_id"])
    if product is None or product.store_id != store_id:
        return jsonify({"error": "Product not found in your store"}), 404

    supply = SupplyRequest(
        product_id=product.id,
        store_id=store_id,
        clerk_id=clerk.id,
        quantity_requested=data["quantity_requested"],
        notes=data.get("notes"),
        status=SupplyRequestStatus.PENDING,
    )
    db.session.add(supply)
    db.session.commit()
    return jsonify(supply.to_dict()), 201
