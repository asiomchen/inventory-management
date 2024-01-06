from flask import render_template, request, url_for, redirect, send_from_directory, Blueprint, current_app, flash
from flask_login import login_required
from customer import customers
from data import db , Invoice, InvoiceProduct


invoice = Blueprint('invoice', __name__)


@invoice.route('/invoices/print/<int:invoice_id>')
@login_required
def print(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    products = products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id).all()
    if invoice.status == 'open':
        flash('Invoice is not closed yet', 'danger')
        return redirect(url_for('main.index'))
    if not invoice.customer:
        flash('Invoice has no customer, please add a customer first', 'danger')
        return redirect(url_for('main.index'))
    return render_template('pdf_template.html', invoice=invoice, products=products)