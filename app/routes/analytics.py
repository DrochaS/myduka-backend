from flask import Blueprint, jsonify

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/sales")
def sales_analytics():
    """Return sample sales series shaped for the React Chart.js dashboard."""
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
