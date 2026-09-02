"""Tests for the public storefront routes."""


def test_list_products_only_shows_active_in_stock_items(client, store, product):
    resp = client.get(f"/api/storefront/products?store_id={store.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Maize Flour"
    assert "buy_price" not in data[0]  # internal-only field must not leak


def test_list_products_requires_store_id(client):
    resp = client.get("/api/storefront/products")
    assert resp.status_code == 400


def test_checkout_cash_creates_order_and_deducts_stock(client, store, product):
    resp = client.post(
        "/api/storefront/checkout",
        json={
            "store_id": store.id,
            "customer_name": "Jane Wambui",
            "customer_phone": "+254712345678",
            "payment_method": "cash",
            "items": [{"product_id": product.id, "quantity": 3}],
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["payment_status"] == "pending"
    assert data["status"] == "confirmed"
    assert data["total_amount"] == 300.0
    assert data["items"][0]["quantity"] == 3

    # stock should be deducted
    products_resp = client.get(f"/api/storefront/products?store_id={store.id}")
    remaining = products_resp.get_json()[0]["quantity_in_stock"]
    assert remaining == 7


def test_checkout_mpesa_marks_paid_immediately(client, store, product):
    resp = client.post(
        "/api/storefront/checkout",
        json={
            "store_id": store.id,
            "customer_name": "Peter Otieno",
            "customer_phone": "+254700000000",
            "payment_method": "mpesa",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["payment_status"] == "paid"


def test_checkout_rejects_insufficient_stock(client, store, product):
    resp = client.post(
        "/api/storefront/checkout",
        json={
            "store_id": store.id,
            "customer_name": "Overbuyer",
            "customer_phone": "+254711111111",
            "payment_method": "card",
            "items": [{"product_id": product.id, "quantity": 999}],
        },
    )
    assert resp.status_code == 400
    assert "left in stock" in resp.get_json()["error"]


def test_checkout_rejects_missing_fields(client, store):
    resp = client.post("/api/storefront/checkout", json={"store_id": store.id})
    assert resp.status_code == 400


def test_get_order_returns_order(client, store, product):
    create_resp = client.post(
        "/api/storefront/checkout",
        json={
            "store_id": store.id,
            "customer_name": "Jane Wambui",
            "customer_phone": "+254712345678",
            "payment_method": "cash",
            "items": [{"product_id": product.id, "quantity": 1}],
        },
    )
    order_id = create_resp.get_json()["id"]

    resp = client.get(f"/api/storefront/orders/{order_id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == order_id


def test_get_order_404_for_missing_order(client):
    resp = client.get("/api/storefront/orders/99999")
    assert resp.status_code == 404