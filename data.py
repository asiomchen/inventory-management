from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from images import upload_image
from sqlalchemy.sql import func
from flask_login import UserMixin
from dataclasses import dataclass
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
    "imported",
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
    
    @classmethod
    def from_wix(cls, product: ImportedProduct):
        photo_url = product.photo
        category = Category.query.filter_by(name="imported").first()
        if photo_url:
            secure_url, public_id = upload_image(photo_url)
            image = Image(url=secure_url, public_id=public_id)
            db.session.add(image)
            db.session.commit()
            photo_idx = image.idx
        else:
            photo_idx = None
        return cls(
            title=product.title,
            category_idx=category.idx,
            description=product.description,
            photo_idx=photo_idx,
            quantity=product.quantity,
            weight=product.weight,
            purchase_price=product.purchase_price,
            sale_price=product.sale_price,
            volume=product.volume,
            profit = product.sale_price - product.purchase_price)


    
@dataclass
class ImportedProduct:
    title: str 
    category_idx: int = 0
    description: str = ""
    photo: str = None
    quantity: int = 0
    weight: float = 0
    purchase_price: float = 0
    sale_price: float = 0
    volume: float  = 0


class InvoiceProduct(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    invoice_idx = db.Column(db.Integer, db.ForeignKey("invoice.idx"))
    product_idx = db.Column(db.Integer, db.ForeignKey("product.idx"))
    product = db.relationship("Product", backref="invoice", lazy=True)
    category_idx = db.Column(db.Integer, db.ForeignKey("category.idx"))
    category = db.relationship("Category", backref="invoice", lazy=True)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)
    title = db.Column(db.String(255))

    def __repr__(self):
        return "<InvoiceProduct %r>" % self.idx
    
    @classmethod
    def from_product(cls, invoice_idx: int, product: Product):
        """
        Create an InvoiceProduct object from a Product object."""

        return cls(
            invoice_idx=invoice_idx,
            product_idx=product.idx,
            category_idx=product.category_idx,
            quantity=1,
            weight=product.weight,
            purchase_price=product.purchase_price,
            sale_price=product.sale_price,
            profit=product.sale_price - product.purchase_price,
            title=product.title,
        )
    


class Invoice(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    invoice_products = db.relationship("InvoiceProduct", backref="invoice", lazy=True)
    total_weight = db.Column(db.Float, default=0)
    total_purchase_price = db.Column(db.Float, default=0)
    total_sale_price = db.Column(db.Float, default=0)
    total_profit = db.Column(db.Float, default=0)
    total_customer_price = db.Column(db.Float, default=0)
    status = db.Column(db.String(255), default="open")
    is_active = db.Column(db.Boolean, default=True)
    customer_idx = db.Column(
        db.Integer, db.ForeignKey("customer.idx"), nullable=True, default=None
    )
    customer = db.relationship("Customer", backref="invoice", lazy=True)

    def calculate_totals(self):
        """
        Calculate the total weight, purchase price, sale price, and profit of the invoice.
        """
        self.total_weight = sum(
            product.weight * product.quantity for product in self.invoice_products
        )
        self.total_purchase_price = sum(
            product.purchase_price * product.quantity 
            for product in self.invoice_products
        )
        self.total_sale_price = sum(
            product.sale_price * product.quantity 
            for product in self.invoice_products
        )
        self.total_profit = self.total_sale_price - self.total_purchase_price

        self.total_customer_price = sum(
            product.sale_price * product.quantity * 
            (1 + product.category.tax_rate / 100) for product in self.invoice_products)

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
