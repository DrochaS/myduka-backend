from flask import Flask


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        TESTING=testing,
        JSON_SORT_KEYS=False,
    )
    return app
