"""
Tests for app.utils.pagination.Paginator / paginate().

These tests spin up a throwaway Flask app + in-memory SQLite DB so they
don't depend on Postgres or the rest of the app being wired up yet.
Drop this into your tests/ folder as test_pagination.py.
"""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.utils.pagination import Paginator, paginate


@pytest.fixture
def app_and_db():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["DEFAULT_PAGE"] = 1
    app.config["DEFAULT_PER_PAGE"] = 20
    app.config["MAX_PER_PAGE"] = 100

    db = SQLAlchemy(app)

    class Item(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))

    with app.app_context():
        db.create_all()
        for i in range(1, 46):  # 45 records
            db.session.add(Item(name=f"item-{i}"))
        db.session.commit()
        yield app, db, Item


def test_default_pagination(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items"):
        result = paginate(Item.query.order_by(Item.id), serializer=lambda i: {"id": i.id})
        p = result["pagination"]
        assert p["page"] == 1
        assert p["per_page"] == 20
        assert p["total_records"] == 45
        assert p["total_pages"] == 3
        assert len(result["data"]) == 20
        assert p["has_next"] is True
        assert p["has_prev"] is False


def test_custom_page_and_per_page(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items?page=3&per_page=10"):
        result = paginate(Item.query.order_by(Item.id), serializer=lambda i: {"id": i.id})
        p = result["pagination"]
        assert p["page"] == 3
        assert p["per_page"] == 10
        assert p["total_pages"] == 5
        assert len(result["data"]) == 10
        assert p["has_next"] is True
        assert p["has_prev"] is True


def test_last_page_has_remainder(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items?page=5&per_page=10"):
        result = paginate(Item.query.order_by(Item.id), serializer=lambda i: {"id": i.id})
        assert len(result["data"]) == 5  # 45 - 40
        assert result["pagination"]["has_next"] is False


def test_per_page_exceeds_max_raises(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items?per_page=500"):
        with pytest.raises(Exception):
            paginate(Item.query, serializer=lambda i: {"id": i.id})


def test_invalid_page_value_raises(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items?page=abc"):
        with pytest.raises(Exception):
            paginate(Item.query, serializer=lambda i: {"id": i.id})


def test_out_of_range_page_returns_empty(app_and_db):
    app, db, Item = app_and_db
    with app.test_request_context("/items?page=99&per_page=20"):
        result = paginate(Item.query.order_by(Item.id), serializer=lambda i: {"id": i.id})
        assert result["data"] == []
        assert result["pagination"]["total_records"] == 45