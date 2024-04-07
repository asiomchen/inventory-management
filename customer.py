from flask import (
    render_template,
    request,
    url_for,
    redirect,
    Blueprint,
    flash,
)
from flask_login import login_required
from forms import CustomerForm
from data import db, Customer, Invoice


customer = Blueprint("customer", __name__)


@customer.route("/customers/<int:customer_id>")
@login_required
def details(customer_id):
    customer = Customer.query.get(customer_id)
    return render_template("customers/details.html", customer=customer)


@customer.route("/customers")
@login_required
def customers():
    customers = Customer.query.all()
    return render_template("customers/table.html", customers=customers)


@customer.route("/customers/new", methods=["GET", "POST"])
@login_required
def new():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer()
        form.populate_obj(customer)
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully", "success")
        return redirect(url_for("customer.customers"))
    return render_template("customers/new.html", form=form)


@customer.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit(customer_id):
    customer: Customer = Customer.query.get(customer_id)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        db.session.add(customer)
        db.session.commit()
        flash("Customer updated successfully", "success")
        return redirect(url_for("customer.customers"))
    return render_template("customers/edit.html", customer=customer, form=form)


@customer.route("/customers/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete(customer_id):
    customer = Customer.query.get(customer_id)
    invoices = Invoice.query.filter_by(customer_idx=customer.idx).all()
    if invoices:
        flash("Customer has invoices and cannot be deleted", "danger")
        return redirect(url_for("customer.customers"))
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully", "success")
    return redirect(url_for("customer.customers"))
