from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from flask_login import login_required
from data import db , Customer


customer = Blueprint('customer', __name__)

@customer.route('/customers/<int:customer_id>')
@login_required
def details(customer_id):
    customer = Customer.query.get(customer_id)
    return render_template('customers/details.html', customer=customer)

@customer.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers/table.html', customers=customers)

@customer.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new():
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

@customer.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(customer_id):
    customer = Customer.query.get(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        customer.notes = request.form['notes']
        db.session.commit()
        flash('Customer updated successfully')
        return redirect(url_for('customer.customers'))
    return render_template('customers/edit.html', customer=customer)

@customer.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete(customer_id):
    customer = Customer.query.get(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully')
    return redirect(url_for('customer.customers'))
