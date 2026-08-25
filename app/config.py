import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # PostgreSQL via DATABASE_URL; fall back to local SQLite file
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///myduka.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Invite tokens expire after this many hours
    INVITE_TOKEN_HOURS = int(os.getenv("INVITE_TOKEN_HOURS", "48"))

    # Frontend base URL used when building invite links
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Mail — when not configured, invite links are logged instead of sent
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@myduka.local")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key-at-least-32-bytes"
    INVITE_TOKEN_HOURS = 24
    MAIL_SERVER = ""
