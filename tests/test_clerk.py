"""Clerk endpoint tests."""

from tests.conftest import auth_header


def test_clerk_create_stock_entry(client, clerk_user, product, store):
    headers = auth_header(client, "clerk@myduka.test", "clerk-pass")

    response = client.post(
        "/api/clerk/stock-entries",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity_received": 20,
            "stock_quantity": 30,
            "spoilt_quantity": 1,
            "buy_price": 80.0,
            "sell_price": 110.0,
            "payment_status": "not_paid",
        },
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["quantity_received"] == 20
    assert body["payment_status"] == "not_paid"
    assert body["product_id"] == product.id
    assert body["store_id"] == store.id

    listed = client.get("/api/clerk/stock-entries", headers=headers)
    assert listed.status_code == 200
    assert len(listed.get_json()) == 1


def test_clerk_create_supply_request(client, clerk_user, product):
    headers = auth_header(client, "clerk@myduka.test", "clerk-pass")

    response = client.post(
        "/api/clerk/supply-requests",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity_requested": 50,
            "notes": "Running low",
        },
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["quantity_requested"] == 50

    listed = client.get("/api/clerk/supply-requests", headers=headers)
    assert listed.status_code == 200
    assert len(listed.get_json()) == 1


def test_clerk_can_list_store_products(client, clerk_user, product):
    headers = auth_header(client, "clerk@myduka.test", "clerk-pass")
    response = client.get("/api/clerk/products", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.get_json()] == [product.id]


def test_clerk_can_report_spoilt_goods(client, clerk_user, product):
    headers = auth_header(client, "clerk@myduka.test", "clerk-pass")
    created = client.post(
        "/api/clerk/stock-entries",
        headers=headers,
        json={
            "product_id": product.id,
            "quantity_received": 5,
            "stock_quantity": 10,
            "buy_price": 80,
            "sell_price": 100,
        },
    )

    response = client.patch(
        f"/api/clerk/stock-entries/{created.get_json()['id']}/spoilt",
        headers=headers,
        json={"spoilt_quantity": 2},
    )

    assert response.status_code == 200
    assert response.get_json()["spoilt_quantity"] == 2
    assert response.get_json()["stock_quantity"] == 8


def test_clerk_stock_entry_requires_auth(client, product):
    response = client.post(
        "/api/clerk/stock-entries",
        json={
            "product_id": product.id,
            "quantity_received": 5,
            "stock_quantity": 5,
            "buy_price": 10,
            "sell_price": 15,
        },
    )
    assert response.status_code == 401
