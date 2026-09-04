"""Merchant routes: admins, stores, store/product reports."""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import case, func

from app.extensions import db
from app.models import (
    InviteToken,
    Order,
    OrderItem,
    PaymentStatus,
    Product,
    Role,
    StockEntry,
    Store,
    SupplyRequest,
    User,
)
from app.schemas import ProductCreateSchema, StoreCreateSchema
from app.utils.decorators import merchant_required

merchant_bp = Blueprint("merchant", __name__)

store_schema = StoreCreateSchema()
product_schema = ProductCreateSchema()


@merchant_bp.get("/admins")
@merchant_required
def list_admins(merchant: User):
    admins = User.query.filter_by(role=Role.ADMIN).all()
    return jsonify([a.to_dict() for a in admins]), 200


@merchant_bp.patch("/admins/<int:admin_id>/deactivate")
@merchant_required
def deactivate_admin(merchant: User, admin_id: int):
    admin = User.query.filter_by(id=admin_id, role=Role.ADMIN).first()
    if admin is None:
        return jsonify({"error": "Admin not found"}), 404
    admin.is_active = False
    db.session.commit()
    return jsonify(admin.to_dict()), 200


@merchant_bp.delete("/admins/<int:admin_id>")
@merchant_required
def delete_admin(merchant: User, admin_id: int):
    admin = User.query.filter_by(id=admin_id, role=Role.ADMIN).first()
    if admin is None:
        return jsonify({"error": "Admin not found"}), 404
    db.session.delete(admin)
    db.session.commit()
    return jsonify({"message": "Admin deleted"}), 200


@merchant_bp.get("/stores")
@merchant_required
def list_stores(merchant: User):
    stores = Store.query.order_by(Store.name).all()
    return jsonify([s.to_dict() for s in stores]), 200


@merchant_bp.post("/stores")
@merchant_required
def create_store(merchant: User):
    try:
        data = store_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    if Store.query.filter_by(name=data["name"]).first() is not None:
        return jsonify({"error": "Store name already exists"}), 409

    store = Store(name=data["name"], location=data.get("location"))
    db.session.add(store)
    db.session.commit()
    return jsonify(store.to_dict()), 201


@merchant_bp.delete("/stores/<int:store_id>")
@merchant_required
def delete_store(merchant: User, store_id: int):
    store = db.session.get(Store, store_id)
    if store is None:
        return jsonify({"error": "Branch not found"}), 404

    order_count = Order.query.filter_by(store_id=store.id).count()
    if order_count > 0:
        return jsonify(
            {
                "error": (
                    f"Cannot delete this branch: it has {order_count} order(s) on record. "
                    "Orders must be kept for historical records."
                )
            }
        ), 409

    # Unassign any admins/clerks tied to this branch rather than deleting their accounts.
    User.query.filter_by(store_id=store.id).update({"store_id": None})

    # Pending invites tied to this store no longer make sense once it's gone.
    InviteToken.query.filter_by(store_id=store.id).delete()

    # Supply requests reference the store directly and aren't cascade-deleted
    # through the Product relationship, so clear them explicitly.
    SupplyRequest.query.filter_by(store_id=store.id).delete()

    # Products (and their StockEntries, via the Product model's own cascade)
    # are removed automatically by Store's "all, delete-orphan" cascade below.
    db.session.delete(store)
    db.session.commit()

    return jsonify({"message": "Branch deleted"}), 200


@merchant_bp.post("/products")
@merchant_required
def create_product(merchant: User):
    """Convenience endpoint so merchants can seed products for stores."""
    try:
        data = product_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "details": ve.messages}), 400

    store = db.session.get(Store, data["store_id"])
    if store is None:
        return jsonify({"error": "Store not found"}), 404

    product = Product(
        name=data["name"],
        category=data.get("category"),
        sku=data.get("sku"),
        image_url=data.get("image_url"),
        store_id=store.id,
        buy_price=data.get("buy_price", 0.0),
        sell_price=data.get("sell_price", 0.0),
        quantity_in_stock=data.get("quantity_in_stock", 0),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@merchant_bp.delete("/products/<int:product_id>")
@merchant_required
def delete_product(merchant: User, product_id: int):
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    order_count = OrderItem.query.filter_by(product_id=product.id).count()
    if order_count > 0:
        return jsonify(
            {"error": f"Cannot delete: this product appears in {order_count} order(s)."}
        ), 409

    request_count = SupplyRequest.query.filter_by(product_id=product.id).count()
    if request_count > 0:
        return jsonify(
            {"error": f"Cannot delete: this product has {request_count} supply request(s) on record."}
        ), 409

    # StockEntry rows are removed automatically via Product's own cascade.
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200


@merchant_bp.get("/reports/stores")
@merchant_required
def store_reports(merchant: User):
    """Per-store paid/unpaid supplier payment summary."""
    paid_sum = func.coalesce(
        func.sum(
            case(
                (StockEntry.payment_status == PaymentStatus.PAID, StockEntry.buy_price * StockEntry.quantity_received),
                else_=0,
            )
        ),
        0,
    )
    unpaid_sum = func.coalesce(
        func.sum(
            case(
                (
                    StockEntry.payment_status == PaymentStatus.NOT_PAID,
                    StockEntry.buy_price * StockEntry.quantity_received,
                ),
                else_=0,
            )
        ),
        0,
    )
    paid_count = func.coalesce(
        func.sum(case((StockEntry.payment_status == PaymentStatus.PAID, 1), else_=0)),
        0,
    )
    unpaid_count = func.coalesce(
        func.sum(case((StockEntry.payment_status == PaymentStatus.NOT_PAID, 1), else_=0)),
        0,
    )

    rows = (
        db.session.query(
            Store.id,
            Store.name,
            paid_sum.label("paid_amount"),
            unpaid_sum.label("unpaid_amount"),
            paid_count.label("paid_entries"),
            unpaid_count.label("unpaid_entries"),
            func.count(StockEntry.id).label("total_entries"),
        )
        .outerjoin(StockEntry, StockEntry.store_id == Store.id)
        .group_by(Store.id)
        .order_by(Store.name)
        .all()
    )

    stores = [
        {
            "store_id": r.id,
            "store_name": r.name,
            "paid_amount": float(r.paid_amount or 0),
            "unpaid_amount": float(r.unpaid_amount or 0),
            "paid_entries": int(r.paid_entries or 0),
            "unpaid_entries": int(r.unpaid_entries or 0),
            "total_entries": int(r.total_entries or 0),
        }
        for r in rows
    ]

    return jsonify(
        {
            "stores": stores,
            "paidUnpaidByStore": {
                "labels": [s["store_name"] for s in stores],
                "paid": [s["paid_amount"] for s in stores],
                "unpaid": [s["unpaid_amount"] for s in stores],
                "label": "Supplier payments",
            },
        }
    ), 200


@merchant_bp.get("/reports/products")
@merchant_required
def product_reports(merchant: User):
    """Product-level stock / spoilage / value report (optionally filtered by store)."""
    store_id = request.args.get("store_id", type=int)
    query = (
        db.session.query(
            Product.id,
            Product.name,
            Product.category,
            Product.store_id,
            Store.name.label("store_name"),
            Product.quantity_in_stock,
            Product.buy_price,
            Product.sell_price,
            func.coalesce(func.sum(StockEntry.quantity_received), 0).label("total_received"),
            func.coalesce(func.sum(StockEntry.spoilt_quantity), 0).label("total_spoilt"),
        )
        .join(Store, Store.id == Product.store_id)
        .outerjoin(StockEntry, StockEntry.product_id == Product.id)
        .group_by(Product.id, Store.name)
    )
    if store_id is not None:
        query = query.filter(Product.store_id == store_id)

    rows = query.order_by(Product.name).all()
    products = [
        {
            "product_id": r.id,
            "name": r.name,
            "category": r.category,
            "store_id": r.store_id,
            "store_name": r.store_name,
            "quantity_in_stock": r.quantity_in_stock,
            "buy_price": r.buy_price,
            "sell_price": r.sell_price,
            "total_received": int(r.total_received),
            "total_spoilt": int(r.total_spoilt),
            "stock_value": float(r.quantity_in_stock * r.buy_price),
        }
        for r in rows
    ]

    return jsonify(
        {
            "products": products,
            "stockByProduct": {
                "labels": [p["name"] for p in products],
                "values": [p["quantity_in_stock"] for p in products],
                "label": "Units in stock",
            },
        }
    ), 200