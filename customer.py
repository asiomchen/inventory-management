from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from flask_login import login_required
from data import db , Customer


customer = Blueprint('customer', __name__)

@customer.route('/customers')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)
