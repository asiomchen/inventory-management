from flask import (
    render_template,
    url_for,
    redirect,
    Blueprint,
    flash,
    request,
)
from flask_login import login_required
from data import Invoice, InvoiceProduct, Product, Customer, db
import re
import logging

invoice_blueprint = Blueprint("invoice", __name__)

@invoice_blueprint.route("/new_invoice/", methods=("POST",))
@login_required
def new_invoice():
    if request.method == "POST":
        name = request.form["invoice_name"]
        if not name or not re.match(r"^[a-zA-Z0-9_\s]+$", name) or name == "":
            flash("Please enter a valid invoice name", "danger")
            return redirect(url_for("invoice.invoices"))
        else:
            name = name.strip()
            if name == "" or re.match(r"\s+", name):
                flash("Please enter a valid invoice name", "danger")
                return redirect(url_for("invoice.invoices"))
            elif Invoice.query.filter_by(name=name).first():
                flash("Invoice with this name already exists", "danger")
                return redirect(url_for("invoice.invoices"))
        invoice = Invoice(name=name)
        current_active_invoice = Invoice.query.filter_by(is_active=True).first()
        if current_active_invoice:
            current_active_invoice.is_active = False
            db.session.merge(current_active_invoice)
        db.session.add(invoice)
        db.session.commit()
        flash(f"New invoice {invoice.name} created", "success")
        return redirect(url_for("invoice.invoices"))
    return render_template("new_invoice.html")


@invoice_blueprint.route("/change_active_status/", methods=("POST",))
@login_required
def change_active_status():
    invoice_id = int(request.form["invoice_id"])
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.is_active:
        flash(f"Invoice #{invoice_id} is already active", "danger")
        return redirect(url_for("invoice.invoices"))
    else:
        current_active_invoice = Invoice.query.filter_by(is_active=True).first()
        if current_active_invoice:
            current_active_invoice.is_active = False
            db.session.merge(current_active_invoice)
        invoice.is_active = True
        db.session.merge(invoice)
        db.session.commit()
        flash(f"Invoice #{invoice_id} is now active", "success")
        return redirect(url_for("invoice.invoices"))


@invoice_blueprint.route("/add2invoice/<int:product_id>/", methods=("POST",))
@login_required
def add2invoice(product_id):
    active_invoice = (
        Invoice.query.filter_by(is_active=True).filter_by(status="open").first()
    )
    if not active_invoice:
        flash("No active open invoices, please create or choose one first", "danger")
        return redirect(url_for("invoice.invoices"))
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form["quantity"])
    weight = product.weight * quantity
    purchase_price = product.purchase_price * quantity
    sale_price = product.sale_price * quantity
    profit = sale_price - purchase_price
    tax_rate = product.category.tax_rate / 100
    customer_price = sale_price * (1 + tax_rate)
    invoice_id = active_invoice.idx
    if InvoiceProduct.query.filter_by(
        invoice_idx=invoice_id, product_idx=product_id
    ).first():
        invoice_product = InvoiceProduct.query.filter_by(
            invoice_idx=invoice_id, product_idx=product_id
        ).first()
        invoice_product.quantity += quantity
        invoice_product.weight += weight
        invoice_product.purchase_price += purchase_price
        invoice_product.sale_price += sale_price
        invoice_product.profit += profit
    else:
        invoice_product = InvoiceProduct(
            invoice_idx=invoice_id,
            product_idx=product_id,
            quantity=quantity,
            weight=weight,
            purchase_price=purchase_price,
            sale_price=sale_price,
            profit=profit,
        )
    if Invoice.query.get(invoice_id) is None:
        invoice = Invoice(
            idx=invoice_id,
            total_weight=weight,
            total_purchase_price=purchase_price,
            total_sale_price=sale_price,
            total_profit=profit,
            customer_price=customer_price,
        )
        db.session.add(invoice)
    else:
        invoice = Invoice.query.get(invoice_id)
        invoice.total_weight += weight
        invoice.total_purchase_price += purchase_price
        invoice.total_sale_price += sale_price
        invoice.total_profit += profit
        invoice.customer_price += customer_price
        db.session.merge(invoice)
    product.quantity -= quantity
    db.session.merge(product)

    db.session.add(invoice_product)
    db.session.commit()
    flash(f"{product.title} added to invoice #{invoice_id}", "success")
    return redirect(url_for("main.table"))


@invoice_blueprint.route("/invoice/<int:invoice_id>/")
@login_required
def invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # select products from invoice by invoice_id and sum quantities weight, purchase_price, sale_price, profit
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id).all()
    customers = Customer.query.all()

    logging.debug(products)
    return render_template(
        "invoices/invoice.html", invoice=invoice, products=products, customers=customers
    )


@invoice_blueprint.route("/latest_invoice/")
@login_required
def latest_invoice():
    invoice = Invoice.query.order_by(Invoice.idx.desc()).first()
    if invoice is None:
        flash("No invoices yet, please create one", "info")
        return redirect(url_for("invoice.index"))
    return redirect(url_for("invoice.invoice", invoice_id=invoice.idx))


@invoice_blueprint.route("/active_invoice/")
@login_required
def active_invoice():
    invoice = Invoice.query.filter_by(is_active=True).first()
    if invoice is None:
        flash("No active invoices, please create one", "info")
        return redirect(url_for("invoice.index"))
    return redirect(url_for("invoice.invoice", invoice_id=invoice.idx))


@invoice_blueprint.route("/rename_invoice/<int:invoice_id>/", methods=("POST",))
@login_required
def rename(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    old_name = invoice.name
    new_name = request.form["new_name"]
    if not new_name or not re.match(r"^[a-zA-Z0-9_\s]+$", new_name) or new_name == "":
        flash("Please enter a valid invoice name", "danger")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    else:
        new_name = new_name.strip()
        if new_name == "" or re.match(r"\s+", new_name):
            flash("Please enter a valid invoice name", "danger")
            return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
        elif Invoice.query.filter_by(name=new_name).first():
            flash("Invoice with this name already exists", "danger")
            return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    invoice.name = new_name
    db.session.merge(invoice)
    db.session.commit()
    flash(f"Invoice #{invoice_id} {old_name} renamed to {new_name}", "success")
    return redirect(url_for("invoice.invoice", invoice_id=invoice_id))

@invoice_blueprint.route("/submit_invoice/<int:invoice_id>/")
@login_required
def submit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if not invoice.invoice_products:
        flash("No products in this invoice, please add some", "danger")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    if not invoice.customer_idx:
        flash("No customer assigned to this invoice, please assign one", "danger")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    invoice.status = "closed"
    db.session.merge(invoice)
    db.session.commit()
    for product in invoice.invoice_products:
        update_quantity(product.product_idx, product.quantity)
    flash(f"Invoice #{invoice_id} was submitted successfully", "success")
    return redirect(url_for("main.index"))


@invoice_blueprint.route("/invoices/<int:invoice_id>/edit/", methods=("GET", "POST"))
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)
    if request.method == "POST":
        changed_product_id = int(request.form["product_id"])
        changed_product = InvoiceProduct.query.filter_by(
            product_idx=changed_product_id
        ).first()
        original_product = Product.query.get_or_404(changed_product.product_idx)
        requested_quantity = int(request.form["quantity"])
        if requested_quantity > original_product.quantity + changed_product.quantity:
            flash(
                f"Not enough {original_product.title} in stock, please enter a smaller quantity",
                "danger",
            )
            return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))
        else:
            original_product.quantity += changed_product.quantity - requested_quantity
            changed_product.quantity = requested_quantity
            changed_product.weight = (
                changed_product.product.weight * changed_product.quantity
            )
            changed_product.purchase_price = (
                changed_product.product.purchase_price * changed_product.quantity
            )
            changed_product.sale_price = (
                changed_product.product.sale_price * changed_product.quantity
            )
            changed_product.profit = (
                changed_product.sale_price - changed_product.purchase_price
            )
            db.session.merge(changed_product)
            if changed_product.quantity == 0:
                db.session.delete(changed_product)
                logging.debug(f"Product {changed_product.product.title} deleted")
            products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)

        invoice.total_weight = sum([product.weight for product in products])
        invoice.total_purchase_price = sum(
            [product.purchase_price for product in products]
        )
        invoice.total_sale_price = sum([product.sale_price for product in products])
        invoice.total_profit = sum([product.profit for product in products])
        invoice.customer_price = sum([product.sale_price * 
                                      (1 + product.product.category.tax_rate / 100)
                                       for product in products])
        db.session.merge(invoice)
        db.session.commit()
        flash("Invoice updated", "success")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    if request.method == "GET":
        return render_template("invoices/edit.html", invoice=invoice, products=products)


@invoice_blueprint.route("/invoices/")
@login_required
def invoices():
    invoices = Invoice.query.all()
    return render_template("invoices/invoices.html", invoices=invoices)


@invoice_blueprint.route("/invoices/customer=<int:customer_id>/")
@login_required
def invoices_by_customer(customer_id):
    invoices = Invoice.query.filter_by(customer_idx=customer_id).all()
    customer = Customer.query.get_or_404(customer_id)
    return render_template("invoices/invoices.html", invoices=invoices, customer=customer)


@invoice_blueprint.route("/invoices/<int:invoice_id>/assign_customer/", methods=["POST"])
def assign_customer(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    customer_id = int(request.form["customer_id"])
    customer = Customer.query.get_or_404(customer_id)
    invoice.customer_idx = customer.idx
    db.session.merge(invoice)
    db.session.commit()
    flash(f"Customer {customer.name} assigned to invoice #{invoice.idx}", "success")
    return redirect(url_for("invoice.invoice", invoice_id=invoice_id))


def update_quantity(product_id, quantity):
    product = Product.query.get_or_404(product_id)
    product.quantity -= quantity
    db.session.merge(product)
    db.session.commit()


@invoice_blueprint.route("/invoices/print/<int:invoice_id>")
@login_required
def print(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    products = products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id).all()
    if invoice.status == "open":
        flash("Invoice is not closed yet", "danger")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    if not invoice.customer:
        flash("Invoice has no customer, please add a customer first", "danger")
        return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
    return render_template("invoices/pdf_template.html", invoice=invoice, products=products)
