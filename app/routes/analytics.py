from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Product, StockEntry

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/sales")
def sales_analytics():
    """
    Return sales-oriented series for the React Chart.js dashboard.

    Uses live stock-entry totals when data exists; otherwise returns a
    stable sample series so the frontend charts still render.
    """
    entry_count = db.session.query(db.func.count(StockEntry.id)).scalar() or 0

    if entry_count == 0:
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

    # Aggregate by product category for breakdown
    from sqlalchemy import func

    category_rows = (
        db.session.query(
            func.coalesce(Product.category, "Other").label("category"),
            func.coalesce(
                func.sum(StockEntry.quantity_received * StockEntry.sell_price), 0
            ).label("total"),
        )
        .join(Product, Product.id == StockEntry.product_id)
        .group_by(func.coalesce(Product.category, "Other"))
        .all()
    )
    cat_labels = [r.category for r in category_rows] or ["Other"]
    cat_values_raw = [float(r.total) for r in category_rows] or [0.0]
    total = sum(cat_values_raw) or 1.0
    cat_values = [round(v / total * 100, 1) for v in cat_values_raw]

    # Build a simple 7-point trend from cumulative sell value
    entries = (
        StockEntry.query.order_by(StockEntry.created_at.asc()).limit(200).all()
    )
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    buckets = [0.0] * 7
    for idx, entry in enumerate(entries):
        buckets[idx % 7] += float(entry.quantity_received * entry.sell_price)

    return jsonify(
        {
            "salesTrend": {
                "labels": labels,
                "values": buckets,
                "label": "Daily sales",
            },
            "categoryBreakdown": {
                "labels": cat_labels,
                "values": cat_values,
                "label": "Share %",
            },
        }
    )
