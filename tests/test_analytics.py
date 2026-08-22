"""Analytics and health endpoint tests."""


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_sales_analytics_shape(client):
    response = client.get("/api/analytics/sales")
    assert response.status_code == 200

    payload = response.get_json()
    assert "salesTrend" in payload
    assert "categoryBreakdown" in payload

    trend = payload["salesTrend"]
    assert len(trend["labels"]) == len(trend["values"])
    assert all(isinstance(v, (int, float)) for v in trend["values"])

    breakdown = payload["categoryBreakdown"]
    assert len(breakdown["labels"]) == len(breakdown["values"])


def test_sales_analytics_with_stock_data(client, clerk_user, product):
    from tests.conftest import auth_header

    headers = auth_header(client, "clerk@myduka.test", "clerk-pass")
    create = client.post(
        "/api/clerk/stock-entries",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity_received": 10,
            "stock_quantity": 20,
            "spoilt_quantity": 0,
            "buy_price": 80.0,
            "sell_price": 100.0,
            "payment_status": "paid",
        },
    )
    assert create.status_code == 201

    response = client.get("/api/analytics/sales")
    assert response.status_code == 200
    payload = response.get_json()
    assert "Groceries" in payload["categoryBreakdown"]["labels"] or len(
        payload["categoryBreakdown"]["labels"]
    ) >= 1
