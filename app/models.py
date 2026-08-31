"""SQLAlchemy models for MyDuka inventory API."""

from __future__ import annotations

import enum
import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Role(str, enum.Enum):
    MERCHANT = "merchant"
    ADMIN = "admin"
    CLERK = "clerk"


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    NOT_PAID = "not_paid"


class SupplyRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    location = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    users = db.relationship("User", back_populates="store", lazy="dynamic")
    products = db.relationship("Product", back_populates="store", lazy="dynamic")
    stock_entries = db.relationship("StockEntry", back_populates="store", lazy="dynamic")
    supply_requests = db.relationship(
        "SupplyRequest", back_populates="store", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.Enum(Role), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    store = db.relationship("Store", back_populates="users")
    stock_entries = db.relationship(
        "StockEntry",
        back_populates="clerk",
        foreign_keys="StockEntry.clerk_id",
        lazy="dynamic",
    )
    supply_requests = db.relationship(
        "SupplyRequest",
        back_populates="clerk",
        foreign_keys="SupplyRequest.clerk_id",
        lazy="dynamic",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if isinstance(self.role, Role) else self.role,
            "is_active": self.is_active,
            "store_id": self.store_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    sku = db.Column(db.String(64), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    buy_price = db.Column(db.Float, nullable=False, default=0.0)
    sell_price = db.Column(db.Float, nullable=False, default=0.0)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    store = db.relationship("Store", back_populates="products")
    stock_entries = db.relationship("StockEntry", back_populates="product", lazy="dynamic")
    supply_requests = db.relationship(
        "SupplyRequest", back_populates="product", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "sku": self.sku,
            "image_url": self.image_url,
            "store_id": self.store_id,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "quantity_in_stock": self.quantity_in_stock,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StockEntry(db.Model):
    """Record of items received by a clerk."""

    __tablename__ = "stock_entries"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    clerk_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quantity_received = db.Column(db.Integer, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    spoilt_quantity = db.Column(db.Integer, nullable=False, default=0)
    buy_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    payment_status = db.Column(
        db.Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.NOT_PAID,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product = db.relationship("Product", back_populates="stock_entries")
    store = db.relationship("Store", back_populates="stock_entries")
    clerk = db.relationship("User", back_populates="stock_entries", foreign_keys=[clerk_id])

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "product_category": self.product.category if self.product else None,
            "product_sku": self.product.sku if self.product else None,
            "product_image_url": self.product.image_url if self.product else None,
            "store_id": self.store_id,
            "clerk_id": self.clerk_id,
            "clerk_email": self.clerk.email if self.clerk else None,
            "quantity_received": self.quantity_received,
            "stock_quantity": self.stock_quantity,
            "spoilt_quantity": self.spoilt_quantity,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "payment_status": (
                self.payment_status.value
                if isinstance(self.payment_status, PaymentStatus)
                else self.payment_status
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupplyRequest(db.Model):
    __tablename__ = "supply_requests"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    clerk_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum(SupplyRequestStatus),
        nullable=False,
        default=SupplyRequestStatus.PENDING,
    )
    notes = db.Column(db.Text, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    product = db.relationship("Product", back_populates="supply_requests")
    store = db.relationship("Store", back_populates="supply_requests")
    clerk = db.relationship(
        "User", back_populates="supply_requests", foreign_keys=[clerk_id]
    )
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "store_id": self.store_id,
            "clerk_id": self.clerk_id,
            "clerk_email": self.clerk.email if self.clerk else None,
            "quantity_requested": self.quantity_requested,
            "status": self.status.value if isinstance(self.status, SupplyRequestStatus) else self.status,
            "notes": self.notes,
            "reviewed_by_id": self.reviewed_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class InviteToken(db.Model):
    """Tokenized invite for admin (or clerk) registration."""

    __tablename__ = "invite_tokens"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.ADMIN)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=True)
    invited_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invited_by = db.relationship("User", foreign_keys=[invited_by_id])
    store = db.relationship("Store")

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @classmethod
    def create_invite(
        cls,
        email: str,
        role: Role,
        invited_by_id: int,
        hours: int = 48,
        store_id: int | None = None,
    ) -> "InviteToken":
        invite = cls(
            email=email.lower().strip(),
            token=cls.generate_token(),
            role=role,
            store_id=store_id,
            invited_by_id=invited_by_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
        )
        db.session.add(invite)
        return invite

    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires

    def mark_used(self) -> None:
        self.used_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "token": self.token,
            "role": self.role.value if isinstance(self.role, Role) else self.role,
            "store_id": self.store_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
