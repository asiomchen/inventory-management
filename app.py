import os
from pydoc import describe
import re
import stat
import random
from turtle import pu, title
from flask import Flask, render_template, request, url_for, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import logging
from sqlalchemy.sql import func
from utils import generate_random_image


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

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
    
#init database on first run
with app.app_context():
    db.create_all()
    if not Product.query.all():
        for i in range(10):
            weight = round(random.random(), 2)
            purchase_price = random.randint(1, 100)
            sale_price = purchase_price + random.randint(1, 50)
            profit = sale_price - purchase_price
            product = Product(title=f'Product {i}', 
                              description=f'Description {i}', 
                              quantity=i, 
                              photo=generate_random_image(f'uploads/test_product_{i}.png'),
                              weight=weight,
                              purchase_price=purchase_price,
                              sale_price=sale_price,
                              profit=profit)
            db.session.add(product)
        db.session.commit()


@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)
    

@app.route('/<int:product_id>/')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        photo = request.files['photo']
        weight = float(request.form['weight'])
        purchase_price = float(request.form['purchase_price'])
        sale_price = float(request.form['sale_price'])
        profit = sale_price - purchase_price

        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo = filename
        else:
            photo = 'No photo'

        product = Product(title=title, 
                          description=description, 
                          quantity=quantity, 
                          photo=photo, 
                          weight=weight, 
                          purchase_price=purchase_price, 
                          sale_price=sale_price, 
                          profit=profit)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/<int:product_id>/edit/', methods=('GET', 'POST'))
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.title = request.form['title']
        product.description = request.form['description']
        product.quantity = int(request.form['quantity'])
        product.weight = float(request.form['weight'])
        product.purchase_price = float(request.form['purchase_price'])
        product.sale_price = float(request.form['sale_price'])
        product.profit = product.sale_price - product.purchase_price

        # Check if a new photo was uploaded in the form
        if 'photo' in request.files:
            new_photo = request.files['photo']
            if new_photo.filename:
                # Process the new photo and update the product's photo field
                filename = secure_filename(new_photo.filename)
                new_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.photo = filename

        db.session.add(product)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('edit.html', product=product)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.post('/<int:product_id>/delete/')
def delete(product_id):
    product = product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/table/')
def table():
    products = Product.query.all()
    return render_template('table.html', products=products)

@app.route('/add2invoice/<int:product_id>/', methods=('POST',))
def add2invoice(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form['quantity'])
    weight = product.weight * quantity
    purchase_price = product.purchase_price * quantity
    sale_price = product.sale_price * quantity
    profit = sale_price - purchase_price
    product_title = product.title
    latest_invoice = Invoice.query.order_by(Invoice.idx.desc()).first()
    if latest_invoice is None:
        invoice_id = 1
    else:
        latest_invoice_id = latest_invoice.idx
        if latest_invoice.status == 'closed':
            invoice_id = latest_invoice_id + 1
        elif latest_invoice.status == 'open':
            invoice_id = latest_invoice_id
        else:
            raise Exception('Invoice status is not open or closed, it is {}'.format(latest_invoice.status))
    if InvoiceProduct.query.filter_by(invoice_idx=invoice_id, product_idx=product_id).first():
        invoice_product = InvoiceProduct.query.filter_by(invoice_idx=invoice_id, product_idx=product_id).first()
        invoice_product.quantity += quantity
        invoice_product.weight += weight
        invoice_product.purchase_price += purchase_price
        invoice_product.sale_price += sale_price
        invoice_product.profit += profit
    else:
        invoice_product = InvoiceProduct(invoice_idx=invoice_id,
                                            product_idx=product_id,
                                            product_title=product_title,
                                            quantity=quantity,
                                            weight=weight,
                                            purchase_price=purchase_price,
                                            sale_price=sale_price,
                                            profit=profit)
    if Invoice.query.get(invoice_id) is None:
        invoice = Invoice(
            idx=invoice_id,    
            total_weight=weight, 
            total_purchase_price=purchase_price, 
            total_sale_price=sale_price, 
            total_profit=profit, customer_price=sale_price * (1 + 10 / 100))
        db.session.add(invoice)
    else:
        invoice = Invoice.query.get(invoice_id)
        invoice.total_weight += weight
        invoice.total_purchase_price += purchase_price
        invoice.total_sale_price += sale_price
        invoice.total_profit += profit
        invoice.customer_price = invoice.total_sale_price * (1 + invoice.tax_rate / 100)
        db.session.merge(invoice)
    

    db.session.add(invoice_product)
    db.session.commit()
    return redirect(url_for('table'))

@app.route('/invoice/<int:invoice_id>/')
def invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # select products from invoice by invoice_id and sum quantities weight, purchase_price, sale_price, profit
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id).all()

    logging.debug(products)
    return render_template('invoice.html', invoice=invoice, products=products)

@app.route('/latest_invoice/')
def latest_invoice():
    invoice = Invoice.query.order_by(Invoice.idx.desc()).first()
    return redirect(url_for('invoice', invoice_id=invoice.idx))

@app.route('/submit_invoice/<int:invoice_id>/')
def submit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'closed'
    db.session.merge(invoice)
    db.session.commit()
    for product in invoice.invoice_products:
        update_quantity(product.product_idx, product.quantity)
    return redirect(url_for('index'))

@app.route('/invoices/<int:invoice_id>/edit/', methods=('GET', 'POST'))
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)
    if request.method == 'POST':
        for product in products:
            product.quantity = int(request.form[f'quantity_{product.idx}'])
            product.weight = product.product.weight * product.quantity
            product.purchase_price = product.product.purchase_price * product.quantity
            product.sale_price = product.product.sale_price * product.quantity
            product.profit = product.sale_price - product.purchase_price
            db.session.merge(product)
        invoice.total_weight = sum([product.weight for product in products])
        invoice.total_purchase_price = sum([product.purchase_price for product in products])
        invoice.total_sale_price = sum([product.sale_price for product in products])
        invoice.total_profit = sum([product.profit for product in products])
        invoice.customer_price = invoice.total_sale_price * (1 + invoice.tax_rate / 100)
        db.session.merge(invoice)
        db.session.commit()
        return redirect(url_for('invoice', invoice_id=invoice_id))
    if request.method == 'GET':
        return render_template('edit_invoice.html', invoice=invoice, products=products)

@app.route('/invoices/')
def invoices():
    invoices = Invoice.query.all()
    return render_template('invoices.html', invoices=invoices)

def update_quantity(product_id, quantity):
    product = Product.query.get_or_404(product_id)
    product.quantity -= quantity
    db.session.merge(product)
    db.session.commit()
