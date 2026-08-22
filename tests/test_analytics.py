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
