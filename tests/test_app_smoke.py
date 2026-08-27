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
