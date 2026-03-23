from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# NAGS Auto Glass Part Numbering System
# ---------------------------------------------------------------------------
NAGS_PREFIXES = {
    "FW": "Windshield", "DW": "Windshield",
    "FD": "Door Glass", "DD": "Door Glass",
    "FB": "Back Glass", "DB": "Back Glass",
    "FQ": "Quarter Glass", "DQ": "Quarter Glass",
    "FV": "Vent Glass", "DV": "Vent Glass",
    "FT": "T-Top", "DT": "T-Top",
    "FS": "Sunroof", "DS": "Sunroof",
}


def nags_category(code):
    """Derive glass category from a NAGS part code like FW01234 or DB09520."""
    if not code:
        return ""
    code = code.strip().upper()
    if len(code) >= 2:
        prefix = code[:2]
        return NAGS_PREFIXES.get(prefix, "")
    return ""


# ---------------------------------------------------------------------------
# User — with signup approval workflow
# ---------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200), default="")
    phone = db.Column(db.String(50), default="")
    address = db.Column(db.Text, default="")
    company_name = db.Column(db.String(200), default="")
    role = db.Column(db.String(20), nullable=False, default="customer")  # admin | customer
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # False until admin approves
    approval_status = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def can_access(self):
        """User can access the site if admin OR approved customer."""
        return self.is_admin or (self.is_approved and self.is_active)

    def __repr__(self):
        return f"<User {self.username} ({self.role}, approved={self.is_approved})>"


# ---------------------------------------------------------------------------
# Product — with NAGS code support
# ---------------------------------------------------------------------------
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(100), default="General", index=True)
    car_make = db.Column(db.String(100), default="", index=True)
    car_model = db.Column(db.String(100), default="", index=True)
    car_year_start = db.Column(db.Integer, nullable=True, index=True)
    car_year_end = db.Column(db.Integer, nullable=True, index=True)
    part_number = db.Column(db.String(100), default="", index=True)
    nags_code = db.Column(db.String(20), default="", index=True)
    nags_type = db.Column(db.String(50), default="")  # Derived from NAGS prefix
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost = db.Column(db.Float, default=0.0)
    stock_quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    shipment_items = db.relationship("ShipmentItem", back_populates="product", lazy="dynamic")
    order_items = db.relationship("OrderItem", back_populates="product", lazy="dynamic")

    @property
    def year_range(self):
        if self.car_year_start and self.car_year_end:
            return f"{self.car_year_start}-{self.car_year_end}"
        elif self.car_year_start:
            return f"{self.car_year_start}+"
        return ""

    @property
    def display_code(self):
        """Best code to show: NAGS code if available, else part_number."""
        return self.nags_code or self.part_number or ""

    @property
    def profit_margin(self):
        if self.cost and self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return 0

    def set_nags(self, code):
        """Set NAGS code and auto-derive the glass type."""
        self.nags_code = (code or "").strip().upper()
        self.nags_type = nags_category(self.nags_code)

    def __repr__(self):
        return f"<Product {self.name}>"


# ---------------------------------------------------------------------------
# Wholesale Shipments (supplier deliveries)
# ---------------------------------------------------------------------------
class WholesaleShipment(db.Model):
    __tablename__ = "wholesale_shipments"

    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.String(200), nullable=False)
    invoice_number = db.Column(db.String(100), default="")
    total_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="PENDING")  # PENDING | RECEIVED
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    items = db.relationship("ShipmentItem", back_populates="shipment",
                            cascade="all, delete-orphan", lazy="joined")

    def __repr__(self):
        return f"<Shipment {self.invoice_number}>"


class ShipmentItem(db.Model):
    __tablename__ = "shipment_items"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)

    shipment_id = db.Column(db.Integer, db.ForeignKey("wholesale_shipments.id", ondelete="CASCADE"), nullable=False)
    shipment = db.relationship("WholesaleShipment", back_populates="items")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product", back_populates="shipment_items")

    @property
    def line_total(self):
        return self.quantity * self.unit_cost

    def __repr__(self):
        return f"<ShipmentItem {self.product_id} x{self.quantity}>"


# ---------------------------------------------------------------------------
# Order — with payment method, delivery/pickup, multi-address
# ---------------------------------------------------------------------------
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref="orders")
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), default="")
    customer_phone = db.Column(db.String(50), default="")
    customer_address = db.Column(db.Text, default="")

    # Payment
    payment_method = db.Column(db.String(30), default="cash")  # cash | zelle_echeck
    payment_status = db.Column(db.String(20), default="unpaid")  # unpaid | paid

    # Delivery / Pickup
    fulfillment_type = db.Column(db.String(20), default="pickup")  # pickup | delivery
    pickup_time = db.Column(db.String(100), default="")  # customer's requested pickup time
    delivery_addresses = db.Column(db.Text, default="")  # JSON list of addresses for multi-drop delivery
    delivery_time = db.Column(db.String(100), default="")  # requested delivery time
    delivery_note = db.Column(db.Text, default="")

    status = db.Column(db.String(20), default="PENDING")  # PENDING | APPROVED | SHIPPED | COMPLETED | CANCELLED
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    items = db.relationship("OrderItem", back_populates="order",
                            cascade="all, delete-orphan", lazy="joined")

    @property
    def delivery_address_list(self):
        """Parse delivery_addresses JSON into a list."""
        if not self.delivery_addresses:
            return []
        import json
        try:
            return json.loads(self.delivery_addresses)
        except (json.JSONDecodeError, TypeError):
            return [self.delivery_addresses] if self.delivery_addresses else []

    def __repr__(self):
        return f"<Order #{self.id} - {self.customer_name}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    order = db.relationship("Order", back_populates="items")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product", back_populates="order_items")

    @property
    def line_total(self):
        return self.quantity * self.price

    def __repr__(self):
        return f"<OrderItem {self.product_id} x{self.quantity}>"


# ---------------------------------------------------------------------------
# Invoice (imported PDF records)
# ---------------------------------------------------------------------------
class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=False, unique=True)
    supplier = db.Column(db.String(200), default="")
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = db.Column(db.Float, default=0.0)
    file_path = db.Column(db.String(500), default="")
    raw_text = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="IMPORTED")  # IMPORTED | PROCESSED | ERROR
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"
