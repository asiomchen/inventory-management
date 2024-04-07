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
    jsonify,
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
    query = Product.query
    category_name = None
    sortables = ["title", "quantity", "weight", "purchase_price", "sale_price", "profit"]
    if "category" in request.args:
        category_name = request.args["category"]
        category = Category.query.filter_by(name=category_name).first()
        if category:
            query = query.filter_by(category_idx=category.idx)
    per_page = request.args.get("per_page", 5, type=int)
    # Sorting
    if "sort_by" in request.args:
        sort_by = request.args["sort_by"]
        if sort_by in sortables:
            if "sort_order" in request.args:
                sort_order = request.args["sort_order"]
                if sort_order == "asc":
                    query = query.order_by(getattr(Product, sort_by))
                elif sort_order == "desc":
                    query = query.order_by(getattr(Product, sort_by).desc())
            else:
                query = query.order_by(getattr(Product, sort_by))


    page = query.paginate(per_page=per_page)
    if len(page.items) == 0 and category_name:
        flash(f"No products found in the category: {category_name}", "warning")
        return redirect(url_for("main.index"))
    logging.info(f"{type(page)}")
    return render_template(
        "index.html", page=page, products=page.items, category_name=category_name)



@main.route("/<int:product_id>/")
@login_required
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("products/product.html", product=product)


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

        volume = request.form.get("volume")
        if volume:
            if volume == "":
                volume = None
            elif re.match(r"^\d+(\.\d+)?$", volume):
                volume = float(volume)
            else:
                flash("Volume must be a number", "danger")
                return render_template("products/create.html")

        product = Product(
            title=title,
            description=description,
            quantity=quantity,
            photo_idx=photo.idx if photo != "No photo" else None,
            weight=weight,
            purchase_price=purchase_price,
            sale_price=sale_price,
            profit=profit,
            category_idx=category_idx, volume=volume
        )
        db.session.add(product)
        db.session.commit()

        return redirect(url_for("main.index"))
    return render_template("products/create.html")


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
                logging.info(f"New photo uploaded: {filename}")
                new_photo.save(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                )
                url, public_id = upload_image(
                    os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                )
                image = Image(url=url, public_id=public_id)
                db.session.add(image)
                db.session.commit()
                image = Image.query.filter_by(public_id=public_id).first()
                product.photo_idx = image.idx
                os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

        volume = request.form.get("volume")
        if volume:
            if volume == "":
                volume = None
            elif re.match(r"^\d+(\.\d+)?$", volume):
                volume = float(volume)
            else:
                flash("Volume must be a number", "danger")
                return render_template("products/create.html")
        product.volume = volume

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("main.index"))
    return render_template("products/edit.html", product=product)


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


@main.route("/table")
@login_required
def table():
    return render_template("products/table.html")

@main.route("/api/products/")
@login_required
def get_products():

    query = Product.query
    search = request.args.get('search[value]')
    if search:
        logging.info(f"Search by {search}")
        # if string like float_column>float or float_column<float we need to split it
        if re.match(r"([a-z_].+)([<>])(\d+\.?\d?)", search):
            logging.info(f"Search by {search}")
            column, operator, value = re.match(r"([a-z_].+)([<>])(\d+\.?\d?)", search).groups()
            if operator == '>':
                query = query.filter(getattr(Product, column) > float(value))
            elif operator == '<':
                query = query.filter(getattr(Product, column) < float(value))
        else:
            query = query.filter(db.or_(
                Product.title.like(f'%{search}%'),
                Product.description.like(f'%{search}%'),
                Product.category.has(Category.name.like(f'%{search}%')),
                Product.quantity.like(f'%{search}%'),
            ))
    total_filtered = query.count()

    # Sorting
    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        logging.info(f"Sorting by {col_name}")
        if col_name in ['photo', 'add2cart']:
            col_name = 'title'
        if col_name == 'category':
            col_name = 'category_idx'
        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        col = getattr(Product, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)
    # Pagination
    start = int(request.args.get("start", 0))
    length = int(request.args.get("length", 10))
    query = query.offset(start).limit(length)
    data = []
    for product in query:
        data.append(
            {   
                "id": product.idx,
                "title": product.title,
                "description": product.description,
                "quantity": product.quantity,
                "weight": product.weight,
                "purchase_price": product.purchase_price,
                "sale_price": product.sale_price,
                "profit": product.profit,
                "category": product.category.name,
                "photo": product.photo.url if product.photo else current_app.url_for("static", filename="no-photo.bmp"),
                "volume": product.volume,
            }
        )
    return jsonify(
        {
            "data": data,
            "recordsTotal": total_filtered,
            "recordsFiltered": total_filtered,
            "draw": request.args.get("draw"),
        }
    )


