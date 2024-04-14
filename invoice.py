from flask import (
    render_template,
    url_for,
    redirect,
    Blueprint,
    flash,
    request,
    jsonify
)
from flask_login import login_required
from data import Invoice, InvoiceProduct, Product, Customer, db
from forms import InvoiceProductForm
import re
import logging

invoice_blueprint = Blueprint("invoice", __name__)

@invoice_blueprint.route("/new_invoice/", methods=("POST",))
@login_required
def new_invoice():
    if request.method == "POST":
        name = request.form["invoice_name"].strip()
        if not validate_name(name):
            flash("Please enter a valid name", "danger")
            return redirect(request.referrer)
        elif Invoice.query.filter_by(name=name).first():
            flash("Invoice with this name already exists", "danger")
            return redirect(request.referrer)
        invoice = Invoice(name=name)
        current_active_invoice = Invoice.query.filter_by(is_active=True).first()
        if current_active_invoice:
            current_active_invoice.is_active = False
            db.session.merge(current_active_invoice)
        db.session.add(invoice)
        db.session.commit()
        flash(f"New invoice {invoice.name} created", "success")
        return redirect(request.referrer)


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
        flash(f"Invoice '{invoice.name}' is now active", "success")
        return redirect(request.referrer)


@invoice_blueprint.route("/add2invoice/<int:product_id>/", methods=("POST",))
@login_required
def add2invoice(product_id):
    active_invoice = (
        Invoice.query.filter_by(is_active=True).filter_by(status="open").first()
    )
    if not active_invoice:
        flash("No active open invoices, please create or choose one first", "danger")
        return redirect(url_for("invoice.invoices"))
    product: Product = Product.query.get_or_404(product_id)
    quantity = int(request.form["quantity"])
    invoice_id = active_invoice.idx
    if InvoiceProduct.query.filter_by(
        invoice_idx=invoice_id, product_idx=product_id
    ).first():
        invoice_product: InvoiceProduct = InvoiceProduct.query.filter_by(
            invoice_idx=invoice_id, product_idx=product_id
        ).first()
        invoice_product.quantity += quantity
    else:
        invoice_product = InvoiceProduct.from_product(invoice_idx=invoice_id, product=product)
        invoice_product.quantity = quantity
    
    product.quantity -= quantity
    db.session.add(invoice_product)
    db.session.merge(product)
    db.session.commit()

    invoice: Invoice = Invoice.query.get(invoice_id)
    invoice.calculate_totals()
    db.session.merge(invoice)
    db.session.commit()
    flash(f"{product.title} added to invoice '{invoice.name}'", "success")
    # redirect to the same page where the form was submitted
    return redirect(request.referrer)


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
    new_name = request.form["new_name"].strip()
    if not validate_name(new_name):
        flash("Please enter a valid name", "danger")
        return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))
    elif Invoice.query.filter_by(name=new_name).first():
        flash("Invoice with this name already exists", "danger")
        return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))
    invoice.name = new_name
    db.session.merge(invoice)
    db.session.commit()
    flash(f"Invoice #{invoice_id} {old_name} renamed to {new_name}", "success")
    return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))

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
    flash(f"Invoice #{invoice_id} {invoice.name} was submitted successfully", "success")
    return redirect(url_for("invoice.invoice", invoice_id=invoice_id))


@invoice_blueprint.route("/invoices/<int:invoice_id>/edit/", methods=("GET", "POST"))
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    products = InvoiceProduct.query.filter_by(invoice_idx=invoice_id)
    if request.method == "GET":
        if invoice.status == "closed":
            flash("Invoice is closed and cannot be edited", "danger")
            return redirect(url_for("invoice.invoice", invoice_id=invoice_id))
        return render_template("invoices/edit.html", invoice=invoice, products=products)


@invoice_blueprint.route("/invoices/<int:invoice_id>/<int:product_id>/edit/", methods=("GET", "POST"))
@login_required
def edit_product(invoice_id, product_id):
    invoice: Invoice = Invoice.query.get_or_404(invoice_id)
    product: InvoiceProduct = InvoiceProduct.query.filter_by(invoice_idx=invoice_id, idx=product_id).first()
    source_product: Product = Product.query.get(product.product_idx)
    max_stock = source_product.quantity + product.quantity
    form = InvoiceProductForm(obj=product)
    if form.validate_on_submit():
        form.populate_obj(product)
        if product.quantity > max_stock:
            flash(f"Cannot add items, max stock is {max_stock}", "danger")
            return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))
        product.profit = product.sale_price - product.purchase_price
        source_product.quantity = max_stock - product.quantity
        
        db.session.merge(product)
        db.session.merge(source_product)
        db.session.commit()
        invoice.calculate_totals()
        db.session.merge(invoice)
        db.session.commit()

        flash(f"Product {product.product.title} updated successfully", "success")
        return redirect(url_for("invoice.edit_invoice", invoice_id=invoice_id))
    return render_template("invoices/edit_product.html", form=form, invoice=invoice, product=product)


@invoice_blueprint.route("/invoices")
@login_required
def invoices():
    customer_id = request.args.get("customer_id")
    customer = Customer.query.get(customer_id)
    if customer:
        return render_template("invoices/invoices.html", customer=customer)
    return render_template("invoices/invoices.html")


@invoice_blueprint.route("/api/invoices")
@login_required
def get_invoices():
    query = Invoice.query
    customer_id = request.args.get("customer_id")
    if customer_id:
        customer = Customer.query.get_or_404(customer_id)
        query = query.filter_by(customer_idx=customer.idx)
    search = request.args.get('search[value]')
    if search:
        query = query.filter(db.or_(
            Invoice.name.like(f'%{search}%'),
            Invoice.date.like(f'%{search}%'),
            Invoice.status.like(f'%{search}%'),
        ))
    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')

        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        col = getattr(Invoice, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    start = int(request.args.get('start', type=int))
    length = int(request.args.get('length', type=int))
    query = query.offset(start).limit(length)
    data = []
    for invoice in query:
        data.append({
            "id": invoice.idx,
            "name": invoice.name,
            "date": invoice.date.strftime('%Y-%m-%d'),
            "total_profit": str(invoice.total_profit) + "$",
            "total_weight": str('%.2f' % invoice.total_weight) + "g",
            "status": 'Closed' if invoice.status == 'closed' else 'Open',
            "is_active": invoice.is_active
        })
    return jsonify({"data": data,
                    "recordsTotal": total_filtered,
                    "recordsFiltered": total_filtered,
                    "draw": request.args.get('draw', type=int),
                    })



@invoice_blueprint.route("/invoices/<int:invoice_id>/assign_customer/", methods=["POST"])
@login_required
def assign_customer(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    customer_id = int(request.form["customer_id"])
    customer = Customer.query.get_or_404(customer_id)
    invoice.customer_idx = customer.idx
    db.session.merge(invoice)
    db.session.commit()
    flash(f"Customer {customer.name} assigned to invoice #{invoice.idx}", "success")
    return redirect(url_for("invoice.invoice", invoice_id=invoice_id))


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



def validate_name(name):
    if not name or not re.match(r"^[a-zA-Z0-9_\s]+$", name) or name == "":
        return False
    else:
        if name == "" or re.match(r"\s+", name):
            return False
    return True