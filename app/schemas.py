"""Marshmallow schemas for request validation / response shaping."""

from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))


class RegisterSchema(Schema):
    """Public account registration."""

    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    full_name = fields.Str(required=False, allow_none=True, validate=validate.Length(max=120))
    role = fields.Str(
        load_default="merchant",
        validate=validate.OneOf(["merchant", "admin", "clerk"]),
    )


class InviteAdminSchema(Schema):
    email = fields.Email(required=True)
    store_id = fields.Int(required=False, allow_none=True)
    full_name = fields.Str(required=False, allow_none=True)


class AcceptInviteSchema(Schema):
    token = fields.Str(required=True, validate=validate.Length(min=8))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    full_name = fields.Str(required=False, allow_none=True)


class CreateClerkSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=False, allow_none=True, validate=validate.Length(min=6))
    full_name = fields.Str(required=False, allow_none=True)
    invite = fields.Bool(load_default=False)


class StockEntrySchema(Schema):
    product_id = fields.Int(required=True)
    quantity_received = fields.Int(required=True, validate=validate.Range(min=1))
    stock_quantity = fields.Int(required=True, validate=validate.Range(min=0))
    spoilt_quantity = fields.Int(load_default=0, validate=validate.Range(min=0))
    buy_price = fields.Float(required=True, validate=validate.Range(min=0))
    sell_price = fields.Float(required=True, validate=validate.Range(min=0))
    payment_status = fields.Str(
        load_default="not_paid",
        validate=validate.OneOf(["paid", "not_paid"]),
    )


class SpoiltGoodsSchema(Schema):
    spoilt_quantity = fields.Int(required=True, validate=validate.Range(min=1))


class SupplyRequestCreateSchema(Schema):
    product_id = fields.Int(required=True)
    quantity_requested = fields.Int(required=True, validate=validate.Range(min=1))
    notes = fields.Str(required=False, allow_none=True)


class PaymentUpdateSchema(Schema):
    payment_status = fields.Str(
        required=True, validate=validate.OneOf(["paid", "not_paid"])
    )


class StoreCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    location = fields.Str(required=False, allow_none=True)


class ProductCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    category = fields.Str(required=False, allow_none=True)
    sku = fields.Str(required=False, allow_none=True)
    image_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    store_id = fields.Int(required=True)
    buy_price = fields.Float(load_default=0.0)
    sell_price = fields.Float(load_default=0.0)
    quantity_in_stock = fields.Int(load_default=0)


class CheckoutItemSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class CheckoutSchema(Schema):
    store_id = fields.Int(required=True)
    customer_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    customer_phone = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    customer_email = fields.Email(required=False, allow_none=True)
    payment_method = fields.Str(
        required=True, validate=validate.OneOf(["cash", "mpesa", "card"])
    )
    items = fields.List(fields.Nested(CheckoutItemSchema), required=True, validate=validate.Length(min=1))
