
from flask import (
    render_template,
    request,
    url_for,
    redirect,
    Blueprint,
    flash,
)
from flask_login import login_required
from forms import ImportForm
from data import db, ImportedProduct, Product, Image


import_data = Blueprint("import_data", __name__)


@import_data.route("/import/products")
@login_required
def products():
    form = ImportForm()
    if form.validate_on_submit():
        pass
    return render_template("import.html", form=form)




