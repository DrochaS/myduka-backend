"""Admin endpoint tests."""

from tests.conftest import auth_header


def _seed_stock_and_supply(client, product):
    clerk_headers = auth_header(client, "clerk@myduka.test", "clerk-pass")

    stock = client.post(
        "/api/clerk/stock-entries",
        headers=clerk_headers,
        json={
            "product_id": product.id,
            "quantity_received": 15,
            "stock_quantity": 25,
            "spoilt_quantity": 2,
            "buy_price": 80.0,
            "sell_price": 100.0,
            "payment_status": "not_paid",
        },
    )
    assert stock.status_code == 201, stock.get_json()

    supply = client.post(
        "/api/clerk/supply-requests",
        headers=clerk_headers,
        json={"product_id": product.id, "quantity_requested": 40},
    )
    assert supply.status_code == 201, supply.get_json()
    return stock.get_json(), supply.get_json()


def test_admin_approve_supply_request(client, admin_user, clerk_user, product):
    _, supply = _seed_stock_and_supply(client, product)
    admin_headers = auth_header(client, "admin@myduka.test", "admin-pass")

    response = client.post(
        f"/api/admin/supply-requests/{supply['id']}/approve",
        headers=admin_headers,
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["status"] == "approved"


def test_admin_update_payment_status(client, admin_user, clerk_user, product):
    stock, _ = _seed_stock_and_supply(client, product)
    admin_headers = auth_header(client, "admin@myduka.test", "admin-pass")

    response = client.patch(
        f"/api/admin/payments/{stock['id']}",
        headers=admin_headers,
        json={"payment_status": "paid"},
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["payment_status"] == "paid"

    listed = client.get("/api/admin/payments?status=paid", headers=admin_headers)
    assert listed.status_code == 200
    assert any(item["id"] == stock["id"] for item in listed.get_json())


def test_admin_create_clerk_with_password(client, admin_user):
    admin_headers = auth_header(client, "admin@myduka.test", "admin-pass")
    response = client.post(
        "/api/admin/clerks",
        headers=admin_headers,
        json={
            "email": "newclerk@myduka.test",
            "password": "clerk-secret",
            "full_name": "New Clerk",
        },
    )
    assert response.status_code == 201, response.get_json()
    assert response.get_json()["role"] == "clerk"


def test_admin_clerk_performance_report(client, admin_user, clerk_user, product):
    _seed_stock_and_supply(client, product)
    admin_headers = auth_header(client, "admin@myduka.test", "admin-pass")
    response = client.get(
        "/api/admin/reports/clerk-performance",
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "clerks" in body
    assert "entriesByClerk" in body
    assert len(body["entriesByClerk"]["labels"]) == len(body["entriesByClerk"]["values"])
