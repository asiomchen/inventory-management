from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class Product(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(255))
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)

    def __repr__(self):
        return '<Product %r>' % self.title
    
    
class InvoiceProduct(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    invoice_idx = db.Column(db.Integer, db.ForeignKey('invoice.idx'))
    product_idx = db.Column(db.Integer, db.ForeignKey('product.idx'))
    product = db.relationship('Product', backref='invoice', lazy=True)
    product_title = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    profit = db.Column(db.Float)

    def __repr__(self):
        return '<InvoiceProduct %r>' % self.idx
    
class Invoice(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    invoice_products = db.relationship('InvoiceProduct', backref='invoice', lazy=True)
    total_weight = db.Column(db.Float)
    total_purchase_price = db.Column(db.Float)
    total_sale_price = db.Column(db.Float)
    total_profit = db.Column(db.Float)
    tax_rate = db.Column(db.Float, default=10)
    customer_price = db.Column(db.Float)
    status = db.Column(db.String(255), default='open')

    def __repr__(self):
        return '<Invoice %r>' % self.idx
    
class User(db.Model):
    idx = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username