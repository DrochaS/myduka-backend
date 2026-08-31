from flask import Flask
from app import create_app
from app.config import TestConfig


def test_create_app_returns_flask_app():
    app = create_app()
    assert isinstance(app, Flask)
    assert app.config["TESTING"] is False


def test_create_app_with_testing_config():
    app = create_app(TestConfig)
    assert app.config["TESTING"] is True


def test_api_preflight_allows_configured_frontend_origin():
    app = create_app(TestConfig)
    response = app.test_client().options(
        "/api/auth/register",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"


def test_api_preflight_rejects_unconfigured_frontend_origin():
    app = create_app(TestConfig)
    response = app.test_client().options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "Access-Control-Allow-Origin" not in response.headers
