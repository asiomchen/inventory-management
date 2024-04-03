import os
import re
from flask import (
    render_template,
    request,
    url_for,
    redirect,
    send_from_directory,
    Blueprint,
    current_app,
    flash,
)
from werkzeug.utils import secure_filename
from flask_login import login_required
import logging
from data import Product, InvoiceProduct, Invoice, Image, Category, Customer, db
from images import upload_image

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template(
        "index.html", products=products, category_name=None, categories=categories
    )


@main.route("/category/<int:category_id>/")
@login_required
def category(category_id):
    products = Product.query.filter_by(category_idx=category_id).all()
    current_category = Category.query.get_or_404(category_id)
    if not products:
        flash("No products in this category yet", "info")
        return redirect(url_for("main.index"))
    return render_template(
        "index.html", products=products, category_name=current_category.name
    )


@main.route("/<int:product_id>/")
@login_required
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product.html", product=product)


@main.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@main.route("/create/", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        quantity = int(request.form["quantity"])
        photo = request.files["photo"]
        weight = float(request.form["weight"])
        purchase_price = float(request.form["purchase_price"])
        sale_price = float(request.form["sale_price"])
        profit = sale_price - purchase_price
        category_name = request.form["category"]
        category = Category.query.filter_by(name=category_name).first()
        category_idx = category.idx

        if photo:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            url, public_id = upload_image(
                os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            )
            image = Image(url=url, public_id=public_id)
            db.session.add(image)
            db.session.commit()
            image = Image.query.filter_by(public_id=public_id).first()
            photo = image
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        else:
            photo = "No photo"

        product = Product(
            title=title,
            description=description,
            quantity=quantity,
            photo_idx=photo.idx if photo != "No photo" else None,
            weight=weight,
            purchase_price=purchase_price,
            sale_price=sale_price,
            profit=profit,
            category_idx=category_idx,
        )
        db.session.add(product)
        db.session.commit()

        return redirect(url_for("main.index"))
    return render_template("create.html")


@main.route("/<int:product_id>/edit/", methods=("GET", "POST"))
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.title = request.form["title"]
        category_name = request.form["category"]
        category = Category.query.filter_by(name=category_name).first()
        product.category_idx = category.idx

        product.description = request.form["description"]
        product.quantity = int(request.form["quantity"])
        product.weight = float(request.form["weight"])
        product.purchase_price = float(request.form["purchase_price"])
        product.sale_price = float(request.form["sale_price"])
        product.profit = product.sale_price - product.purchase_price

        # Check if a new photo was uploaded in the form
        if "photo" in request.files:
            new_photo = request.files["photo"]
            if new_photo.filename:
                # Process the new photo and update the product's photo field
                filename = secure_filename(new_photo.filename)
                new_photo.save(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                )
                product.photo = filename

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("main.index"))
    return render_template("edit.html", product=product)


@main.route("/about/")
@login_required
def about():
    return render_template("about.html")


@main.post("/<int:product_id>/delete/")
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("main.index"))


@main.route("/table/")
@login_required
def table():
    products = Product.query.all()
    return render_template("table.html", products=products)
