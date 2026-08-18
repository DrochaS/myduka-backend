from flask import Flask

from app import create_app


def test_create_app_returns_flask_app():
    app = create_app()

    assert isinstance(app, Flask)
    assert app.config["TESTING"] is False


def test_create_app_with_testing_config():
    app = create_app(testing=True)

    assert app.config["TESTING"] is True
