from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from flask_login import login_required
from data import db , Customer


customer = Blueprint('customer', __name__)

@customer.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers/table.html', customers=customers)

@customer.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        notes = request.form['notes']
        customer = Customer(name=name, phone=phone, address=address, notes=notes)
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully')
        return redirect(url_for('customer.customers'))
    return render_template('customers/new.html')
