from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models import Order, OrderItem, OrderStatus, PaymentMethod, OrderPaymentStatus, Product
from app.schemas import CheckoutSchema

storefront_bp = Blueprint("storefront", __name__)

checkout_schema = CheckoutSchema()


@storefront_bp.get("/products")
def list_products():
    store_id = request.args.get("store_id", type=int)
    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    products = Product.query.filter_by(store_id=store_id, is_active=True).all()
    return jsonify(
        [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "sku": product.sku,
                "image_url": product.image_url,
                "sell_price": product.sell_price,
                "quantity_in_stock": product.quantity_in_stock,
            }
            for product in products
            if product.quantity_in_stock > 0
        ]
    )


@storefront_bp.post("/checkout")
def checkout():
    try:
        payload = checkout_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    store_id = payload["store_id"]

    # Lock in products and validate stock before creating anything.
    line_items = []
    for item in payload["items"]:
        product = Product.query.filter_by(
            id=item["product_id"], store_id=store_id, is_active=True
        ).first()
        if not product:
            return jsonify({"error": f"Product {item['product_id']} not found in this store"}), 400
        if product.quantity_in_stock < item["quantity"]:
            return jsonify(
                {
                    "error": (
                        f"Only {product.quantity_in_stock} units of "
                        f"'{product.name}' left in stock"
                    )
                }
            ), 400
        line_items.append((product, item["quantity"]))

    total_amount = sum(product.sell_price * qty for product, qty in line_items)
    payment_method = PaymentMethod(payload["payment_method"])

    # Card and M-Pesa are treated as paid immediately for this project
    # (no real payment processor wired up yet); cash is paid on delivery.
    payment_status = (
        OrderPaymentStatus.PENDING if payment_method == PaymentMethod.CASH else OrderPaymentStatus.PAID
    )

    order = Order(
        store_id=store_id,
        customer_name=payload["customer_name"],
        customer_phone=payload["customer_phone"],
        customer_email=payload.get("customer_email"),
        payment_method=payment_method,
        payment_status=payment_status,
        status=OrderStatus.CONFIRMED,
        total_amount=total_amount,
    )
    db.session.add(order)
    db.session.flush()  # populate order.id before creating items

    for product, qty in line_items:
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=product.sell_price,
            )
        )
        product.quantity_in_stock -= qty

    db.session.commit()

    return jsonify(order.to_dict()), 201


@storefront_bp.get("/orders/<int:order_id>")
def get_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.to_dict())