from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin

product_categories = [
    "kettles",
    "yixing pots",
    "tea caddy",
    "scoop/spoon",
    "ceramics",
    "knife/pick",
    "base",
    "stove",
    "wood",
    "lacquer",
    "tea",
    "partnership sales",
    "vintage teas",
    "miscellaneous",
]
db = SQLAlchemy()


class Image(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))
    public_id = db.Column(db.String(255))

    def __repr__(self):
        return "<Image %r>" % self.idx


class Category(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    tax_rate = db.Column(db.Float, default=10)

    def __repr__(self):
        return "<Category %r>" % self.name


class Product(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    category_idx = db.Column(db.Integer, db.ForeignKey("category.idx"))
    category = db.relationship("Category", backref="product", lazy=True)
    description = db.Column(db.Text)
    photo_idx = db.Column(db.Integer, db.ForeignKey("image.idx"))
    photo = db.relationship("Image", backref="product", lazy=True)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)
    volume = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return "<Product %r>" % self.title


class InvoiceProduct(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    invoice_idx = db.Column(db.Integer, db.ForeignKey("invoice.idx"))
    product_idx = db.Column(db.Integer, db.ForeignKey("product.idx"))
    product = db.relationship("Product", backref="invoice", lazy=True)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)

    def __repr__(self):
        return "<InvoiceProduct %r>" % self.idx


class Invoice(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    invoice_products = db.relationship("InvoiceProduct", backref="invoice", lazy=True)
    total_weight = db.Column(db.Float, default=0)
    total_purchase_price = db.Column(db.Float, default=0)
    total_sale_price = db.Column(db.Float, default=0)
    total_profit = db.Column(db.Float, default=0)
    customer_price = db.Column(db.Float, default=0)
    status = db.Column(db.String(255), default="open")
    is_active = db.Column(db.Boolean, default=True)
    customer_idx = db.Column(
        db.Integer, db.ForeignKey("customer.idx"), nullable=True, default=None
    )
    customer = db.relationship("Customer", backref="invoice", lazy=True)

    def __repr__(self):
        return "<Invoice %r>" % self.idx


class User(UserMixin, db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return self.idx

    def __repr__(self):
        return "<User %r>" % self.username


class Customer(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    notes = db.Column(db.Text, default="")

    def __repr__(self):
        return "<Customer %r>" % self.name


class Pricing(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    formula_online = db.Column(db.Text)
    formula_teahouse = db.Column(db.Text)

    def __repr__(self):
        return "<Pricing %r>" % self.name
