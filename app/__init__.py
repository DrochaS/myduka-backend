from flask import Flask, jsonify

from app.config import Config, TestConfig


def create_app(config_class=None, testing: bool = False) -> Flask:
    app = Flask(__name__)
    if config_class is not None:
        app.config.from_object(config_class)
    elif testing:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    if testing:
        app.config["TESTING"] = True

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/analytics/sales")
    def sales_analytics():
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

    return app
