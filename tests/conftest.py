"""Pytest fixtures for MyDuka API tests."""

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Product, Role, Store, User


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.drop_all()
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def store(app):
    with app.app_context():
        s = Store(name="Nairobi Central", location="Nairobi")
        db.session.add(s)
        db.session.commit()
        db.session.refresh(s)
        store_id = s.id
    # re-fetch in app context for callers
    with app.app_context():
        return db.session.get(Store, store_id)


@pytest.fixture()
def merchant(app):
    with app.app_context():
        user = User(email="merchant@myduka.test", role=Role.MERCHANT, is_active=True)
        user.set_password("merchant-pass")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with app.app_context():
        return db.session.get(User, user_id)


@pytest.fixture()
def admin_user(app, store):
    with app.app_context():
        user = User(
            email="admin@myduka.test",
            role=Role.ADMIN,
            is_active=True,
            store_id=store.id,
            full_name="Store Admin",
        )
        user.set_password("admin-pass")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with app.app_context():
        return db.session.get(User, user_id)


@pytest.fixture()
def clerk_user(app, store):
    with app.app_context():
        user = User(
            email="clerk@myduka.test",
            role=Role.CLERK,
            is_active=True,
            store_id=store.id,
            full_name="Front Clerk",
        )
        user.set_password("clerk-pass")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with app.app_context():
        return db.session.get(User, user_id)


@pytest.fixture()
def product(app, store):
    with app.app_context():
        p = Product(
            name="Maize Flour",
            category="Groceries",
            store_id=store.id,
            buy_price=80.0,
            sell_price=100.0,
            quantity_in_stock=10,
        )
        db.session.add(p)
        db.session.commit()
        product_id = p.id
    with app.app_context():
        return db.session.get(Product, product_id)


def auth_header(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.get_json()
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
