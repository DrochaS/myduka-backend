"""Auth endpoint tests."""

from app.extensions import db
from app.models import InviteToken, Role, User
from tests.conftest import auth_header


def test_register_creates_selected_role_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newmerchant@myduka.test",
            "password": "merchant-secret",
            "full_name": "New Merchant",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["user"]["email"] == "newmerchant@myduka.test"
    assert payload["user"]["role"] == "admin"
    assert "access_token" in payload


def test_register_rejects_existing_email(client, merchant):
    response = client.post(
        "/api/auth/register",
        json={"email": merchant.email, "password": "merchant-secret"},
    )

    assert response.status_code == 409


def test_unassigned_admin_can_load_an_empty_performance_report(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "email": "admin-without-store@myduka.test",
            "password": "admin-secret",
            "role": "admin",
        },
    )
    token = registration.get_json()["access_token"]

    response = client.get(
        "/api/admin/reports/clerk-performance",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["entriesByClerk"]["labels"] == []


def test_login_success(client, merchant):
    response = client.post(
        "/api/auth/login",
        json={"email": "merchant@myduka.test", "password": "merchant-pass"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "access_token" in payload
    assert payload["user"]["role"] == "merchant"
    assert payload["user"]["email"] == "merchant@myduka.test"


def test_login_invalid_password(client, merchant):
    response = client.post(
        "/api/auth/login",
        json={"email": "merchant@myduka.test", "password": "wrong"},
    )
    assert response.status_code == 401


def test_invite_admin_and_accept(client, app, merchant, store):
    headers = auth_header(client, "merchant@myduka.test", "merchant-pass")

    invite_resp = client.post(
        "/api/auth/invite-admin",
        json={"email": "newadmin@myduka.test", "store_id": store.id},
        headers=headers,
    )
    assert invite_resp.status_code == 201
    invite_body = invite_resp.get_json()
    assert invite_body["email"] == "newadmin@myduka.test"
    token = invite_body["token"]
    assert "invite_url" in invite_body

    accept_resp = client.post(
        "/api/auth/accept-invite",
        json={
            "token": token,
            "password": "admin-secret",
            "full_name": "New Admin",
        },
    )
    assert accept_resp.status_code == 201
    accept_body = accept_resp.get_json()
    assert accept_body["user"]["role"] == "admin"
    assert accept_body["user"]["email"] == "newadmin@myduka.test"
    assert "access_token" in accept_body

    with app.app_context():
        user = User.query.filter_by(email="newadmin@myduka.test").first()
        assert user is not None
        assert user.role == Role.ADMIN
        invite = InviteToken.query.filter_by(token=token).first()
        assert invite.used_at is not None


def test_accept_invite_expired_or_invalid(client):
    response = client.post(
        "/api/auth/accept-invite",
        json={"token": "not-a-real-token", "password": "whatever1"},
    )
    assert response.status_code == 400


def test_me_requires_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, merchant):
    headers = auth_header(client, "merchant@myduka.test", "merchant-pass")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["email"] == "merchant@myduka.test"
