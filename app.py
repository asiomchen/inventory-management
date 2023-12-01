import os
import random
from flask import Flask, render_template, request, url_for, redirect, send_from_directory , flash
from werkzeug.utils import secure_filename
import logging
from utils import generate_random_image
from data import db, Product, InvoiceProduct, Invoice, User

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = "dev"
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config["MAIN_PASSWORD"] = generate_password_hash(os.environ['MAIN_PASSWORD'])
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# init database
db.init_app(app)
    
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

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if not app.config['LOG_ENABLED']:
#         flash('Too many unsuccessful login attempts. Please try again in {} hours.'.format((app.config['ALLOW_LOGGING_TIME'] - datetime.datetime.now()).seconds // 3600))
#     elif request.method == 'POST':
#         if check_password_hash(app.config["MAIN_PASSWORD"], request.form['password']):
#             # add logging cookie

#             flash('You were successfully logged in', 'success')
#         else:
#             app.config['UNSUCCESSFUL_LOGIN_ATTEMPTS'] += 1
#             flash('Incorrect password. You have {} attempts left.'.format(app.config['MAX_UNSUCCESSFUL_LOGIN_ATTEMPTS'] - app.config['UNSUCCESSFUL_LOGIN_ATTEMPTS']))
#             if app.config['UNSUCCESSFUL_LOGIN_ATTEMPTS'] >= app.config['MAX_UNSUCCESSFUL_LOGIN_ATTEMPTS']:
#                 app.config['UNSUCCESSFUL_LOGIN_ATTEMPTS'] = 0
#                 app.config['LOG_ENABLED'] = False
#                 app.config['ALLOW_LOGGING_TIME'] = datetime.datetime.now() + datetime.timedelta(days=1)
#                 flash('Too many unsuccessful login attempts. Please try again tomorrow.')
#     return render_template('login.html')


# @app.route('/change-password', methods=['GET', 'POST'])
# def change_password():
#     if request.method == 'POST':
#         pass
#     else:
#         return render_template('change-password.html')

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

@app.route('/change_tax_rate/', methods=['POST'])
def change_invoice_tax_rate():
    invoice_id = int(request.form['invoice_id'])
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.tax_rate = float(request.form['tax_rate'])
    invoice.customer_price = invoice.total_sale_price * (1 + invoice.tax_rate / 100)
    db.session.merge(invoice)
    db.session.commit()
    return redirect(url_for('invoice', invoice_id=invoice_id))
