import enum
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from app.extensions import db
except ImportError:
    from app import db


# ==============================================================================
# ENUMS
# ==============================================================================

class Role(str, enum.Enum):
    ADMIN = "admin"
    MERCHANT = "merchant"
    CLERK = "clerk"


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    NOT_PAID = "not_paid"


class SupplyRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CARD = "card"
    CASH = "cash"
    MPESA = "mpesa"


class OrderPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# ==============================================================================
# MODELS
# ==============================================================================

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    full_name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.CLERK, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    supply_requests = db.relationship(
        'SupplyRequest',
        backref='requester',
        lazy=True,
        foreign_keys='SupplyRequest.clerk_id',
    )
    stock_entries = db.relationship('StockEntry', backref='clerk', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        role_val = self.role.value if isinstance(self.role, Role) else self.role
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username or self.email.split('@')[0],
            'full_name': self.full_name,
            'role': role_val,
            'store_id': self.store_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='store', lazy=True)
    products = db.relationship('Product', backref='store', lazy=True, cascade="all, delete-orphan")
    stock_entries = db.relationship('StockEntry', backref='store', lazy=True)
    supply_requests = db.relationship('SupplyRequest', backref='store', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model):
    """A product as sold/stocked at a specific store."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    sku = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    buy_price = db.Column(db.Float, default=0.0, nullable=False)
    sell_price = db.Column(db.Float, default=0.0, nullable=False)
    quantity_in_stock = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    stock_entries = db.relationship('StockEntry', backref='product', lazy=True, cascade="all, delete-orphan")
    supply_requests = db.relationship('SupplyRequest', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'sku': self.sku,
            'image_url': self.image_url,
            'store_id': self.store_id,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'quantity_in_stock': self.quantity_in_stock,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StockEntry(db.Model):
    """A delivery of stock recorded by a clerk, plus its supplier payment status."""
    __tablename__ = 'stock_entries'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    clerk_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    quantity_received = db.Column(db.Integer, nullable=False, default=0)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    spoilt_quantity = db.Column(db.Integer, nullable=False, default=0)

    buy_price = db.Column(db.Float, nullable=False, default=0.0)
    sell_price = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(
        db.Enum(PaymentStatus), default=PaymentStatus.NOT_PAID, nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        payment_val = (
            self.payment_status.value
            if isinstance(self.payment_status, PaymentStatus)
            else self.payment_status
        )
        return {
            'id': self.id,
            'store_id': self.store_id,
            'product_id': self.product_id,
            'clerk_id': self.clerk_id,
            'quantity_received': self.quantity_received,
            'stock_quantity': self.stock_quantity,
            'spoilt_quantity': self.spoilt_quantity,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'payment_status': payment_val,
            'product_name': self.product.name if self.product else None,
            'store_name': self.store.name if self.store else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SupplyRequest(db.Model):
    __tablename__ = 'supply_requests'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    clerk_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    quantity_requested = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(SupplyRequestStatus), default=SupplyRequestStatus.PENDING, nullable=False
    )

    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])

    def to_dict(self):
        status_val = (
            self.status.value if isinstance(self.status, SupplyRequestStatus) else self.status
        )
        return {
            'id': self.id,
            'store_id': self.store_id,
            'store_name': self.store.name if self.store else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'clerk_id': self.clerk_id,
            'reviewed_by_id': self.reviewed_by_id,
            'quantity_requested': self.quantity_requested,
            'notes': self.notes,
            'status': status_val,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Order(db.Model):
    """A customer order placed through the public storefront."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120), nullable=True)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    payment_status = db.Column(
        db.Enum(OrderPaymentStatus), default=OrderPaymentStatus.PENDING, nullable=False
    )
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)

    # M-Pesa STK push tracking (populated only when payment_method == MPESA)
    mpesa_checkout_request_id = db.Column(db.String(100), nullable=True)
    mpesa_receipt_number = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship('Store', backref='orders')
    items = db.relationship(
        'OrderItem', backref='order', lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        payment_method_val = (
            self.payment_method.value
            if isinstance(self.payment_method, PaymentMethod)
            else self.payment_method
        )
        payment_status_val = (
            self.payment_status.value
            if isinstance(self.payment_status, OrderPaymentStatus)
            else self.payment_status
        )
        status_val = self.status.value if isinstance(self.status, OrderStatus) else self.status
        return {
            'id': self.id,
            'store_id': self.store_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'payment_method': payment_method_val,
            'payment_status': payment_status_val,
            'status': status_val,
            'total_amount': self.total_amount,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'mpesa_checkout_request_id': self.mpesa_checkout_request_id,
            'mpesa_customer_message': (
                'Check your phone to complete payment'
                if self.payment_method == PaymentMethod.MPESA
                and self.payment_status == OrderPaymentStatus.PENDING
                else None
            ),
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': round(self.quantity * self.unit_price, 2),
        }


class InviteToken(db.Model):
    __tablename__ = 'invite_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(Role), default=Role.ADMIN, nullable=False)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def create_invite(cls, email, role, invited_by_id, hours=48, store_id=None):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=hours)
        invite = cls(
            token=token,
            email=email,
            role=role,
            invited_by_id=invited_by_id,
            store_id=store_id,
            expires_at=expires_at
        )
        db.session.add(invite)
        return invite

    def is_valid(self):
        return not self.is_used and self.expires_at > datetime.utcnow()

    def mark_used(self):
        self.is_used = True
        self.used_at = datetime.utcnow()

    def to_dict(self):
        role_val = self.role.value if isinstance(self.role, Role) else self.role
        return {
            'id': self.id,
            'token': self.token,
            'email': self.email,
            'role': role_val,
            'invited_by_id': self.invited_by_id,
            'store_id': self.store_id,
            'is_used': self.is_used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
