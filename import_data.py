from flask import (
    render_template,
    Blueprint,
    flash,
)
from flask_login import login_required
from forms import ImportForm
from data import db, ImportedProduct, Product
import pandas as pd

import_data = Blueprint("import_data", __name__)


@import_data.route("/import/products", methods=["GET", "POST"])
@login_required
def products():
    form = ImportForm()
    if form.validate_on_submit():
        allow_duplicates = form.allow_duplicates.data
        data = form.file.data
        filename = data.filename
        data.save(filename)
        df = pd.read_csv(filename)
        usefull = df[["Name", "Category", "Description"]]
        usefull.columns = ["name", "description", "photo"]
        usefull.description.fillna("", inplace=True)
        usefull.photo.fillna("", inplace=True)
        usefull.photo = usefull.photo.apply(lambda x: x.split(";")[0])
        base_url = "https://static.wixstatic.com/media/"
        usefull["photo_url"] = usefull["photo"].apply(
            lambda x: base_url + x.split(";")[0] if x else ""
        )
        usefull.drop("photo", axis=1, inplace=True)
        successful = 0
        for _, row in usefull.iterrows():
            product = ImportedProduct(
                title=row["name"],
                category_idx=1,
                description=row["description"],
                photo=row["photo_url"],
            )
            product = Product.from_wix(product)
            if (
                Product.query.filter_by(title=product.title).first()
                and not allow_duplicates
            ):
                flash(f"Product '{product.title}' already exists", "danger")
                continue
            db.session.add(product)
            db.session.commit()
            successful += 1
        if successful:
            flash(f"Successfully imported {successful} products", "success")
    return render_template("import.html", form=form)
