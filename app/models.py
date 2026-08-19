# app/models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class InventoryEntry(db.Model):
    __tablename__ = "inventory_entries"

    id = db.Column(db.Integer, primary_key=True)
    quantity_in_stock = db.Column(db.Integer, nullable=False)
    payment_status = db.Column(db.String(20), default="not_paid")

    def to_dict(self):
        return {
            "id": self.id,
            "quantity_in_stock": self.quantity_in_stock,
            "payment_status": self.payment_status,
        }

# Add more models below as your team builds them out:
# class User(db.Model): ...
# class Store(db.Model): ...
# class Product(db.Model): ...