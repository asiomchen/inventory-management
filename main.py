import os
import re
from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from werkzeug.utils import secure_filename
from flask_login import login_required
import logging
from data import Product, InvoiceProduct, Invoice, User, Image, Category, db
from images import upload_image, delete_image, deliver_image

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('index.html', products=products, category_name=None, categories=categories)

@main.route('/category/<int:category_id>/')
@login_required
def category(category_id):
    products = Product.query.filter_by(category_idx=category_id).all()
    current_category = Category.query.get_or_404(category_id)
    if not products:
        flash('No products in this category yet', 'info')
        return redirect(url_for('main.index'))
    return render_template('index.html', products=products,
                            category_name=current_category.name)

@main.route('/<int:product_id>/')
@login_required
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               filename)

@main.route('/create/', methods=('GET', 'POST'))
@login_required
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
            photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            url, public_id = upload_image(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image = Image(url=url, public_id=public_id)
            db.session.add(image)
            db.session.commit()
            image = Image.query.filter_by(public_id=public_id).first()
            photo = image
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        else:
            photo = 'No photo'

        product = Product(title=title, 
                          description=description, 
                          quantity=quantity, 
                          photo_idx=photo.idx if photo != 'No photo' else None,
                          weight=weight, 
                          purchase_price=purchase_price, 
                          sale_price=sale_price, 
                          profit=profit)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('main.index'))
    return render_template('create.html')

@main.route('/<int:product_id>/edit/', methods=('GET', 'POST'))
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.title = request.form['title']
        category_name = request.form['category']
        category = Category.query.filter_by(name=category_name).first()
        product.category_idx = category.idx

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
                new_photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                product.photo = filename

        db.session.add(product)
        db.session.commit()

        return redirect(url_for('main.index'))
    return render_template('edit.html', product=product)

@main.route('/about/')
@login_required
def about():
    return render_template('about.html')

@main.post('/<int:product_id>/delete/')
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('main.index'))

@main.route('/table/')
@login_required
def table():
    products = Product.query.all()
    return render_template('table.html', products=products)

@main.route(f'/new_invoice/', methods=('POST',))
@login_required
def new_invoice():
    if request.method == 'POST':
        name = request.form['invoice_name']
        invoice = Invoice(name=name)
        current_active_invoice = Invoice.query.filter_by(is_active=True).first()
        if current_active_invoice:
            current_active_invoice.is_active = False
            db.session.merge(current_active_invoice)
        db.session.add(invoice)
        db.session.commit()
        flash(f'New invoice {invoice.name} created', 'success')
        return redirect(url_for('main.invoices'))
    return render_template('new_invoice.html')

@main.route('/change_active_status/', methods=('POST',))
@login_required
def change_active_status():
    invoice_id = int(request.form['invoice_id'])
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.is_active:
        flash(f'Invoice #{invoice_id} is already active', 'danger')
        return redirect(url_for('main.invoices'))
    else:
        current_active_invoice = Invoice.query.filter_by(is_active=True).first()
        if current_active_invoice:
            current_active_invoice.is_active = False
            db.session.merge(current_active_invoice)
        invoice.is_active = True
        db.session.merge(invoice)
        db.session.commit()
        flash(f'Invoice #{invoice_id} is now active', 'success')
        return redirect(url_for('main.invoices'))


@main.route('/add2invoice/<int:product_id>/', methods=('POST',))
@login_required
def add2invoice(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form['quantity'])
    weight = product.weight * quantity
    purchase_price = product.purchase_price * quantity
    sale_price = product.sale_price * quantity
    profit = sale_price - purchase_price
    product_title = product.title
    active_invoice = Invoice.query.filter_by(is_active=True).filter_by(status='open').first()
    if not active_invoice:
        flash('No active open invoices, please create one first', 'danger')
        return redirect(url_for('main.invoices'))
    invoice_id = active_invoice.idx
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
    product.quantity -= quantity
    db.session.merge(product)

    db.session.add(invoice_product)
    db.session.commit()
    flash(f"{product.title} added to invoice #{invoice_id}", 'success')
    return redirect(url_for('main.table'))

@main.route('/invoice/<int:invoice_id>/')
@login_required
def invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # select products from invoice by invoice_id and sum quantities weight, purchase_price, sale_price, profit
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id).all()

    logging.debug(products)
    return render_template('invoice.html', invoice=invoice, products=products)

@main.route('/latest_invoice/')
@login_required
def latest_invoice():
    invoice = Invoice.query.order_by(Invoice.idx.desc()).first()
    if invoice is None:
        flash('No invoices yet, please create one', 'info')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.invoice', invoice_id=invoice.idx))

@main.route('/active_invoice/')
@login_required
def active_invoice():
    invoice = Invoice.query.filter_by(is_active=True).first()
    if invoice is None:
        flash('No active invoices, please create one', 'info')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.invoice', invoice_id=invoice.idx))

@main.route('/submit_invoice/<int:invoice_id>/')
@login_required
def submit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'closed'
    db.session.merge(invoice)
    db.session.commit()
    for product in invoice.invoice_products:
        update_quantity(product.product_idx, product.quantity)
    flash(f'Invoice #{invoice_id} was submitted successfully', 'success')
    return redirect(url_for('main.index'))

@main.route('/invoices/<int:invoice_id>/edit/', methods=('GET', 'POST'))
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)
    if request.method == 'POST':
        changed_product_id = int(request.form['product_id'])
        changed_product = InvoiceProduct.query.filter_by(product_idx=changed_product_id).first()
        original_product = Product.query.get_or_404(changed_product.product_idx)
        requested_quantity = int(request.form[f'quantity'])
        if requested_quantity > original_product.quantity + changed_product.quantity:
            flash(f'Not enough {original_product.title} in stock, please enter a smaller quantity', 'danger')
            return redirect(url_for('main.edit_invoice', invoice_id=invoice_id))
        else:
            original_product.quantity += changed_product.quantity - requested_quantity
            changed_product.quantity = requested_quantity
            changed_product.weight = changed_product.product.weight * changed_product.quantity
            changed_product.purchase_price = changed_product.product.purchase_price * changed_product.quantity
            changed_product.sale_price = changed_product.product.sale_price * changed_product.quantity
            changed_product.profit = changed_product.sale_price - changed_product.purchase_price
            db.session.merge(changed_product)
            if changed_product.quantity == 0:
                db.session.delete(changed_product)
            products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)
            
                
        invoice.total_weight = sum([product.weight for product in products])
        invoice.total_purchase_price = sum([product.purchase_price for product in products])
        invoice.total_sale_price = sum([product.sale_price for product in products])
        invoice.total_profit = sum([product.profit for product in products])
        invoice.customer_price = invoice.total_sale_price * (1 + invoice.tax_rate / 100)
        db.session.merge(invoice)
        db.session.commit()
        flash('Invoice updated', 'success')
        return redirect(url_for('main.invoice', invoice_id=invoice_id))
    if request.method == 'GET':
        return render_template('edit_invoice.html', invoice=invoice, products=products)

@main.route('/invoices/')
@login_required
def invoices():
    invoices = Invoice.query.all()
    return render_template('invoices.html', invoices=invoices)

def update_quantity(product_id, quantity):
    product = Product.query.get_or_404(product_id)
    product.quantity -= quantity
    db.session.merge(product)
    db.session.commit()
